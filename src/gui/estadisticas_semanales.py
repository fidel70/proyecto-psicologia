import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import os

class VentanaEstadisticas:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Estadísticas de Pensamientos - Vista Semanal")
        self.ventana.geometry("1200x700")
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value="veces")
        self.pensamiento_seleccionado = None
        
        # Calcular fechas de la semana
        hoy = datetime.now()
        self.fecha_fin = hoy
        dias_al_lunes = hoy.weekday()
        self.fecha_inicio = hoy - timedelta(days=dias_al_lunes)
        
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
        
        # Selector de dimensión
        frame_dimension = ttk.LabelFrame(panel_superior, text="Dimensión", padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        
        for dimension in ["veces", "minutos", "intensidad"]:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                          variable=self.dimension_actual, value=dimension,
                          command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        
        # Frame para gráficos
        self.frame_graficos = ttk.Frame(self.main_frame)
        self.frame_graficos.grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        # Etiqueta del período
        ttk.Label(self.main_frame, 
                 text=f"Período: {self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}",
                 font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, pady=10)
        
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
            
    def obtener_datos_semana(self):
        if not self.paciente_seleccionado.get():
            return {}
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        
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
                HAVING total_cantidad > 0
            """, (f'{codigo_paciente}%', 
                  self.fecha_inicio.strftime('%Y-%m-%d'),
                  self.fecha_fin.strftime('%Y-%m-%d')))
            
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
            
    def obtener_datos_diarios(self, codigo_pensamiento):
        try:
            conn = sqlite3.connect(os.path.join('..', '..', 'data', 'db_psicologia_clinic.db'))
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
            """, (codigo_pensamiento,
                  self.fecha_inicio.strftime('%Y-%m-%d'),
                  self.fecha_fin.strftime('%Y-%m-%d')))
            
            resultados = {}
            for row in cursor.fetchall():
                resultados[row[0]] = {
                    'cantidad': row[1] or 0,
                    'duracion': row[2] or 0,
                    'intensidad': row[3] or 0
                }
            
            # Llenar días faltantes con ceros
            fecha_actual = self.fecha_inicio
            while fecha_actual <= self.fecha_fin:
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
                if fecha_str not in resultados:
                    resultados[fecha_str] = {
                        'cantidad': 0,
                        'duracion': 0,
                        'intensidad': 0
                    }
                fecha_actual += timedelta(days=1)
                
            conn.close()
            return dict(sorted(resultados.items()))
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener datos diarios: {str(e)}")
            return {}
            
    def actualizar_graficos(self, event=None):
        # Limpiar frame de gráficos
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
            
        if not self.paciente_seleccionado.get():
            return
            
        # Crear gráfico circular
        self.crear_grafico_circular()
        
        # Crear gráfico de línea si hay un pensamiento seleccionado
        if self.pensamiento_seleccionado:
            self.crear_grafico_linea()
            
    def crear_grafico_circular(self):
        datos = self.obtener_datos_semana()
        if not datos:
            return
            
        # Crear figura
        fig = Figure(figsize=(6, 5))
        ax = fig.add_subplot(111)
        
        # Preparar datos
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
        
        fig.tight_layout()
        
        # Crear canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, padx=5, pady=5)
        
        # Evento de clic
        def on_click(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_point([event.x, event.y]):
                        self.pensamiento_seleccionado = etiquetas[i]
                        self.mostrar_pensamiento(datos[etiquetas[i]]['pensamiento'])
                        self.crear_grafico_linea()
                        break
                        
        canvas.mpl_connect('button_press_event', on_click)
        
    def crear_grafico_linea(self):
        if not self.pensamiento_seleccionado:
            return
            
        datos = self.obtener_datos_diarios(self.pensamiento_seleccionado)
        if not datos:
            return
            
        # Crear figura
        fig = Figure(figsize=(6, 5))
        ax = fig.add_subplot(111)
        
        # Preparar datos
        fechas = list(datos.keys())
        dimension = self.dimension_actual.get()
        
        if dimension == "veces":
            valores = [datos[fecha]['cantidad'] for fecha in fechas]
            titulo = "Cantidad de veces por día"
        elif dimension == "minutos":
            valores = [datos[fecha]['duracion'] for fecha in fechas]
            titulo = "Duración (minutos) por día"
        else:  # intensidad
            valores = [datos[fecha]['intensidad'] for fecha in fechas]
            titulo = "Intensidad promedio por día"
            
        # Crear gráfico de línea
        ax.plot(range(len(fechas)), valores, marker='o')
        
        # Configurar eje X
        ax.set_xticks(range(len(fechas)))
        ax.set_xticklabels([datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m')
                           for fecha in fechas], rotation=45)
        
        # Etiquetas
        ax.set_xlabel("Fecha")
        ax.set_ylabel(titulo)
        ax.set_title(f"Evolución diaria - {self.pensamiento_seleccionado}")
        
        fig.tight_layout()
        
        # Crear canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=1, padx=5, pady=5)
        
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