import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from collections import defaultdict

class VentanaEstadisticas:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Estadísticas de Pensamientos")
        self.ventana.geometry("1200x800")
        
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.periodo_actual = tk.StringVar(value="día")
        self.dimension_actual = tk.StringVar(value="veces")
        self.pensamiento_seleccionado = None
        self.datos_pensamientos = {}  # Para almacenar datos de pensamientos
        self.colores_pensamientos = {}  # Para mantener consistencia en colores
        
        self.crear_widgets()
        self.cargar_pacientes()

    def crear_widgets(self):
        # Panel superior
        panel_superior = ttk.Frame(self.main_frame)
        panel_superior.pack(fill=tk.X, pady=10)
        
        # Selección de paciente
        ttk.Label(panel_superior, text="Paciente:").pack(side=tk.LEFT, padx=5)
        self.combo_pacientes = ttk.Combobox(panel_superior, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.actualizar_estadisticas)
        
        # Selección de periodo
        ttk.Label(panel_superior, text="Periodo:").pack(side=tk.LEFT, padx=5)
        for periodo in ["día", "semana", "mes"]:
            ttk.Radiobutton(panel_superior, text=periodo, value=periodo,
                          variable=self.periodo_actual,
                          command=self.actualizar_estadisticas).pack(side=tk.LEFT, padx=5)
        
        # Panel de gráficos
        self.panel_graficos = ttk.Frame(self.main_frame)
        self.panel_graficos.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Panel izquierdo (gráfico circular)
        self.panel_izq = ttk.LabelFrame(self.panel_graficos, text="Distribución de Pensamientos")
        self.panel_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Botones de dimensión
        panel_botones = ttk.Frame(self.panel_izq)
        panel_botones.pack(fill=tk.X, pady=5)
        
        for dimension in ["veces", "minutos", "intensidad"]:
            ttk.Radiobutton(panel_botones, text=dimension, value=dimension,
                          variable=self.dimension_actual,
                          command=self.actualizar_grafico_circular).pack(side=tk.LEFT, padx=5)
        
        # Panel derecho (gráfico de línea para semana/mes)
        self.panel_der = ttk.LabelFrame(self.panel_graficos, text="Evolución Temporal")
        self.panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

    def cargar_pacientes(self):
        try:
            conn = sqlite3.connect('../../db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nombre FROM pacientes ORDER BY codigo")
            pacientes = cursor.fetchall()
            self.combo_pacientes['values'] = [f"{p[0]} - {p[1]}" for p in pacientes]
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar pacientes: {str(e)}")

    def obtener_datos_periodo(self):
        if not self.paciente_seleccionado.get():
            return None
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha_actual = datetime.now().date()
        
        if self.periodo_actual.get() == "día":
            fecha_inicio = fecha_actual
        elif self.periodo_actual.get() == "semana":
            fecha_inicio = fecha_actual - timedelta(days=6)
        else:  # mes
            fecha_inicio = fecha_actual - timedelta(days=29)
            
        try:
            conn = sqlite3.connect('../../db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.codigo, p.pensamiento, d.fecha, d.cantidad, d.duracion, d.intensidad
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo LIKE ? AND d.fecha BETWEEN ? AND ?
                ORDER BY d.fecha
            """, (f'{codigo_paciente}%', fecha_inicio, fecha_actual))
            
            datos = cursor.fetchall()
            conn.close()
            
            return datos
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener datos: {str(e)}")
            return None

    def generar_colores(self, n):
        if not self.colores_pensamientos:
            # Generar colores HSV espaciados uniformemente
            HSV_tuples = [(x/n, 0.7, 0.7) for x in range(n)]
            RGB_tuples = map(lambda x: plt.cm.hsv(x), HSV_tuples)
            return list(RGB_tuples)
        return list(self.colores_pensamientos.values())

    def mostrar_pensamiento(self, event):
        if not hasattr(event, 'artist') or not hasattr(event.artist, 'get_label'):
            return
            
        codigo = event.artist.get_label()
        if codigo in self.datos_pensamientos:
            ventana = tk.Toplevel(self.ventana)
            ventana.title(f"Detalle del Pensamiento - {codigo}")
            ventana.geometry("400x300")
            
            text = tk.Text(ventana, wrap=tk.WORD, padx=10, pady=10)
            text.insert('1.0', self.datos_pensamientos[codigo])
            text.config(state='disabled')
            text.pack(fill=tk.BOTH, expand=True)
            
            ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)

    def actualizar_grafico_circular(self):
        datos = self.obtener_datos_periodo()
        if not datos:
            return
            
        # Limpiar panel
        for widget in self.panel_izq.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        
        # Procesar datos
        dimension_idx = {'veces': 3, 'minutos': 4, 'intensidad': 5}[self.dimension_actual.get()]
        totales_pensamiento = defaultdict(float)
        
        for dato in datos:
            if dato[dimension_idx] is not None:  # Considerar valores nulos
                totales_pensamiento[dato[0]] += dato[dimension_idx]
                self.datos_pensamientos[dato[0]] = dato[1]  # Guardar descripción
        
        if not totales_pensamiento:
            return
            
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(6, 6))
        valores = list(totales_pensamiento.values())
        etiquetas = list(totales_pensamiento.keys())
        
        if self.dimension_actual.get() == 'intensidad':
            colores = ['#90EE90' if v <= 3 else '#FFD700' if v <= 7 else '#FF6B6B' 
                      for v in valores]
        else:
            colores = self.generar_colores(len(valores))
            
        # Actualizar colores consistentes
        for etiqueta, color in zip(etiquetas, colores):
            self.colores_pensamientos[etiqueta] = color
        
        patches, texts, autotexts = ax.pie(valores, labels=etiquetas, colors=colores,
                                         autopct='%1.1f%%', startangle=90)
        
        ax.axis('equal')
        
        # Conectar evento de click
        for patch in patches:
            patch.set_picker(True)
        
        canvas = FigureCanvasTkAgg(fig, master=self.panel_izq)
        canvas.mpl_connect('pick_event', self.mostrar_pensamiento)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def actualizar_grafico_linea(self):
        if self.periodo_actual.get() == "día":
            return
            
        datos = self.obtener_datos_periodo()
        if not datos or not self.pensamiento_seleccionado:
            return
            
        # Limpiar panel
        for widget in self.panel_der.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        
        # Filtrar datos del pensamiento seleccionado
        datos_pensamiento = [d for d in datos if d[0] == self.pensamiento_seleccionado]
        
        if not datos_pensamiento:
            return
            
        # Procesar datos por fecha
        dimension_idx = {'veces': 3, 'minutos': 4, 'intensidad': 5}[self.dimension_actual.get()]
        valores_por_fecha = defaultdict(float)
        
        fecha_inicio = datetime.strptime(datos_pensamiento[0][2], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(datos_pensamiento[-1][2], '%Y-%m-%d').date()
        
        # Llenar fechas faltantes con ceros
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            valores_por_fecha[fecha_actual] = 0
            fecha_actual += timedelta(days=1)
        
        # Sumar valores por fecha
        for dato in datos_pensamiento:
            if dato[dimension_idx] is not None:
                fecha = datetime.strptime(dato[2], '%Y-%m-%d').date()
                valores_por_fecha[fecha] += dato[dimension_idx]
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        fechas = list(valores_por_fecha.keys())
        valores = list(valores_por_fecha.values())
        
        ax.plot(fechas, valores, marker='o')
        ax.set_xlabel('Fecha')
        ax.set_ylabel(self.dimension_actual.get().capitalize())
        ax.set_title(f'Evolución de {self.dimension_actual.get()} - {self.pensamiento_seleccionado}')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.panel_der)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def actualizar_estadisticas(self, event=None):
        self.actualizar_grafico_circular()
        if self.periodo_actual.get() != "día":
            self.actualizar_grafico_linea()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = VentanaEstadisticas(root)
    root.mainloop()
