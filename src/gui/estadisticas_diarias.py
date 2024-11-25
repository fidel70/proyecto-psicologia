import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import os

class VentanaEstadisticas:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Estadísticas de Pensamientos - Vista Diaria")
        self.ventana.geometry("800x600")
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value="veces")
        self.fecha_actual = datetime.now()
        
        self.crear_widgets()
        self.cargar_pacientes()
        
    def crear_widgets(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Panel superior (controles)
        panel_superior = ttk.Frame(self.main_frame)
        panel_superior.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Selector de paciente
        ttk.Label(panel_superior, text="Paciente:").pack(side=tk.LEFT, padx=5)
        self.combo_pacientes = ttk.Combobox(panel_superior, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.actualizar_grafico)
        
        # Selector de dimensión
        frame_dimension = ttk.LabelFrame(panel_superior, text="Dimensión", padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        
        for dimension in ["veces", "minutos", "intensidad"]:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                          variable=self.dimension_actual, value=dimension,
                          command=self.actualizar_grafico).pack(side=tk.LEFT, padx=5)
        
        # Frame para gráfico
        self.frame_grafico = ttk.Frame(self.main_frame)
        self.frame_grafico.grid(row=1, column=0, sticky="nsew")
        
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
            
    def obtener_datos_dia(self):
        if not self.paciente_seleccionado.get():
            return {}
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha = self.fecha_actual.strftime('%Y-%m-%d')
        
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
                WHERE p.codigo LIKE ? AND d.fecha = ?
                GROUP BY p.codigo, p.pensamiento
                HAVING total_cantidad > 0
            """, (f'{codigo_paciente}%', fecha))
            
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
            
    def actualizar_grafico(self, event=None):
        # Limpiar frame de gráfico
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
            
        datos = self.obtener_datos_dia()
        if not datos:
            return
            
        # Crear figura
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        # Preparar datos según dimensión seleccionada
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
                    # Color según intensidad
                    if info['intensidad'] <= 3:
                        colores.append('lightgreen')
                    elif info['intensidad'] <= 7:
                        colores.append('yellow')
                    else:
                        colores.append('red')
                else:
                    colores.append(plt.cm.Set3(len(colores) % 12))
        
        if not valores:
            return
            
        # Crear gráfico circular
        wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, colors=colores,
                                         autopct='%1.1f%%', startangle=90)
        
        # Ajustar etiquetas
        plt.setp(autotexts, size=8)
        plt.setp(texts, size=8)
        
        # Añadir leyenda
        ax.legend(wedges, etiquetas,
                 title="Pensamientos",
                 loc="center left",
                 bbox_to_anchor=(1, 0, 0.5, 1))
        
        # Ajustar layout
        fig.tight_layout()
        
        # Crear canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Evento de clic para mostrar pensamiento
        def on_click(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_point([event.x, event.y]):
                        self.mostrar_pensamiento(datos[etiquetas[i]]['pensamiento'])
                        break
                        
        canvas.mpl_connect('button_press_event', on_click)
        
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
        
    def run(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    app = VentanaEstadisticas()
    app.run()