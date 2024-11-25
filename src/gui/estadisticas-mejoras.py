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

    def obtener_datos_paciente(self, codigo_paciente: str, fecha_inicio: str, fecha_fin: str) -> Dict[str, List[DatosPensamiento]]:
        with self.conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.codigo, p.pensamiento, d.cantidad, d.duracion, d.intensidad, d.fecha
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo LIKE ? AND d.fecha BETWEEN ? AND ?
                ORDER BY d.fecha
            """, (f'{codigo_paciente}%', fecha_inicio, fecha_fin))
            
            datos = {}
            for row in cursor.fetchall():
                codigo = row[0]
                if codigo not in datos:
                    datos[codigo] = []
                datos[codigo].append(DatosPensamiento(
                    pensamiento=row[1],
                    cantidad=row[2] or 0,
                    duracion=row[3] or 0,
                    intensidad=row[4] or 0,
                    fecha=row[5]
                ))
            return datos

class GestorGraficos:
    def __init__(self):
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))
        
    def crear_grafico_circular(self, datos: Dict[str, List[DatosPensamiento]], dimension: str) -> Figure:
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
                color = self._obtener_color(dimension, valor/len(registros))
                colores.append(color)

        if valores:
            wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, colors=colores,
                                            autopct='%1.1f%%', startangle=90)
            plt.setp(autotexts, size=8)
            plt.setp(texts, size=8)
            ax.legend(wedges, etiquetas, title="Pensamientos",
                     loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

        return fig

    def _obtener_color(self, dimension: str, valor: float) -> str:
        if dimension == 'intensidad':
            if valor <= 3: return 'lightgreen'
            if valor <= 7: return 'yellow'
            return 'red'
        return self.colores_base[hash(str(valor)) % len(self.colores_base)]

class VentanaEstadisticas:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Estadísticas de Pensamientos")
        self.ventana.geometry("1280x800")
        
        self.db = GestorDB('../../data/db_psicologia_clinic.db')
        self.gestor_graficos = GestorGraficos()
        
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value="cantidad")
        self.pensamiento_seleccionado = None
        
        self._crear_interfaz()
        self._cargar_pacientes()
    
    def _crear_interfaz(self):
        # Frame principal con mejor manejo del espacio
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel superior con controles
        self._crear_panel_control()
        
        # Panel de gráficos con scrollable
        self._crear_panel_graficos()
    
    def _crear_panel_control(self):
        panel = ttk.LabelFrame(self.main_frame, text="Controles", padding="5")
        panel.pack(fill=tk.X, padx=5, pady=5)
        
        # Selector de paciente mejorado
        frame_paciente = ttk.Frame(panel)
        frame_paciente.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame_paciente, text="Paciente:").pack(side=tk.LEFT)
        self.combo_pacientes = ttk.Combobox(frame_paciente, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=(5, 20))
        
        # Fechas con validación
        frame_fechas = ttk.Frame(panel)
        frame_fechas.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame_fechas, text="Periodo:").pack(side=tk.LEFT)
        self.fecha_inicio = DateEntry(frame_fechas, width=12, 
                                    background='darkblue',
                                    date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_fechas, text="hasta").pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(frame_fechas, width=12,
                                 background='darkblue',
                                 date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        
        # Botones de control
        frame_botones = ttk.Frame(panel)
        frame_botones.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(frame_botones, text="Actualizar",
                  command=self._actualizar_graficos).pack(side=tk.LEFT)
        ttk.Button(frame_botones, text="Exportar",
                  command=self._exportar_datos).pack(side=tk.LEFT, padx=5)
    
    def _crear_panel_graficos(self):
        # Canvas scrollable para gráficos
        self.canvas_graficos = tk.Canvas(self.main_frame)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical",
                                command=self.canvas_graficos.yview)
        self.frame_graficos = ttk.Frame(self.canvas_graficos)
        
        self.canvas_graficos.configure(yscrollcommand=scrollbar.set)
        
        # Pack todos los elementos
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_graficos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_graficos.create_window((0, 0), window=self.frame_graficos, anchor="nw")
        
        # Configurar scroll
        self.frame_graficos.bind("<Configure>", 
            lambda e: self.canvas_graficos.configure(scrollregion=self.canvas_graficos.bbox("all")))
    
    def _actualizar_graficos(self):
        if not self._validar_fechas():
            return
        
        try:
            datos = self.db.obtener_datos_paciente(
                self.paciente_seleccionado.get().split(' - ')[0],
                self.fecha_inicio.get_date().strftime('%Y-%m-%d'),
                self.fecha_fin.get_date().strftime('%Y-%m-%d')
            )
            
            self._mostrar_graficos(datos)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar gráficos: {str(e)}")
    
    def _validar_fechas(self) -> bool:
        if self.fecha_inicio.get_date() > self.fecha_fin.get_date():
            messagebox.showerror("Error", "La fecha inicial no puede ser posterior a la fecha final")
            return False
        return True
    
    def _exportar_datos(self):
        # Implementar exportación a Excel/CSV
        pass

if __name__ == "__main__":
    app = VentanaEstadisticas()
    app.ventana.mainloop()
