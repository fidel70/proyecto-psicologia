import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import calendar
import numpy as np
from typing import List, Dict, Tuple
import os

class VentanaEstadisticas:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Estadísticas de Pensamientos")
        self.ventana.geometry("1200x800")
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.periodo_actual = tk.StringVar(value="día")
        self.dimension_actual = tk.StringVar(value="veces")
        self.fecha_actual = datetime.now()
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))  # 12 colores diferentes
        self.pensamiento_seleccionado = None
        
        self.crear_widgets()
        self.cargar_pacientes()
        
    def crear_widgets(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Panel superior
        panel_superior = ttk.Frame(self.main_frame)
        panel_superior.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Selector de paciente
        ttk.Label(panel_superior, text="Paciente:").pack(side=tk.LEFT, padx=5)
        self.combo_pacientes = ttk.Combobox(panel_superior, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.actualizar_graficos)
        
        # Selector de período
        frame_periodo = ttk.LabelFrame(panel_superior, text="Período", padding=5)
        frame_periodo.pack(side=tk.LEFT, padx=20)
        
        for periodo in ["día", "semana", "mes"]:
            ttk.Radiobutton(frame_periodo, text=periodo.capitalize(), 
                          variable=self.periodo_actual, value=periodo,
                          command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        
        # Selector de dimensión para el gráfico circular
        frame_dimension = ttk.LabelFrame(panel_superior, text="Dimensión", padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        
        for dimension in ["veces", "minutos", "intensidad"]:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                          variable=self.dimension_actual, value=dimension,
                          command=self.actualizar_grafico_circular).pack(side=tk.LEFT, padx=5)
        
        # Frame para gráficos
        self.frame_graficos = ttk.Frame(self.main_frame)
        self.frame_graficos.grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        # Configurar el grid
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
    def cargar_pacientes(self):
        try:
            conn = sqlite3.connect(os.path.join('..', '..', 'data', 'db_psicologia_clinic.db'))
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nombre FROM pacientes ORDER BY codigo")
            pacientes = cursor.fetchall()
            self.combo_pacientes['values'] = [f"{p[0]} - {p[1]}" for p in pacientes]
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar pacientes: {str(e)}")
            
    def obtener_datos_periodo(self) -> Tuple[datetime, datetime, str]:
        fecha_fin = datetime.now()
        
        if self.periodo_actual.get() == "día":
            fecha_inicio = fecha_fin.replace(hour=0, minute=0, second=0, microsecond=0)
            formato_fecha = "%H:00"
        elif self.periodo_actual.get() == "semana":
            fecha_inicio = fecha_fin - timedelta(days=7)
            formato_fecha = "%d/%m"
        else:  # mes
            fecha_inicio = fecha_fin.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            formato_fecha = "%d/%m"
            
        return fecha_inicio, fecha_fin, formato_fecha
    
    def obtener_datos_dimensiones(self) -> Dict:
        if not self.paciente_seleccionado.get():
            return {}
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha_inicio, fecha_fin, _ = self.obtener_datos_periodo()
        
        try:
            conn = sqlite3.connect(os.path.join('..', '..', 'data', 'db_psicologia_clinic.db'))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.codigo, p.pensamiento, 
                       SUM(d.cantidad) as total_cantidad,
                       SUM(d.duracion) as total_duracion,
                       AVG(d.intensidad) as promedio_intensidad
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo LIKE ? 
                AND d.fecha BETWEEN ? AND ?
                GROUP BY p.codigo, p.pensamiento
            """, (f'{codigo_paciente}%', fecha_inicio.strftime('%Y-%m-%d'), 
                  fecha_fin.strftime('%Y-%m-%d')))
            
            resultados = {}
            for row in cursor.fetchall():
                resultados[row[0]] = {
                    'pensamiento': row[1],
                    'cantidad': row[2] or 0,
                    'duracion': row[3] or 0,
                    'intensidad': row[4] or 0
                }
                
            conn.close()
            return resultados
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener datos: {str(e)}")
            return {}
            
    def obtener_datos_temporales(self, codigo_pensamiento: str = None) -> Dict:
        if not self.paciente_seleccionado.get():
            return {}
            
        fecha_inicio, fecha_fin, _ = self.obtener_datos_periodo()
        
        try:
            conn = sqlite3.connect(os.path.join('..', '..', 'data', 'db_psicologia_clinic.db'))
            cursor = conn.cursor()
            
            if codigo_pensamiento:
                cursor.execute("""
                    SELECT d.fecha, 
                           SUM(d.cantidad) as total_cantidad,
                           SUM(d.duracion) as total_duracion,
                           AVG(d.intensidad) as promedio_intensidad
                    FROM dimensiones d
                    JOIN pensamientos p ON d.pensamiento_id = p.id
                    WHERE p.codigo = ? 
                    AND d.fecha BETWEEN ? AND ?
                    GROUP BY d.fecha
                    ORDER BY d.fecha
                """, (codigo_pensamiento, fecha_inicio.strftime('%Y-%m-%d'), 
                      fecha_fin.strftime('%Y-%m-%d')))
            else:
                codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
                cursor.execute("""
                    SELECT d.fecha, 
                           SUM(d.cantidad) as total_cantidad,
                           SUM(d.duracion) as total_duracion,
                           AVG(d.intensidad) as promedio_intensidad
                    FROM dimensiones d
                    JOIN pensamientos p ON d.pensamiento_id = p.id
                    WHERE p.codigo LIKE ? 
                    AND d.fecha BETWEEN ? AND ?
                    GROUP BY d.fecha
                    ORDER BY d.fecha
                """, (f'{codigo_paciente}%', fecha_inicio.strftime('%Y-%m-%d'), 
                      fecha_fin.strftime('%Y-%m-%d')))
            
            resultados = {}
            for row in cursor.fetchall():
                resultados[row[0]] = {
                    'cantidad': row[1] or 0,
                    'duracion': row[2] or 0,
                    'intensidad': row[3] or 0
                }
                
            conn.close()
            return resultados
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener datos temporales: {str(e)}")
            return {}
    
    def actualizar_graficos(self, event=None):
        # Limpiar frame de gráficos
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
            
        if not self.paciente_seleccionado.get():
            return
            
        # Crear y mostrar gráfico circular
        self.crear_grafico_circular()
        
        # Si es semana o mes, mostrar también el gráfico de línea
        if self.periodo_actual.get() in ["semana", "mes"]:
            self.crear_grafico_linea()
            
    def crear_grafico_circular(self):
        datos = self.obtener_datos_dimensiones()
        if not datos:
            return
            
        # Crear figura para el gráfico circular
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        
        # Preparar datos según la dimensión seleccionada
        dimension = self.dimension_actual.get()
        valores = []
        etiquetas = []
        colores = []
        
        for codigo, info in datos.items():
            if dimension == "veces":
                valor = info['cantidad']
            elif dimension == "minutos":
                valor = info['duracion']
            else:  # intensidad
                valor = info['intensidad']
                
            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
                
                if dimension == "intensidad":
                    # Definir color según intensidad
                    if info['intensidad'] <= 3:
                        colores.append('lightgreen')
                    elif info['intensidad'] <= 7:
                        colores.append('yellow')
                    else:
                        colores.append('red')
                else:
                    colores.append(self.colores_base[len(colores) % len(self.colores_base)])
        
        if not valores:
            return
            
        # Crear gráfico circular
        wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, colors=colores,
                                         autopct='%1.1f%%', startangle=90)
        
        # Ajustar tamaño de fuente y posición de etiquetas
        plt.setp(autotexts, size=8)
        plt.setp(texts, size=8)
        
        # Añadir leyenda
        ax.legend(wedges, etiquetas,
                 title="Pensamientos",
                 loc="center left",
                 bbox_to_anchor=(1, 0, 0.5, 1))
        
        # Crear canvas y empaquetarlo
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Conectar evento de clic
        def on_click(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_point([event.x, event.y]):
                        self.mostrar_pensamiento(datos[etiquetas[i]]['pensamiento'])
                        if self.periodo_actual.get() in ["semana", "mes"]:
                            self.pensamiento_seleccionado = etiquetas[i]
                            self.crear_grafico_linea()
                        break
                        
        canvas.mpl_connect('button_press_event', on_click)
        
    def crear_grafico_linea(self):
        if not self.pensamiento_seleccionado:
            return
            
        datos = self.obtener_datos_temporales(self.pensamiento_seleccionado)
        if not datos:
            return
            
        # Crear figura para el gráfico de línea
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        
        # Preparar datos
        fechas = list(datos.keys())
        dimension = self.dimension_actual.get()
        
        if dimension == "veces":
            valores = [datos[fecha]['cantidad'] for fecha in fechas]
            titulo = "Cantidad de veces"
        elif dimension == "minutos":
            valores = [datos[fecha]['duracion'] for fecha in fechas]
            titulo = "Duración (minutos)"
        else:  # intensidad
            valores = [datos[fecha]['intensidad'] for fecha in fechas]
            titulo = "Intensidad promedio"
            
        # Crear gráfico de línea
        ax.plot(fechas, valores, marker='o')
        
        # Configurar eje X
        ax.set_xlabel("Fecha")
        ax.set_ylabel(titulo)
        
        # Rotar etiquetas del eje X para mejor legibilidad
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # Ajustar layout
        fig.tight_layout()
        
        # Crear canvas y empaquetarlo
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
    def mostrar_pensamiento(self, pensamiento: str):
        ventana = tk.Toplevel(self.ventana)
        ventana.title("Detalle del Pensamiento")
        ventana.geometry("400x300")
        
        text = tk.Text(ventana, wrap=tk.WORD, padx=10, pady=10)
        text.insert('1.0', pensamiento)
        text.config(state='disabled')
        text.pack(fill=tk.BOTH, expand=True


        def actualizar_grafico_circular(self):
        # Actualizar solo el gráfico circular manteniendo el de línea si existe
        for widget in self.frame_graficos.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        
        self.crear_grafico_circular()
        if self.periodo_actual.get() in ["semana", "mes"] and self.pensamiento_seleccionado:
            self.crear_grafico_linea()

    def navegar_fecha(self, delta: int):
        if self.periodo_actual.get() == "día":
            self.fecha_actual += timedelta(days=delta)
        elif self.periodo_actual.get() == "semana":
            self.fecha_actual += timedelta(weeks=delta)
        else:  # mes
            año = self.fecha_actual.year
            mes = self.fecha_actual.month + delta
            
            if mes > 12:
                año += mes // 12
                mes = mes % 12
            elif mes < 1:
                año += (mes - 1) // 12
                mes = 12 + (mes - 1) % 12
                
            self.fecha_actual = self.fecha_actual.replace(year=año, month=mes)
            
        self.actualizar_graficos()

    def run(self):
        # Añadir botones de navegación
        frame_navegacion = ttk.Frame(self.main_frame)
        frame_navegacion.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(frame_navegacion, text="Anterior", 
                  command=lambda: self.navegar_fecha(-1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_navegacion, text="Siguiente",
                  command=lambda: self.navegar_fecha(1)).pack(side=tk.LEFT, padx=5)
        
        # Configurar cierre de ventana
        self.ventana.protocol("WM_DELETE_WINDOW", self.ventana.destroy)
        
        # Iniciar loop principal
        self.ventana.mainloop()

if __name__ == "__main__":
    app = VentanaEstadisticas()
    app.run()