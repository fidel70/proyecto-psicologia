import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
from dataclasses import dataclass

@dataclass
class DatosPensamiento:
    codigo: str
    pensamiento: str
    cantidad: int
    duracion: int
    intensidad: float
    max_cantidad: int
    max_duracion: int

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
        
        # Constantes
        self.DB_PATH = '../../data/db_psicologia_clinic.db'
        self.DIMENSIONES = ["veces", "minutos", "intensidad"]
        
        # Configuración de estilos
        self.configurar_estilos()
        
        self.crear_widgets()
        self.cargar_pacientes()

    def configurar_estilos(self):
        style = ttk.Style()
        style.configure('Stats.TFrame', padding=10)
        style.configure('Stats.TLabelframe', padding=10)
        style.configure('Stats.TButton', padding=5)
        
    def crear_widgets(self):
        self.main_frame = ttk.Frame(self.ventana, padding="10", style='Stats.TFrame')
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.crear_panel_control()
        self.crear_panel_graficos()
        self.configurar_grid()
        
    def crear_panel_control(self):
        panel_control = ttk.Frame(self.main_frame)
        panel_control.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Selector de paciente
        self.crear_selector_paciente(panel_control)
        
        # Selector de fechas
        self.crear_selector_fechas(panel_control)
        
        # Botón de exportar
        ttk.Button(panel_control, text="Exportar Datos", 
                  command=self.exportar_datos,
                  style='Stats.TButton').pack(side=tk.LEFT, padx=20)
        
        # Selector de dimensión
        self.crear_selector_dimension(panel_control)
        
    def crear_selector_paciente(self, parent):
        frame_paciente = ttk.Frame(parent)
        frame_paciente.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_paciente, text="Paciente:").pack(side=tk.LEFT)
        self.combo_pacientes = ttk.Combobox(frame_paciente, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.actualizar_graficos)
        
    def crear_selector_fechas(self, parent):
        frame_fechas = ttk.Frame(parent)
        frame_fechas.pack(side=tk.LEFT, padx=5)
        
        # Fecha inicio
        ttk.Label(frame_fechas, text="Desde:").pack(side=tk.LEFT)
        self.fecha_inicio = DateEntry(frame_fechas, width=12, 
                                    background='darkblue', foreground='white',
                                    date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        
        # Fecha fin
        ttk.Label(frame_fechas, text="Hasta:").pack(side=tk.LEFT)
        self.fecha_fin = DateEntry(frame_fechas, width=12, 
                                 background='darkblue', foreground='white',
                                 date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        
        # Botones de período rápido
        self.crear_botones_periodo(frame_fechas)
        
    def crear_botones_periodo(self, parent):
        frame_botones = ttk.Frame(parent)
        frame_botones.pack(side=tk.LEFT, padx=5)
        
        periodos = {
            "Última semana": 7,
            "Último mes": 30,
            "Último trimestre": 90
        }
        
        for texto, dias in periodos.items():
            ttk.Button(frame_botones, text=texto,
                      command=lambda d=dias: self.establecer_periodo(d),
                      style='Stats.TButton').pack(side=tk.LEFT, padx=2)

    def establecer_periodo(self, dias: int):
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=dias)
        self.fecha_fin.set_date(fecha_fin)
        self.fecha_inicio.set_date(fecha_inicio)
        self.actualizar_graficos()
        
    def crear_selector_dimension(self, parent):
        frame_dimension = ttk.LabelFrame(parent, text="Dimensión",
                                       padding=5, style='Stats.TLabelframe')
        frame_dimension.pack(side=tk.LEFT, padx=20)
        
        for dimension in self.DIMENSIONES:
            ttk.Radiobutton(frame_dimension, text=dimension.capitalize(),
                          variable=self.dimension_actual, value=dimension,
                          command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
    
    def exportar_datos(self):
        if not self.paciente_seleccionado.get():
            messagebox.showwarning("Advertencia", "Seleccione un paciente")
            return
            
        try:
            import pandas as pd
            datos = self.obtener_datos_dimensiones()
            
            if not datos:
                messagebox.showwarning("Advertencia", "No hay datos para exportar")
                return
                
            # Convertir datos a DataFrame
            df_data = []
            for codigo, info in datos.items():
                df_data.append({
                    'Código': codigo,
                    'Pensamiento': info['pensamiento'],
                    'Cantidad Total': info['cantidad'],
                    'Duración Total (min)': info['duracion'],
                    'Intensidad Promedio': round(info['intensidad'], 2),
                    'Cantidad Máxima': info['max_cantidad'],
                    'Duración Máxima': info['max_duracion']
                })
            
            df = pd.DataFrame(df_data)
            
            # Guardar archivo
            paciente = self.paciente_seleccionado.get().split(' - ')[0]
            fecha_inicio = self.fecha_inicio.get_date().strftime('%Y%m%d')
            fecha_fin = self.fecha_fin.get_date().strftime('%Y%m%d')
            filename = f"estadisticas_{paciente}_{fecha_inicio}_{fecha_fin}.xlsx"
            
            df.to_excel(filename, index=False)
            messagebox.showinfo("Éxito", f"Datos exportados a {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar datos: {str(e)}")

    def actualizar_graficos(self, event=None):
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
            
        if not self.paciente_seleccionado.get():
            return
            
        datos = self.obtener_datos_dimensiones()
        if not datos:
            self.mostrar_mensaje_sin_datos()
            return
            
        self.crear_grafico_circular(datos)
        self.mostrar_estadisticas_generales(datos)
        
        if self.pensamiento_seleccionado:
            self.crear_grafico_frecuencia()

    def mostrar_mensaje_sin_datos(self):
        ttk.Label(self.frame_graficos, 
                 text="No hay datos para mostrar en el período seleccionado",
                 style='Stats.TLabel').grid(row=0, column=0, pady=20)

    def mostrar_estadisticas_generales(self, datos: Dict):
        frame_stats = ttk.LabelFrame(self.frame_graficos, text="Estadísticas Generales",
                                   style='Stats.TLabelframe')
        frame_stats.grid(row=1, column=0, sticky='ew', pady=10)
        
        total_pensamientos = len(datos)
        total_veces = sum(info['cantidad'] for info in datos.values())
        total_minutos = sum(info['duracion'] for info in datos.values())
        promedio_intensidad = np.mean([info['intensidad'] for info in datos.values()])
        
        estadisticas = [
            f"Total de pensamientos diferentes: {total_pensamientos}",
            f"Total de veces registradas: {total_veces}",
            f"Total de minutos: {total_minutos}",
            f"Intensidad promedio: {promedio_intensidad:.2f}"
        ]
        
        for i, texto in enumerate(estadisticas):
            ttk.Label(frame_stats, text=texto).grid(row=i, column=0, sticky='w', padx=5)

    # [Resto de métodos actualizados con mejor manejo de errores y validaciones]
