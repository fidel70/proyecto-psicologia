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
        self.ventana.geometry("1280x800")
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value="veces")
        self.pensamiento_seleccionado = None
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))
        
        self.crear_widgets()
        self.cargar_pacientes()

    # [Previous methods remain the same until crear_grafico_circular]

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
        textos_valores = []  # Para mostrar los valores reales en las etiquetas
        
        for codigo, info in datos.items():
            if dimension == "veces":
                valor = info['cantidad']
                texto_valor = f"{codigo}\n({int(valor)} veces)"  # Mostrar cantidad real
            elif dimension == "minutos":
                valor = info['duracion']
                texto_valor = f"{codigo}\n({int(valor)} min)"
            else:  # intensidad
                valor = info['intensidad']
                texto_valor = f"{codigo}\n({valor:.1f})"
                
            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
                textos_valores.append(texto_valor)
                
                if dimension == "intensidad":
                    # Color según intensidad
                    if valor <= 3:
                        colores.append('lightgreen')
                    elif valor <= 7:
                        colores.append('yellow')
                    else:
                        colores.append('red')
                else:
                    colores.append(self.colores_base[len(colores) % len(self.colores_base)])
        
        if not valores:
            return

        # Calcular porcentajes para el gráfico circular
        total = sum(valores)
        porcentajes = [(v/total)*100 for v in valores]
            
        # Crear gráfico circular con porcentajes pero mostrando valores absolutos
        wedges, texts, autotexts = ax.pie(porcentajes, labels=textos_valores, colors=colores,
                                         autopct='%1.1f%%', startangle=90)
        
        # Ajustar tamaño de fuente y posición de etiquetas
        plt.setp(autotexts, size=8)
        plt.setp(texts, size=8)
        
        # Añadir título según dimensión
        if dimension == "veces":
            ax.set_title(f"Total de veces: {int(total)}")
        elif dimension == "minutos":
            ax.set_title(f"Total de minutos: {int(total)}")
        else:
            ax.set_title("Intensidad promedio por pensamiento")
        
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
            
        # Frame para el gráfico y descripción
        frame_derecho = ttk.Frame(self.frame_graficos)
        frame_derecho.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Crear figura para el gráfico de frecuencia
        fig = Figure(figsize=(6, 3))
        ax = fig.add_subplot(111)
        
        # Preparar datos
        fechas = [row[0] for row in datos_diarios]
        dimension = self.dimension_actual.get()
        
        if dimension == "veces":
            valores = [row[1] if row[1] is not None else 0 for row in datos_diarios]
            titulo = f"Cantidad de veces por día"
            ymax = max(valores) + 1  # Añadir espacio en la parte superior
        elif dimension == "minutos":
            valores = [row[2] if row[2] is not None else 0 for row in datos_diarios]
            titulo = "Duración (minutos) por día"
            ymax = max(valores) + 5
        else:  # intensidad
            valores = [row[3] if row[3] is not None else 0 for row in datos_diarios]
            titulo = "Intensidad por día"
            ymax = 10

        # Formatear fechas para el eje X
        fechas_fmt = [datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y') for fecha in fechas]
        
        # Crear gráfico de línea
        ax.plot(fechas_fmt, valores, marker='o', linestyle='-', linewidth=2, markersize=8)
        
        # Configurar ejes
        ax.set_ylim(0, ymax)
        ax.set_xlabel("Fecha")
        ax.set_ylabel(titulo)
        
        # Añadir valores encima de cada punto
        for i, valor in enumerate(valores):
            if dimension == "intensidad":
                ax.annotate(f'{valor:.1f}', (fechas_fmt[i], valores[i]),
                          textcoords="offset points", xytext=(0,10), ha='center')
            else:
                ax.annotate(f'{int(valor)}', (fechas_fmt[i], valores[i]),
                          textcoords="offset points", xytext=(0,10), ha='center')
        
        # Rotar etiquetas del eje X
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # Ajustar layout
        fig.tight_layout()
        
        # Crear canvas para el gráfico
        canvas = FigureCanvasTkAgg(fig, master=frame_derecho)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # [Rest of the method remains the same]
