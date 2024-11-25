import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, Tuple

class EstadisticasPensamientos:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Estadísticas de Pensamientos")
        self.ventana.geometry("1200x800")
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value="veces")
        self.pensamiento_seleccionado = None
        self.perspectiva_3d = tk.BooleanVar(value=True)
        
        # Crear widgets
        self.crear_widgets()
        self.cargar_pacientes()
        
    def crear_widgets(self):
        # Frame principal con padding
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
        
        # Fechas
        frame_fechas = ttk.LabelFrame(panel_superior, text="Rango de fechas", padding=5)
        frame_fechas.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(frame_fechas, text="Desde:").pack(side=tk.LEFT, padx=5)
        self.fecha_inicio = DateEntry(frame_fechas, width=12, 
                                    background='darkblue', foreground='white',
                                    date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_fechas, text="Hasta:").pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(frame_fechas, width=12, 
                                 background='darkblue', foreground='white',
                                 date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        
        # Botón actualizar fechas
        ttk.Button(frame_fechas, text="Actualizar", 
                  command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        
        # Selector de dimensión
        frame_dimension = ttk.LabelFrame(panel_superior, text="Dimensión", padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        
        for dimension in ["veces", "minutos", "intensidad"]:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                          variable=self.dimension_actual, value=dimension,
                          command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        
        # Checkbox para perspectiva 3D
        ttk.Checkbutton(panel_superior, text="Vista 3D",
                       variable=self.perspectiva_3d,
                       command=self.actualizar_graficos).pack(side=tk.LEFT, padx=20)
        
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
            
    def obtener_datos_dimensiones(self) -> Dict:
        if not self.paciente_seleccionado.get():p
            return {}
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha_inicio = self.fecha_inicio.get_date()
        fecha_fin = self.fecha_fin.get_date()
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
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
            
    def obtener_datos_diarios(self, codigo_pensamiento: str) -> Dict:
        fecha_inicio = self.fecha_inicio.get_date()
        fecha_fin = self.fecha_fin.get_date()
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
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
            messagebox.showerror("Error", f"Error al obtener datos diarios: {str(e)}")
            return {}
    
    def actualizar_graficos(self, event=None):
        # Limpiar frame de gráficos
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
            
        if not self.paciente_seleccionado.get():
            return
            
        # Crear y mostrar gráfico circular
        self.crear_grafico_circular()
        
        # Mostrar gráfico de línea si hay pensamiento seleccionado
        if self.pensamiento_seleccionado:
            self.crear_grafico_linea()
            
    def crear_grafico_circular(self):
        datos = self.obtener_datos_dimensiones()
        if not datos:
            return
            
        # Crear figura para el gráfico circular
        fig = Figure(figsize=(6, 4))
        
        if self.perspectiva_3d.get():
            ax = fig.add_subplot(111, projection='3d')
            ax.set_proj_type('ortho')  # Proyección ortográfica para mejor visualización
        else:
            ax = fig.add_subplot(111)
        
        # Preparar datos según la dimensión seleccionada
        dimension = self.dimension_actual.get()
        valores = []
        etiquetas = []
        colores = []
        
        for codigo, info in datos.items():
            if dimension == "veces":
                valor = info['cantidad']
                color = plt.cm.Set3(len(colores) % 12)  # 12 colores diferentes
            elif dimension == "minutos":
                valor = info['duracion']
                color = plt.cm.Set3(len(colores) % 12)
            else:  # intensidad
                valor = info['intensidad']
                if valor <= 3:
                    color = 'lightgreen'
                elif valor <= 7:
                    color = 'yellow'
                else:
                    color = 'red'
                
            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
                colores.append(color)
        
        if not valores:
            return
            
        # Crear gráfico circular
        if self.perspectiva_3d.get():
            # Calcular coordenadas para el gráfico 3D
            suma = sum(valores)
            fracs = [v/suma for v in valores]
            angulos = [f*2.*np.pi for f in np.cumsum(fracs)]
            angulos = [0] + list(angulos)
            
            # Crear gráfico 3D
            z = np.zeros(100)
            r = np.ones(100)
            theta = np.linspace(0, 2*np.pi, 100)
            
            for i in range(len(fracs)):
                inicio = angulos[i]
                fin = angulos[i+1]
                theta_sector = np.linspace(inicio, fin, 100)
                x = r * np.cos(theta_sector)
                y = r * np.sin(theta_sector)
                
                # Crear superficie del sector
                ax.plot_surface(x.reshape(-1, 1), y.reshape(-1, 1), z.reshape(-1, 1) + 0.5,
                              color=colores[i], alpha=0.8)
                
            ax.set_zlim(0, 1)
            ax.set_box_aspect([1,1,0.3])
            
            # Añadir etiquetas
            for i, etiqueta in enumerate(etiquetas):
                angulo = (angulos[i] + angulos[i+1])/2
                x = 1.3 * np.cos(angulo)
                y = 1.3 * np.sin(angulo)
                ax.text(x, y, 0.5, etiqueta, ha='center', va='center')
                
        else:
            wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, colors=colores,
                                            autopct='%1.1f%%', startangle=90)
            
            # Ajustar tamaño de fuente
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
                if self.perspectiva_3d.get():
                    # Convertir coordenadas del clic a ángulo
                    x, y = event.xdata, event.ydata
                    if x is not None and y is not None:
                        angulo = np.arctan2(y, x)
                        if angulo < 0:
                            angulo += 2*np.pi
                            
                        # Encontrar el sector correspondiente
                        for i in range(len(fracs)):
                            if angulos[i] <= angulo <= angulos[i+1]:
                                self.mostrar_pensamiento(datos[etiquetas[i]]['pensamiento'])
                                self.pensamiento_seleccionado = etiquetas[i]
                                self.crear_grafico_linea()
                                break
                else:
                    for i, wedge in enumerate(wedges):
                        if wedge.contains_point([event.x, event.y]):
                            self.mostrar_pensamiento(datos[etiquetas[i]]['pensamiento'])
                            self.pensamiento_seleccionado = etiquetas[i]
                            self.crear_grafico_linea()
                            break
                            
        canvas.mpl_connect('button_press_event', on_click)
        
    def crear_grafico_linea(self):
        if not self.pensamiento_seleccionado:
            return
            
        datos = self.obtener_datos_diarios(self.pensamiento_seleccionado)
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
           titulo = "Cantidad de veces por día"
           ymax = max(valores) if valores else 10
        elif dimension == "minutos":
           valores = [datos[fecha]['duracion'] for fecha in fechas]
           titulo = "Duración total por día (minutos)"
           ymax = max(valores) if valores else 60
        else:  # intensidad
            valores = [datos[fecha]['intensidad'] for fecha in fechas]
            titulo = "Intensidad promedio por día"
            ymax = 10
                        
            # Crear gráfico de línea
            ax.plot(fechas, valores, marker='o', linestyle='-', color='blue')
            
            # Configurar ejes
            ax.set_xlabel("Fecha")
            ax.set_ylabel(titulo)
            ax.set_ylim(0, ymax)
            
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
        text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(ventana, text="Cerrar", 
                  command=ventana.destroy).pack(pady=10)

    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    app = EstadisticasPensamientos()
    app.ejecutar()