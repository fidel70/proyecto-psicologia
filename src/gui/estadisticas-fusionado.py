import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Tuple, Optional
import pandas as pd

class VentanaEstadisticas:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Estadísticas de Pensamientos")
        self.ventana.geometry("1280x800")
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value="veces")
        self.periodo_seleccionado = tk.StringVar(value="personalizado")
        self.pensamiento_seleccionado = None
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))
        
        # Cache para datos
        self._cache_datos = {}
        self._ultimo_refresco = None
        
        self.crear_widgets()
        self.cargar_pacientes()
        
    def crear_widgets(self):
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Panel superior con controles
        self.crear_panel_control()
        
        # Panel de estadísticas resumen
        self.crear_panel_resumen()
        
        # Frame para gráficos
        self.frame_graficos = ttk.Frame(self.main_frame)
        self.frame_graficos.grid(row=2, column=0, columnspan=2, sticky="nsew")
        
        # Configuración del grid
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

    def crear_panel_control(self):
        panel_control = ttk.Frame(self.main_frame)
        panel_control.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Frame superior para paciente y período
        frame_sup = ttk.Frame(panel_control)
        frame_sup.pack(fill=tk.X, pady=(0, 5))
        
        # Selector de paciente
        ttk.Label(frame_sup, text="Paciente:").pack(side=tk.LEFT, padx=5)
        self.combo_pacientes = ttk.Combobox(frame_sup, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=5)
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.actualizar_graficos)
        
        # Selector de período
        frame_periodo = ttk.LabelFrame(frame_sup, text="Período", padding=5)
        frame_periodo.pack(side=tk.LEFT, padx=20)
        
        periodos = [
            ("Hoy", "hoy"),
            ("Última semana", "semana"),
            ("Último mes", "mes"),
            ("Personalizado", "personalizado")
        ]
        
        for texto, valor in periodos:
            ttk.Radiobutton(frame_periodo, text=texto, value=valor,
                          variable=self.periodo_seleccionado,
                          command=self.actualizar_periodo).pack(side=tk.LEFT, padx=5)
        
        # Frame inferior para fechas y dimensión
        frame_inf = ttk.Frame(panel_control)
        frame_inf.pack(fill=tk.X, pady=5)
        
        # Selector de fechas
        self.frame_fechas = ttk.Frame(frame_inf)
        self.frame_fechas.pack(side=tk.LEFT)
        
        ttk.Label(self.frame_fechas, text="Desde:").pack(side=tk.LEFT, padx=5)
        self.fecha_inicio = DateEntry(self.frame_fechas, width=12, 
                                    background='darkblue', foreground='white',
                                    date_pattern='dd/mm/yyyy')
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.frame_fechas, text="Hasta:").pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(self.frame_fechas, width=12, 
                                 background='darkblue', foreground='white',
                                 date_pattern='dd/mm/yyyy')
        self.fecha_fin.pack(side=tk.LEFT, padx=5)
        
        # Selector de dimensión
        frame_dimension = ttk.LabelFrame(frame_inf, text="Dimensión", padding=5)
        frame_dimension.pack(side=tk.LEFT, padx=20)
        
        dimensiones = [
            ("Veces", "veces"),
            ("Minutos", "minutos"),
            ("Intensidad", "intensidad")
        ]
        
        for texto, valor in dimensiones:
            ttk.Radiobutton(frame_dimension, text=texto, value=valor,
                          variable=self.dimension_actual,
                          command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        
        # Botones de control
        frame_botones = ttk.Frame(frame_inf)
        frame_botones.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(frame_botones, text="Actualizar", 
                  command=self.actualizar_graficos).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Exportar", 
                  command=self.exportar_datos).pack(side=tk.LEFT, padx=5)

    def crear_panel_resumen(self):
        self.frame_resumen = ttk.LabelFrame(self.main_frame, text="Resumen", padding=10)
        self.frame_resumen.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Etiquetas para mostrar estadísticas resumen
        self.labels_resumen = {}
        estadisticas = [
            "Total registros", "Promedio diario", "Máximo diario",
            "Duración total", "Intensidad promedio", "Días registrados"
        ]
        
        for i, stat in enumerate(estadisticas):
            ttk.Label(self.frame_resumen, text=f"{stat}:").grid(
                row=i//3, column=(i%3)*2, padx=5, pady=2, sticky="e")
            lbl = ttk.Label(self.frame_resumen, text="--")
            lbl.grid(row=i//3, column=(i%3)*2+1, padx=5, pady=2, sticky="w")
            self.labels_resumen[stat] = lbl

    def actualizar_periodo(self):
        """Actualiza las fechas según el período seleccionado"""
        hoy = datetime.now()
        
        if self.periodo_seleccionado.get() == "hoy":
            self.fecha_inicio.set_date(hoy)
            self.fecha_fin.set_date(hoy)
            self.frame_fechas.pack_forget()
        elif self.periodo_seleccionado.get() == "semana":
            self.fecha_inicio.set_date(hoy - timedelta(days=7))
            self.fecha_fin.set_date(hoy)
            self.frame_fechas.pack_forget()
        elif self.periodo_seleccionado.get() == "mes":
            self.fecha_inicio.set_date(hoy - timedelta(days=30))
            self.fecha_fin.set_date(hoy)
            self.frame_fechas.pack_forget()
        else:  # personalizado
            self.frame_fechas.pack(side=tk.LEFT)
            
        self.actualizar_graficos()

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
        """Obtiene los datos de dimensiones con caché"""
        if not self.paciente_seleccionado.get():
            return {}
            
        # Verificar caché
        cache_key = (
            self.paciente_seleccionado.get(),
            self.fecha_inicio.get_date(),
            self.fecha_fin.get_date()
        )
        
        if cache_key in self._cache_datos and self._ultimo_refresco and \
           (datetime.now() - self._ultimo_refresco).seconds < 300:  # 5 minutos
            return self._cache_datos[cache_key]
            
        datos = self._obtener_datos_dimensiones_db()
        self._cache_datos[cache_key] = datos
        self._ultimo_refresco = datetime.now()
        
        return datos

    def _obtener_datos_dimensiones_db(self) -> Dict:
        """Obtiene los datos de dimensiones desde la base de datos"""
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            query = """
                SELECT 
                    p.codigo, 
                    p.pensamiento,
                    COUNT(d.id) as total_registros,
                    SUM(d.cantidad) as total_cantidad,
                    SUM(d.duracion) as total_duracion,
                    AVG(d.intensidad) as promedio_intensidad,
                    MAX(d.cantidad) as max_cantidad,
                    MAX(d.duracion) as max_duracion,
                    COUNT(DISTINCT d.fecha) as dias_registrados
                FROM pensamientos p
                LEFT JOIN dimensiones d ON d.pensamiento_id = p.id
                    AND d.fecha BETWEEN ? AND ?
                WHERE p.codigo LIKE ?
                GROUP BY p.codigo, p.pensamiento
                ORDER BY total_cantidad DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[fecha_inicio, fecha_fin, f'{codigo_paciente}%'])
            conn.close()
            
            return df.to_dict('records')
            
        except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
            messagebox.showerror("Error", f"Error al obtener datos: {str(e)}")
            return {}

    def obtener_datos_diarios(self, codigo_pensamiento: str) -> List:
        fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            query = """
                SELECT d.fecha, d.cantidad, d.duracion, d.intensidad
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo = ? 
                AND d.fecha BETWEEN ? AND ?
                ORDER BY d.fecha
            """
            
            df = pd.read_sql_query(query, conn, params=[codigo_pensamiento, fecha_inicio, fecha_fin])
            conn.close()
            return df.to_dict('records')
            
        except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
            messagebox.showerror("Error", f"Error al obtener datos diarios: {str(e)}")
            return []

    def actualizar_graficos(self, event=None):
        """Actualiza todos los elementos visuales"""
        if not self.paciente_seleccionado.get():
            return
            
        # Limpiar frame de gráficos
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
            
        datos = self.obtener_datos_dimensiones()
        if not datos:
            return
            
        # Actualizar resumen
        self.actualizar_resumen(datos)
        
        # Crear gráficos
        self.crear_grafico_circular(datos)
        if self.pensamiento_seleccionado:
            self.crear_grafico_frecuencia()

    def actualizar_resumen(self, datos: List[Dict]):
        """Actualiza el panel de resumen con los datos actuales"""
        if not datos:
            return
            
        df = pd.DataFrame(datos)
        dias_periodo = (self.fecha_fin.get_date() - self.fecha_inicio.get_date()).days + 1
        
        resumen = {
            "Total registros": df['total_registros'].sum(),
            "Promedio diario": round(df['total_cantidad'].sum() / dias_periodo, 2),
            "Máximo diario": df['max_cantidad'].max(),
            "Duración total": f"{df['total_duracion'].sum()} min",
            "Intensidad promedio": round(df['promedio_intensidad'].mean(), 2),
            "Días registrados": df['dias_registrados'].max()
        }
        
        for key, value in resumen.items():
            self.labels_resumen[key].config(text=str(value))

    def crear_grafico_circular(self, datos: List[Dict]):
        if not datos:
            return
            
        # Crear figura para el gráfico circular
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        
        # Preparar datos según la dimensión seleccionada
        df = pd.DataFrame(datos)
        dimension = self.dimension_actual.get()
        
        if dimension == "veces":
            valores = df['total_cantidad']
            etiquetas = df['codigo']
            colores = [self.colores_base[i % len(self.colores_base)] for i in range(len(df))]
        elif dimension == "minutos":
            valores = df['total_duracion']
            etiquetas = df['codigo']
            colores = [self.colores_base[i % len(self.colores_base)] for i in range(len(df))]
        else:  # intensidad
            valores = df['promedio_intensidad']
            etiquetas = df['codigo']
            colores = ['lightgreen' if v <= 3 else 'yellow' if v <= 7 else 'red' 
                      for v indef crear_grafico_circular(self, datos: List[Dict]):
        # ... (continuación del método anterior)
            valores = df['promedio_intensidad']
            etiquetas = df['codigo']
            colores = ['lightgreen' if v <= 3 else 'yellow' if v <= 7 else 'red' 
                      for v in valores]
        
        # Filtrar valores mayores que 0
        mascara = valores > 0
        valores = valores[mascara]
        etiquetas = etiquetas[mascara]
        colores = [c for i, c in enumerate(colores) if mascara.iloc[i]]
        
        if len(valores) == 0:
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
                        pensamiento = df.loc[df['codigo'] == etiquetas.iloc[i], 'pensamiento'].iloc[0]
                        self.mostrar_pensamiento(pensamiento)
                        self.pensamiento_seleccionado = etiquetas.iloc[i]
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
        
        # Preparar datos usando pandas
        df = pd.DataFrame(datos_diarios)
        dimension = self.dimension_actual.get()
        
        if dimension == "veces":
            valores = df['cantidad']
            titulo = "Cantidad de veces"
            ymax = valores.max()
        elif dimension == "minutos":
            valores = df['duracion']
            titulo = "Duración (minutos)"
            ymax = valores.max()
        else:  # intensidad
            valores = df['intensidad']
            titulo = "Intensidad"
            ymax = 10
        
        # Crear gráfico de línea
        ax.plot(df['fecha'], valores, marker='o')
        ax.set_ylim(0, ymax * 1.1)  # Añadir 10% de margen superior
        
        # Configurar ejes
        ax.set_xlabel("Fecha")
        ax.set_ylabel(titulo)
        
        # Rotar etiquetas del eje X
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # Añadir grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Ajustar layout
        fig.tight_layout()
        
        # Crear canvas para el gráfico
        canvas = FigureCanvasTkAgg(fig, master=frame_derecho)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Obtener y mostrar la descripción del pensamiento y estadísticas
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT pensamiento FROM pensamientos WHERE codigo = ?", 
                         (self.pensamiento_seleccionado,))
            pensamiento = cursor.fetchone()[0]
            conn.close()
            
            # Frame para la descripción y estadísticas
            frame_info = ttk.Frame(frame_derecho)
            frame_info.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            
            # Frame para descripción
            frame_descripcion = ttk.LabelFrame(frame_info, text="Descripción del Pensamiento")
            frame_descripcion.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            
            # Text widget para la descripción
            text_descripcion = tk.Text(frame_descripcion, wrap=tk.WORD, height=5, 
                                     padx=10, pady=10)
            text_descripcion.insert('1.0', pensamiento)
            text_descripcion.config(state='disabled')
            
            # Scrollbar para la descripción
            scrollbar = ttk.Scrollbar(frame_descripcion, command=text_descripcion.yview)
            text_descripcion.configure(yscrollcommand=scrollbar.set)
            
            # Empaquetar widgets de descripción
            text_descripcion.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Frame para estadísticas del pensamiento
            frame_stats = ttk.LabelFrame(frame_info, text="Estadísticas", padding=10)
            frame_stats.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(10, 0))
            
            # Calcular estadísticas
            stats = {
                "Total registros": len(df),
                "Promedio diario": round(valores.mean(), 2),
                "Máximo": valores.max(),
                "Mínimo": valores.min(),
                "Último registro": valores.iloc[-1] if len(valores) > 0 else 0
            }
            
            # Mostrar estadísticas
            for i, (key, value) in enumerate(stats.items()):
                ttk.Label(frame_stats, text=f"{key}:").grid(row=i, column=0, padx=5, pady=2, sticky="e")
                ttk.Label(frame_stats, text=str(value)).grid(row=i, column=1, padx=5, pady=2, sticky="w")
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener información: {str(e)}")

    def exportar_datos(self):
        """Exporta los datos a un archivo Excel"""
        if not self.paciente_seleccionado.get():
            messagebox.showwarning("Advertencia", "Seleccione un paciente primero")
            return
            
        try:
            datos = self.obtener_datos_dimensiones()
            if not datos:
                messagebox.showwarning("Advertencia", "No hay datos para exportar")
                return
            
            # Preparar datos para exportación
            df = pd.DataFrame(datos)
            
            # Solicitar ubicación para guardar
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"estadisticas_{self.paciente_seleccionado.get().split(' - ')[0]}_{datetime.now().strftime('%Y%m%d')}"
            )
            
            if filename:
                df.to_excel(filename, index=False)
                messagebox.showinfo("Éxito", f"Datos exportados a {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar datos: {str(e)}")

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

if __name__ == "__main__":
    app = VentanaEstadisticas()
    app.ventana.mainloop()
