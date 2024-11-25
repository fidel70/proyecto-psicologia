import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class DatosPensamiento:
    pensamiento: str
    cantidad: float
    duracion: float
    intensidad: float
    fecha: str

    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title('Estadísticas de Pensamientos')
        self.ventana.geometry('1280x800')
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value='veces')
        self.pensamiento_seleccionado = None
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))
        self.crear_widgets()
        self.cargar_pacientes()

    def crear_widgets(self):
        self.main_frame = ttk.Frame(self.ventana, padding='10')
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        panel_control = ttk.Frame(self.main_frame)
        panel_control.grid(row=0, column=0, columnspan=2, sticky='ew', pady
            =(0, 10))
        ttk.Label(panel_control, text='Paciente:').pack(side=tk.LEFT, padx=5)
        self.combo_pacientes = ttk.Combobox(panel_control, textvariable=
            self.paciente_seleccionado, state='readonly', width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.
            actualizar_graficos)
        ttk.Label(panel_control, text='Desde:').pack(side=tk.LEFT, padx=5)
        self.fecha_inicio = DateEntry(panel_control, width=12, background=
            'darkblue', foreground='white', date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        ttk.Label(panel_control, text='Hasta:').pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(panel_control, width=12, background=
            'darkblue', foreground='white', date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_control, text='Actualizar', command=self.
            actualizar_graficos).pack(side=tk.LEFT, padx=20)
        frame_dimension = ttk.LabelFrame(panel_control, text='Dimensión',
            padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        for dimension in ['veces', 'minutos', 'intensidad']:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                variable=self.dimension_actual, value=dimension, command=
                self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        self.frame_graficos = ttk.Frame(self.main_frame)
        self.frame_graficos.grid(row=1, column=0, columnspan=2, sticky='nsew')
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

    def cargar_pacientes(self):
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT codigo, nombre FROM pacientes ORDER BY codigo')
            pacientes = cursor.fetchall()
            self.combo_pacientes['values'] = [f'{p[0]} - {p[1]}' for p in
                pacientes]
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror('Error',
                f'Error al cargar pacientes: {str(e)}')

    def obtener_datos_dimensiones(self):
        if not self.paciente_seleccionado.get():
            return {}
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.codigo, p.pensamiento, 
                       SUM(d.cantidad) as total_cantidad,
                       SUM(d.duracion) as total_duracion,
                       AVG(d.intensidad) as promedio_intensidad,
                       MAX(d.cantidad) as max_cantidad,
                       MAX(d.duracion) as max_duracion
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo LIKE ? 
                AND d.fecha BETWEEN ? AND ?
                GROUP BY p.codigo, p.pensamiento
            """
                , (f'{codigo_paciente}%', fecha_inicio, fecha_fin))
            resultados = {}
            for row in cursor.fetchall():
                resultados[row[0]] = {'pensamiento': row[1], 'cantidad': 
                    row[2] or 0, 'duracion': row[3] or 0, 'intensidad': row
                    [4] or 0, 'max_cantidad': row[5] or 0, 'max_duracion': 
                    row[6] or 0}
            conn.close()
            return resultados
        except sqlite3.Error as e:
            messagebox.showerror('Error', f'Error al obtener datos: {str(e)}')
            return {}

    def obtener_datos_diarios(self, codigo_pensamiento):
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.fecha, d.cantidad, d.duracion, d.intensidad
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo = ? 
                AND d.fecha BETWEEN ? AND ?
                ORDER BY d.fecha
            """
                , (codigo_pensamiento, fecha_inicio, fecha_fin))
            datos_diarios = cursor.fetchall()
            conn.close()
            return datos_diarios
        except sqlite3.Error as e:
            messagebox.showerror('Error',
                f'Error al obtener datos diarios: {str(e)}')
            return []

    def actualizar_graficos(self, event=None):
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
        if not self.paciente_seleccionado.get():
            return
        self.crear_grafico_circular()
        if self.pensamiento_seleccionado:
            self.crear_grafico_frecuencia()

    def crear_grafico_circular(self):
        datos = self.obtener_datos_dimensiones()
        if not datos:
            return
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        dimension = self.dimension_actual.get()
        valores = []
        etiquetas = []
        colores = []
        for codigo, info in datos.items():
            if dimension == 'veces':
                valor = info['cantidad']
                colores.append(self.colores_base[len(colores) % len(self.
                    colores_base)])
            elif dimension == 'minutos':
                valor = info['duracion']
                colores.append(self.colores_base[len(colores) % len(self.
                    colores_base)])
            else:
                valor = info['intensidad']
                if valor <= 3:
                    colores.append('lightgreen')
                elif valor <= 7:
                    colores.append('yellow')
                else:
                    colores.append('red')
            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
        if not valores:
            return
        wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, colors
            =colores, autopct='%1.1f%%', startangle=90)
        plt.setp(autotexts, size=8)
        plt.setp(texts, size=8)
        ax.legend(wedges, etiquetas, title='Pensamientos', loc=
            'center left', bbox_to_anchor=(1, 0, 0.5, 1))
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew', padx=5,
            pady=5)

        def on_click(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_point([event.x, event.y]):
                        self.mostrar_pensamiento(datos[etiquetas[i]][
                            'pensamiento'])
                        self.pensamiento_seleccionado = etiquetas[i]
                        self.crear_grafico_frecuencia()
                        break
        canvas.mpl_connect('button_press_event', on_click)

    def crear_grafico_frecuencia(self):
        if not self.pensamiento_seleccionado:
            return
        datos_diarios = self.obtener_datos_diarios(self.
            pensamiento_seleccionado)
        if not datos_diarios:
            return
        frame_derecho = ttk.Frame(self.frame_graficos)
        frame_derecho.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        fig = Figure(figsize=(6, 3))
        ax = fig.add_subplot(111)
        fechas = [row[0] for row in datos_diarios]
        dimension = self.dimension_actual.get()
        if dimension == 'veces':
            valores = [row[1] for row in datos_diarios]
            titulo = 'Cantidad de veces'
            ymax = max(valores)
        elif dimension == 'minutos':
            valores = [row[2] for row in datos_diarios]
            titulo = 'Duración (minutos)'
            ymax = max(valores)
        else:
            valores = [row[3] for row in datos_diarios]
            titulo = 'Intensidad'
            ymax = 10
        ax.plot(fechas, valores, marker='o')
        ax.set_ylim(0, ymax)
        ax.set_xlabel('Fecha')
        ax.set_ylabel(titulo)
        plt.setp(ax.get_xticklabels(), rotation=45)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame_derecho)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT pensamiento FROM pensamientos WHERE codigo = ?', (
                self.pensamiento_seleccionado,))
            pensamiento = cursor.fetchone()[0]
            conn.close()
            frame_descripcion = ttk.LabelFrame(frame_derecho, text=
                'Descripción del Pensamiento')
            frame_descripcion.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            text_descripcion = tk.Text(frame_descripcion, wrap=tk.WORD,
                height=5, padx=10, pady=10)
            text_descripcion.insert('1.0', pensamiento)
            text_descripcion.config(state='disabled')
            scrollbar = ttk.Scrollbar(frame_descripcion, command=
                text_descripcion.yview)
            text_descripcion.configure(yscrollcommand=scrollbar.set)
            text_descripcion.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        except sqlite3.Error as e:
            messagebox.showerror('Error',
                f'Error al obtener descripción: {str(e)}')

    def mostrar_pensamiento(self, pensamiento):
        ventana = tk.Toplevel(self.ventana)
        ventana.title('Detalle del Pensamiento')
        ventana.geometry('400x300')
        text = tk.Text(ventana, wrap=tk.WORD, padx=10, pady=10)
        text.insert('1.0', pensamiento)
        text.config(state='disabled')
        text.pack(fill=tk.BOTH, expand=True)
        ttk.Button(ventana, text='Cerrar', command=ventana.destroy).pack(pady
            =10)


class GestorDB:

    def __init__(self, ruta_db: str):
        self.ruta_db = ruta_db

    @contextmanager
    def conexion(self):
        conn = None
        try:
            conn = sqlite3.connect(self.ruta_db)
            yield conn
        finally:
            if conn:
                conn.close()

    def obtener_datos_paciente(self, codigo_paciente: str, fecha_inicio:
        str, fecha_fin: str) ->Dict[str, List[DatosPensamiento]]:
        with self.conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.codigo, p.pensamiento, d.cantidad, d.duracion, d.intensidad, d.fecha
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo LIKE ? AND d.fecha BETWEEN ? AND ?
                ORDER BY d.fecha
            """
                , (f'{codigo_paciente}%', fecha_inicio, fecha_fin))
            datos = {}
            for row in cursor.fetchall():
                codigo = row[0]
                if codigo not in datos:
                    datos[codigo] = []
                datos[codigo].append(DatosPensamiento(pensamiento=row[1],
                    cantidad=row[2] or 0, duracion=row[3] or 0, intensidad=
                    row[4] or 0, fecha=row[5]))
            return datos


class GestorGraficos:

    def __init__(self):
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))

    def crear_grafico_circular(self, datos: Dict[str, List[DatosPensamiento
        ]], dimension: str) ->Figure:
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        valores = []
        etiquetas = []
        colores = []
        for codigo, registros in datos.items():
            valor = sum(getattr(d, dimension) for d in registros)
            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
                color = self._obtener_color(dimension, valor / len(registros))
                colores.append(color)
        if valores:
            wedges, texts, autotexts = ax.pie(valores, labels=etiquetas,
                colors=colores, autopct='%1.1f%%', startangle=90)
            plt.setp(autotexts, size=8)
            plt.setp(texts, size=8)
            ax.legend(wedges, etiquetas, title='Pensamientos', loc=
                'center left', bbox_to_anchor=(1, 0, 0.5, 1))
        return fig

    def _obtener_color(self, dimension: str, valor: float) ->str:
        if dimension == 'intensidad':
            if valor <= 3:
                return 'lightgreen'
            if valor <= 7:
                return 'yellow'
            return 'red'
        return self.colores_base[hash(str(valor)) % len(self.colores_base)]


class VentanaEstadisticas:

    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title('Estadísticas de Pensamientos')
        self.ventana.geometry('1280x800')
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value='veces')
        self.pensamiento_seleccionado = None
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))
        self.crear_widgets()
        self.cargar_pacientes()

    def _crear_interfaz(self):
        self.main_frame = ttk.Frame(self.ventana, padding='10')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._crear_panel_control()
        self._crear_panel_graficos()

    def _crear_panel_control(self):
        panel = ttk.LabelFrame(self.main_frame, text='Controles', padding='5')
        panel.pack(fill=tk.X, padx=5, pady=5)
        frame_paciente = ttk.Frame(panel)
        frame_paciente.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(frame_paciente, text='Paciente:').pack(side=tk.LEFT)
        self.combo_pacientes = ttk.Combobox(frame_paciente, textvariable=
            self.paciente_seleccionado, state='readonly', width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=(5, 20))
        frame_fechas = ttk.Frame(panel)
        frame_fechas.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(frame_fechas, text='Periodo:').pack(side=tk.LEFT)
        self.fecha_inicio = DateEntry(frame_fechas, width=12, background=
            'darkblue', date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_fechas, text='hasta').pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(frame_fechas, width=12, background=
            'darkblue', date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        frame_botones = ttk.Frame(panel)
        frame_botones.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(frame_botones, text='Actualizar', command=self.
            _actualizar_graficos).pack(side=tk.LEFT)
        ttk.Button(frame_botones, text='Exportar', command=self._exportar_datos
            ).pack(side=tk.LEFT, padx=5)

    def _crear_panel_graficos(self):
        self.canvas_graficos = tk.Canvas(self.main_frame)
        scrollbar = ttk.Scrollbar(self.main_frame, orient='vertical',
            command=self.canvas_graficos.yview)
        self.frame_graficos = ttk.Frame(self.canvas_graficos)
        self.canvas_graficos.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_graficos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_graficos.create_window((0, 0), window=self.
            frame_graficos, anchor='nw')
        self.frame_graficos.bind('<Configure>', lambda e: self.
            canvas_graficos.configure(scrollregion=self.canvas_graficos.
            bbox('all')))

    def _actualizar_graficos(self):
        if not self._validar_fechas():
            return
        try:
            datos = self.db.obtener_datos_paciente(self.
                paciente_seleccionado.get().split(' - ')[0], self.
                fecha_inicio.get_date().strftime('%Y-%m-%d'), self.
                fecha_fin.get_date().strftime('%Y-%m-%d'))
            self._mostrar_graficos(datos)
        except Exception as e:
            messagebox.showerror('Error',
                f'Error al actualizar gráficos: {str(e)}')

    def _validar_fechas(self) ->bool:
        if self.fecha_inicio.get_date() > self.fecha_fin.get_date():
            messagebox.showerror('Error',
                'La fecha inicial no puede ser posterior a la fecha final')
            return False
        return True

    def _exportar_datos(self):
        pass

    def crear_widgets(self):
        self.main_frame = ttk.Frame(self.ventana, padding='10')
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        panel_control = ttk.Frame(self.main_frame)
        panel_control.grid(row=0, column=0, columnspan=2, sticky='ew', pady
            =(0, 10))
        ttk.Label(panel_control, text='Paciente:').pack(side=tk.LEFT, padx=5)
        self.combo_pacientes = ttk.Combobox(panel_control, textvariable=
            self.paciente_seleccionado, state='readonly', width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.
            actualizar_graficos)
        ttk.Label(panel_control, text='Desde:').pack(side=tk.LEFT, padx=5)
        self.fecha_inicio = DateEntry(panel_control, width=12, background=
            'darkblue', foreground='white', date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        ttk.Label(panel_control, text='Hasta:').pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(panel_control, width=12, background=
            'darkblue', foreground='white', date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_control, text='Actualizar', command=self.
            actualizar_graficos).pack(side=tk.LEFT, padx=20)
        frame_dimension = ttk.LabelFrame(panel_control, text='Dimensión',
            padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        for dimension in ['veces', 'minutos', 'intensidad']:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                variable=self.dimension_actual, value=dimension, command=
                self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        self.frame_graficos = ttk.Frame(self.main_frame)
        self.frame_graficos.grid(row=1, column=0, columnspan=2, sticky='nsew')
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

    def cargar_pacientes(self):
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT codigo, nombre FROM pacientes ORDER BY codigo')
            pacientes = cursor.fetchall()
            self.combo_pacientes['values'] = [f'{p[0]} - {p[1]}' for p in
                pacientes]
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror('Error',
                f'Error al cargar pacientes: {str(e)}')

    def obtener_datos_dimensiones(self):
        if not self.paciente_seleccionado.get():
            return {}
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.codigo, p.pensamiento, 
                       SUM(d.cantidad) as total_cantidad,
                       SUM(d.duracion) as total_duracion,
                       AVG(d.intensidad) as promedio_intensidad,
                       MAX(d.cantidad) as max_cantidad,
                       MAX(d.duracion) as max_duracion
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo LIKE ? 
                AND d.fecha BETWEEN ? AND ?
                GROUP BY p.codigo, p.pensamiento
            """
                , (f'{codigo_paciente}%', fecha_inicio, fecha_fin))
            resultados = {}
            for row in cursor.fetchall():
                resultados[row[0]] = {'pensamiento': row[1], 'cantidad': 
                    row[2] or 0, 'duracion': row[3] or 0, 'intensidad': row
                    [4] or 0, 'max_cantidad': row[5] or 0, 'max_duracion': 
                    row[6] or 0}
            conn.close()
            return resultados
        except sqlite3.Error as e:
            messagebox.showerror('Error', f'Error al obtener datos: {str(e)}')
            return {}

    def obtener_datos_diarios(self, codigo_pensamiento):
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.fecha, d.cantidad, d.duracion, d.intensidad
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo = ? 
                AND d.fecha BETWEEN ? AND ?
                ORDER BY d.fecha
            """
                , (codigo_pensamiento, fecha_inicio, fecha_fin))
            datos_diarios = cursor.fetchall()
            conn.close()
            return datos_diarios
        except sqlite3.Error as e:
            messagebox.showerror('Error',
                f'Error al obtener datos diarios: {str(e)}')
            return []

    def actualizar_graficos(self, event=None):
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
        if not self.paciente_seleccionado.get():
            return
        self.crear_grafico_circular()
        if self.pensamiento_seleccionado:
            self.crear_grafico_frecuencia()

    def crear_grafico_circular(self):
        datos = self.obtener_datos_dimensiones()
        if not datos:
            return
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        dimension = self.dimension_actual.get()
        valores = []
        etiquetas = []
        colores = []
        for codigo, info in datos.items():
            if dimension == 'veces':
                valor = info['cantidad']
                colores.append(self.colores_base[len(colores) % len(self.
                    colores_base)])
            elif dimension == 'minutos':
                valor = info['duracion']
                colores.append(self.colores_base[len(colores) % len(self.
                    colores_base)])
            else:
                valor = info['intensidad']
                if valor <= 3:
                    colores.append('lightgreen')
                elif valor <= 7:
                    colores.append('yellow')
                else:
                    colores.append('red')
            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
        if not valores:
            return
        wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, colors
            =colores, autopct='%1.1f%%', startangle=90)
        plt.setp(autotexts, size=8)
        plt.setp(texts, size=8)
        ax.legend(wedges, etiquetas, title='Pensamientos', loc=
            'center left', bbox_to_anchor=(1, 0, 0.5, 1))
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew', padx=5,
            pady=5)

        def on_click(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_point([event.x, event.y]):
                        self.mostrar_pensamiento(datos[etiquetas[i]][
                            'pensamiento'])
                        self.pensamiento_seleccionado = etiquetas[i]
                        self.crear_grafico_frecuencia()
                        break
        canvas.mpl_connect('button_press_event', on_click)

    def crear_grafico_frecuencia(self):
        if not self.pensamiento_seleccionado:
            return
        datos_diarios = self.obtener_datos_diarios(self.
            pensamiento_seleccionado)
        if not datos_diarios:
            return
        frame_derecho = ttk.Frame(self.frame_graficos)
        frame_derecho.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        fig = Figure(figsize=(6, 3))
        ax = fig.add_subplot(111)
        fechas = [row[0] for row in datos_diarios]
        dimension = self.dimension_actual.get()
        if dimension == 'veces':
            valores = [row[1] for row in datos_diarios]
            titulo = 'Cantidad de veces'
            ymax = max(valores)
        elif dimension == 'minutos':
            valores = [row[2] for row in datos_diarios]
            titulo = 'Duración (minutos)'
            ymax = max(valores)
        else:
            valores = [row[3] for row in datos_diarios]
            titulo = 'Intensidad'
            ymax = 10
        ax.plot(fechas, valores, marker='o')
        ax.set_ylim(0, ymax)
        ax.set_xlabel('Fecha')
        ax.set_ylabel(titulo)
        plt.setp(ax.get_xticklabels(), rotation=45)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame_derecho)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT pensamiento FROM pensamientos WHERE codigo = ?', (
                self.pensamiento_seleccionado,))
            pensamiento = cursor.fetchone()[0]
            conn.close()
            frame_descripcion = ttk.LabelFrame(frame_derecho, text=
                'Descripción del Pensamiento')
            frame_descripcion.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            text_descripcion = tk.Text(frame_descripcion, wrap=tk.WORD,
                height=5, padx=10, pady=10)
            text_descripcion.insert('1.0', pensamiento)
            text_descripcion.config(state='disabled')
            scrollbar = ttk.Scrollbar(frame_descripcion, command=
                text_descripcion.yview)
            text_descripcion.configure(yscrollcommand=scrollbar.set)
            text_descripcion.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        except sqlite3.Error as e:
            messagebox.showerror('Error',
                f'Error al obtener descripción: {str(e)}')

    def mostrar_pensamiento(self, pensamiento):
        ventana = tk.Toplevel(self.ventana)
        ventana.title('Detalle del Pensamiento')
        ventana.geometry('400x300')
        text = tk.Text(ventana, wrap=tk.WORD, padx=10, pady=10)
        text.insert('1.0', pensamiento)
        text.config(state='disabled')
        text.pack(fill=tk.BOTH, expand=True)
        ttk.Button(ventana, text='Cerrar', command=ventana.destroy).pack(pady
            =10)


if __name__ == '__main__':
    app = VentanaEstadisticas()
    app.ventana.mainloop()
