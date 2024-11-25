import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

class VentanaEstadisticas:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Estadísticas de Pensamientos")
        self.ventana.geometry("1600x700")
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value="veces")
        self.pensamiento_seleccionado = None
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))
        
        self.crear_widgets()
        self.cargar_pacientes()
        
    def crear_widgets(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Panel de controles
        panel_control = ttk.Frame(self.main_frame)
        panel_control.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Selector de paciente
        ttk.Label(panel_control, text="Paciente:").pack(side=tk.LEFT, padx=5)
        self.combo_pacientes = ttk.Combobox(panel_control, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.actualizar_graficos)
        
        # Selector de fechas
        ttk.Label(panel_control, text="Desde:").pack(side=tk.LEFT, padx=5)
        self.fecha_inicio = DateEntry(panel_control, width=12, 
                                    background='darkblue', foreground='white',
                                    date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(panel_control, text="Hasta:").pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(panel_control, width=12, 
                                 background='darkblue', foreground='white',
                                 date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        
        # Botón actualizar
        ttk.Button(panel_control, text="Actualizar", 
                  command=self.actualizar_graficos).pack(side=tk.LEFT, padx=20)
        
        # Selector de dimensión para el gráfico circular
        frame_dimension = ttk.LabelFrame(panel_control, text="Dimensión", padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        
        for dimension in ["veces", "minutos", "intensidad"]:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                          variable=self.dimension_actual, value=dimension,
                          command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        
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
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nombre FROM pacientes ORDER BY codigo")
            pacientes = cursor.fetchall()
            self.combo_pacientes['values'] = [f"{p[0]} - {p[1]}" for p in pacientes]
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar pacientes: {str(e)}")
    
    def obtener_datos_dimensiones(self):
        if not self.paciente_seleccionado.get():
            return {}
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            cursor.execute("""
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
            """, (f'{codigo_paciente}%', fecha_inicio, fecha_fin))
            
            resultados = {}
            for row in cursor.fetchall():
                resultados[row[0]] = {
                    'pensamiento': row[1],
                    'cantidad': int(row[2]) if row[2] else 0,  # Ensure integer for cantidad
                    'duracion': row[3] or 0,
                    'intensidad': row[4] or 0,
                    'max_cantidad': int(row[5]) if row[5] else 0,  # Ensure integer for max_cantidad
                    'max_duracion': row[6] or 0
                }
                
            conn.close()
            return resultados
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener datos: {str(e)}")
            return {}
    
    def obtener_datos_diarios(self, codigo_pensamiento):
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT d.fecha, 
                       CAST(SUM(d.cantidad) AS INTEGER) as total_cantidad,
                       SUM(d.duracion) as total_duracion,
                       AVG(d.intensidad) as promedio_intensidad
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo = ? 
                AND d.fecha BETWEEN ? AND ?
                GROUP BY d.fecha
                ORDER BY d.fecha
            """, (codigo_pensamiento, fecha_inicio, fecha_fin))
            
            datos_diarios = cursor.fetchall()
            conn.close()
            return datos_diarios
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener datos diarios: {str(e)}")
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
            if dimension == "veces":
                valor = info['cantidad']
                colores.append(self.colores_base[len(colores) % len(self.colores_base)])
            elif dimension == "minutos":
                valor = info['duracion']
                colores.append(self.colores_base[len(colores) % len(self.colores_base)])
            else:  # intensidad
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
            
        wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, colors=colores,
                                         autopct='%1.1f%%' if dimension != "veces" else lambda pct: f'{int(pct*sum(valores)/100)}',
                                         startangle=90)
        
        plt.setp(autotexts, size=8)
        plt.setp(texts, size=8)
        
        ax.legend(wedges, etiquetas,
                 title="Pensamientos",
                 loc="center left",
                 bbox_to_anchor=(1, 0, 0.5, 1))
        
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        def on_click(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_point([event.x, event.y]):
                        self.mostrar_pensamiento(datos[etiquetas[i]]['pensamiento'])
                        self.pensamiento_seleccionado = etiquetas[i]
                        self.crear_grafico_frecuencia()
                        break
                        
        canvas.mpl_connect('button_press_event', on_click)
    
    def crear_grafico_frecuencia(self):
        if not self.pensamiento_seleccionado:
            return
            
        datos_diarios = self.obtener_datos_diarios(self.pensamiento_seleccionado)
        if not datos_diarios:
            return
            
        frame_derecho = ttk.Frame(self.frame_graficos)
        frame_derecho.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        fig = Figure(figsize=(6, 3))
        ax = fig.add_subplot(111)
        
        fechas = [row[0] for row in datos_diarios]
        dimension = self.dimension_actual.get()
        
        if dimension == "veces":
            valores = [int(row[1]) for row in datos_diarios]  # Ensure integer values
            titulo = "Cantidad de veces"
            ymax = max(valores) if valores else 1
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))  # Force integer ticks
        elif dimension == "minutos":
            valores = [row[2] for row in datos_diarios]
            titulo = "Duración (minutos)"
            ymax = max(valores) if valores else 1
        else:  # intensidad
            valores = [row[3] for row in datos_diarios]
            titulo = "Intensidad"
            ymax = 10
        
        ax.plot(fechas, valores, marker='o')
        ax.set_ylim(0, ymax * 1.1)  # Add 10% padding to y-axis
        
        ax.set_xlabel("Fecha")
        ax.set_ylabel(titulo)
        
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame_derecho)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT pensamiento FROM pensamientos WHERE codigo = ?", 
                         (self.pensamiento_seleccionado,))
            pensamiento = cursor.fetchone()[0]
            conn.close()
            
            frame_descripcion = ttk.LabelFrame(frame_derecho, text="Descripción del Pensamiento")
            frame_descripcion.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            
            text_descripcion = tk.Text(frame_descripcion, wrap=tk.WORD, height=5, 
                                     padx=10, pady=10)
            text_descripcion.insert('1.0', pensamiento)
            text_descripcion.config(state='disabled')
            
            scrollbar = ttk.Scrollbar(frame_descripcion, command=text_descripcion.yview)
            text_descripcion.configure(yscrollcommand=scrollbar.set)
            
            text_descripcion.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener descripción: {str(e)}")
    
    def mostrar_pensamiento(self, pensamiento):
        ventana = tk.Toplevel(self.ventana)
        ventana.title("Detalle del Pensamiento")
        ventana.geometry("400x300")
        
        text = tk.Text(ventana, wrap=tk.WORD, padx=10, pady=10)
        text.insert('1.0', pensamiento)
        text.config(state='disabled')
        text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(ventana, text="Cerrar", 
                  command=ventana.destroy).pack(pady=10)

if __name__ == "__main__":
    app = VentanaEstadisticas()
    app.ventana.mainloop()
