import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from contextlib import contextmanager
import pandas as pd
from abc import ABC, abstractmethod


@dataclass
class DatosPensamiento:
    """Estructura de datos para almacenar información de pensamientos."""
    pensamiento: str
    cantidad: float
    duracion: float
    intensidad: float
    fecha: str
    codigo: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pensamiento': self.pensamiento,
            'cantidad': self.cantidad,
            'duracion': self.duracion,
            'intensidad': self.intensidad,
            'fecha': self.fecha,
            'codigo': self.codigo
        }


class BaseDatos:
    """Clase para manejar todas las operaciones de base de datos."""
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

    def obtener_pacientes(self) -> List[Tuple[str, str]]:
        """Obtiene la lista de pacientes."""
        try:
            with self.conexion() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT codigo, nombre FROM pacientes ORDER BY codigo')
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Error al obtener pacientes: {str(e)}")

    def obtener_datos_paciente(self, codigo_paciente: str, fecha_inicio: str, 
                             fecha_fin: str) -> Dict[str, List[DatosPensamiento]]:
        """Obtiene los datos de un paciente en un rango de fechas."""
        try:
            with self.conexion() as conn:
                cursor = conn.cursor()
                query = """
                SELECT p.codigo, p.pensamiento, d.cantidad, d.duracion, 
                       d.intensidad, d.fecha
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo LIKE ? AND d.fecha BETWEEN ? AND ?
                ORDER BY d.fecha
                """
                cursor.execute(query, (f'{codigo_paciente}%', fecha_inicio, fecha_fin))
                
                datos: Dict[str, List[DatosPensamiento]] = {}
                for row in cursor.fetchall():
                    codigo = row[0]
                    if codigo not in datos:
                        datos[codigo] = []
                    datos[codigo].append(DatosPensamiento(
                        pensamiento=row[1],
                        cantidad=row[2] or 0,
                        duracion=row[3] or 0,
                        intensidad=row[4] or 0,
                        fecha=row[5],
                        codigo=codigo
                    ))
                return datos
        except sqlite3.Error as e:
            raise Exception(f"Error al obtener datos del paciente: {str(e)}")

    def obtener_descripcion_pensamiento(self, codigo: str) -> str:
        """Obtiene la descripción de un pensamiento específico."""
        try:
            with self.conexion() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT pensamiento FROM pensamientos WHERE codigo = ?', 
                             (codigo,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else ""
        except sqlite3.Error as e:
            raise Exception(f"Error al obtener descripción: {str(e)}")


class GraficoBase(ABC):
    """Clase base abstracta para gráficos."""
    def __init__(self):
        self.colores_base = plt.cm.Set3(np.linspace(0, 1, 12))

    @abstractmethod
    def crear(self, datos: Dict[str, List[DatosPensamiento]], 
             dimension: str) -> Figure:
        pass

    def _obtener_color_por_intensidad(self, valor: float) -> str:
        if valor <= 3:
            return 'lightgreen'
        elif valor <= 7:
            return 'yellow'
        return 'red'


class GraficoCircular(GraficoBase):
    """Implementación de gráfico circular."""
    def crear(self, datos: Dict[str, List[DatosPensamiento]], 
             dimension: str) -> Figure:
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)

        valores = []
        etiquetas = []
        colores = []

        for codigo, registros in datos.items():
            if dimension == 'intensidad':
                valor = sum(d.intensidad for d in registros) / len(registros)
                color = self._obtener_color_por_intensidad(valor)
            else:
                valor = sum(getattr(d, dimension) for d in registros)
                color = self.colores_base[len(colores) % len(self.colores_base)]

            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
                colores.append(color)

        if valores:
            wedges, texts, autotexts = ax.pie(valores, labels=etiquetas, 
                                            colors=colores, autopct='%1.1f%%', 
                                            startangle=90)
            plt.setp(autotexts, size=8)
            plt.setp(texts, size=8)
            ax.legend(wedges, etiquetas, title='Pensamientos', 
                     loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))

        return fig


class GraficoLineal(GraficoBase):
    """Implementación de gráfico lineal."""
    def crear(self, datos: List[DatosPensamiento], dimension: str) -> Figure:
        fig = Figure(figsize=(6, 3))
        ax = fig.add_subplot(111)

        df = pd.DataFrame([d.to_dict() for d in datos])
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.set_index('fecha')

        valores = df[dimension]
        ax.plot(df.index, valores, marker='o')
        
        ymax = 10 if dimension == 'intensidad' else valores.max()
        ax.set_ylim(0, ymax * 1.1)  # 10% de margen superior
        
        titulo = {
            'cantidad': 'Cantidad de veces',
            'duracion': 'Duración (minutos)',
            'intensidad': 'Intensidad'
        }
        
        ax.set_xlabel('Fecha')
        ax.set_ylabel(titulo[dimension])
        plt.setp(ax.get_xticklabels(), rotation=45)
        fig.tight_layout()

        return fig


class EstadisticasUI:
    """Clase principal de la interfaz de usuario."""
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title('Estadísticas de Pensamientos')
        self.ventana.geometry('1280x800')
        
        # Variables de control
        self.paciente_seleccionado = tk.StringVar()
        self.dimension_actual = tk.StringVar(value='cantidad')
        self.pensamiento_seleccionado = None
        
        # Componentes
        self.db = BaseDatos('../../data/db_psicologia_clinic.db')
        self.grafico_circular = GraficoCircular()
        self.grafico_lineal = GraficoLineal()
        
        self._crear_interfaz()
        self._cargar_pacientes()

    def _crear_interfaz(self):
        """Crea la interfaz principal."""
        self.main_frame = ttk.Frame(self.ventana, padding='10')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._crear_panel_control()
        self._crear_panel_graficos()

    def _crear_panel_control(self):
        """Crea el panel de control superior."""
        panel = ttk.LabelFrame(self.main_frame, text='Controles', padding='5')
        panel.pack(fill=tk.X, padx=5, pady=5)

        # Frame para selección de paciente
        frame_paciente = ttk.Frame(panel)
        frame_paciente.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(frame_paciente, text='Paciente:').pack(side=tk.LEFT)
        self.combo_pacientes = ttk.Combobox(frame_paciente, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly', width=40)
        self.combo_pacientes.pack(side=tk.LEFT, padx=(5, 20))
        self.combo_pacientes.bind('<<ComboboxSelected>>', self._actualizar_graficos)

        # Frame para fechas
        frame_fechas = ttk.Frame(panel)
        frame_fechas.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(frame_fechas, text='Periodo:').pack(side=tk.LEFT)
        
        # Por defecto, último mes
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
        
        self.fecha_inicio = DateEntry(frame_fechas, width=12, background='darkblue',
                                    date_pattern='dd/mm/yyyy')
        self.fecha_inicio.set_date(fecha_inicio)
        self.fecha_inicio.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_fechas, text='hasta').pack(side=tk.LEFT, padx=5)
        self.fecha_fin = DateEntry(frame_fechas, width=12, background='darkblue',
                                 date_pattern='dd/mm/yyyy')
        self.fecha_fin.set_date(fecha_fin)
        self.fecha_fin.pack(side=tk.LEFT, padx=5)

        # Frame para dimensiones
        frame_dimension = ttk.Frame(panel)
        frame_dimension.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(frame_dimension, text='Dimensión:').pack(side=tk.LEFT)
        for dimension in [('cantidad', 'Veces'), 
                        ('duracion', 'Minutos'), 
                        ('intensidad', 'Intensidad')]:
            ttk.Radiobutton(frame_dimension, text=dimension[1],
                          variable=self.dimension_actual, 
                          value=dimension[0],
                          command=self._actualizar_graficos
                          ).pack(side=tk.LEFT, padx=5)

        # Frame para botones
        frame_botones = ttk.Frame(panel)
        frame_botones.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(frame_botones, text='Actualizar', 
                  command=self._actualizar_graficos).pack(side=tk.LEFT)
        ttk.Button(frame_botones, text='Exportar', 
                  command=self._exportar_datos).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text='Generar Informe', 
                  command=self._generar_informe).pack(side=tk.LEFT, padx=5)

    def _crear_panel_graficos(self):
        """Crea el panel para los gráficos."""
        self.frame_graficos = ttk.Frame(self.main_frame)
        self.frame_graficos.pack(fill=tk.BOTH, expand=True, pady=5)

    def _cargar_pacientes(self):
        """Carga la lista de pacientes en el combobox."""
        try:
            pacientes = self.db.obtener_pacientes()
            self.combo_pacientes['values'] = [f'{p[0]} - {p[1]}' for p in pacientes]
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _actualizar_graficos(self, event=None):
        """Actualiza todos los gráficos."""
        if not self._validar_seleccion():
            return

        try:
            # Limpiar gráficos anteriores
            for widget in self.frame_graficos.winfo_children():
                widget.destroy()

            # Obtener datos
            codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
            fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
            fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
            
            datos = self.db.obtener_datos_paciente(codigo_paciente, 
                                                 fecha_inicio, fecha_fin)
            
            if not datos:
                messagebox.showinfo('Información', 
                                  'No hay datos para el período seleccionado')
                return

            # Crear gráficos
            self._crear_grafico_circular(datos)
            if self.pensamiento_seleccionado:
                self._crear_grafico_lineal(datos)

        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _validar_seleccion(self) -> bool:
        """Valida la selección actual."""
        if not self.paciente_seleccionado.get():
            messagebox.showwarning('Advertencia', 'Seleccione un paciente')
            return False
            
        if self.fecha_inicio.get_date() > self.fecha_fin.get_date():
            messagebox.showerror('Error', 
                               'La fecha inicial no puede ser posterior a la final')
            return False
            
        return True

    def _crear_grafico_circular(self, datos: Dict[str, List[DatosPensamiento]]):
        """Crea y muestra el gráfico circular."""
        fig = self.grafico_circular.crear(datos, self.dimension_actual.get())
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        def on_click(event):
            if event.inaxes == fig.axes[0]:
                self._manejar_click_grafico(event, fig.axes[0], datos)
                
        canvas.mpl_connect('button_press_event', on_click)

    def _crear_grafico_lineal(self, datos: Dict[str, List[DatosPensamiento]]):
        """Crea y muestra el gráfico lineal."""
        if self.pensamiento_seleccionado not in datos:
            return
#########
#####
        registros = datos[self.pensamiento_seleccionado]
        frame_derecho = ttk.Frame(self.frame_graficos)
        frame_derecho.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        # Crear gráfico lineal
        fig = self.grafico_lineal.crear(registros, self.dimension_actual.get())
        canvas = FigureCanvasTkAgg(fig, master=frame_derecho)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Mostrar descripción del pensamiento
        self._mostrar_descripcion_pensamiento(frame_derecho)

    def _manejar_click_grafico(self, event, ax, datos: Dict[str, List[DatosPensamiento]]):
        """Maneja el evento de click en el gráfico circular."""
        for wedge in ax.patches:  # patches contiene los wedges del pie chart
            if wedge.contains_point([event.x, event.y]):
                codigo = wedge.get_label()
                self.pensamiento_seleccionado = codigo
                self._mostrar_detalle_pensamiento(datos[codigo][0].pensamiento)
                self._crear_grafico_lineal(datos)
                break

    def _mostrar_descripcion_pensamiento(self, frame_padre: ttk.Frame):
        """Muestra la descripción del pensamiento seleccionado."""
        try:
            descripcion = self.db.obtener_descripcion_pensamiento(
                self.pensamiento_seleccionado)
            
            frame_descripcion = ttk.LabelFrame(frame_padre, 
                                             text='Descripción del Pensamiento')
            frame_descripcion.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            
            text_descripcion = tk.Text(frame_descripcion, wrap=tk.WORD, 
                                     height=5, padx=10, pady=10)
            text_descripcion.insert('1.0', descripcion)
            text_descripcion.config(state='disabled')
            
            scrollbar = ttk.Scrollbar(frame_descripcion, 
                                    command=text_descripcion.yview)
            text_descripcion.configure(yscrollcommand=scrollbar.set)
            
            text_descripcion.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _mostrar_detalle_pensamiento(self, pensamiento: str):
        """Muestra una ventana con el detalle completo del pensamiento."""
        ventana = tk.Toplevel(self.ventana)
        ventana.title('Detalle del Pensamiento')
        ventana.geometry('500x400')
        
        # Hacer la ventana modal
        ventana.transient(self.ventana)
        ventana.grab_set()
        
        # Contenido
        frame = ttk.Frame(ventana, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Texto con scroll
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text = tk.Text(text_frame, wrap=tk.WORD, padx=10, pady=10)
        text.insert('1.0', pensamiento)
        text.config(state='disabled')
        
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botón cerrar
        ttk.Button(frame, text='Cerrar', 
                  command=ventana.destroy).pack(pady=10)
        
        # Centrar la ventana
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    def _exportar_datos(self):
        """Exporta los datos actuales a un archivo Excel."""
        if not self._validar_seleccion():
            return
            
        try:
            codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
            fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
            fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
            
            datos = self.db.obtener_datos_paciente(codigo_paciente, 
                                                 fecha_inicio, fecha_fin)
            
            if not datos:
                messagebox.showinfo('Información', 
                                  'No hay datos para exportar')
                return
                
            # Convertir datos a DataFrame
            filas = []
            for codigo, registros in datos.items():
                for registro in registros:
                    filas.append({
                        'Código': codigo,
                        'Pensamiento': registro.pensamiento,
                        'Fecha': registro.fecha,
                        'Cantidad': registro.cantidad,
                        'Duración (min)': registro.duracion,
                        'Intensidad': registro.intensidad
                    })
            
            df = pd.DataFrame(filas)
            
            # Solicitar ubicación para guardar
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')],
                title='Guardar Exportación'
            )
            
            if filename:
                df.to_excel(filename, index=False)
                messagebox.showinfo('Éxito', 
                                  'Datos exportados correctamente')
                
        except Exception as e:
            messagebox.showerror('Error', 
                               f'Error al exportar datos: {str(e)}')

    def _generar_informe(self):
        """Genera un informe detallado en formato PDF."""
        if not self._validar_seleccion():
            return
            
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            
            # Solicitar ubicación para guardar
            filename = filedialog.asksaveasfilename(
                defaultextension='.pdf',
                filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
                title='Guardar Informe'
            )
            
            if not filename:
                return
                
            # Obtener datos
            codigo_paciente = self.paciente_seleccionado.get()
            fecha_inicio = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
            fecha_fin = self.fecha_fin.get_date().strftime('%Y-%m-%d')
            
            datos = self.db.obtener_datos_paciente(
                codigo_paciente.split(' - ')[0], 
                fecha_inicio, 
                fecha_fin
            )
            
            # Crear documento
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            story.append(Paragraph(f'Informe de Pensamientos: {codigo_paciente}', 
                                 styles['Heading1']))
            story.append(Spacer(1, 12))
            
            # Período
            story.append(Paragraph(f'Período: {fecha_inicio} a {fecha_fin}', 
                                 styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Resumen por pensamiento
            story.append(Paragraph('Resumen por Pensamiento:', 
                                 styles['Heading2']))
            story.append(Spacer(1, 12))
            
            for codigo, registros in datos.items():
                # Estadísticas del pensamiento
                total_cantidad = sum(r.cantidad for r in registros)
                total_duracion = sum(r.duracion for r in registros)
                promedio_intensidad = sum(r.intensidad for r in registros) / len(registros)
                
                story.append(Paragraph(f'Pensamiento: {codigo}', 
                                     styles['Heading3']))
                story.append(Paragraph(f'Descripción: {registros[0].pensamiento}', 
                                     styles['Normal']))
                story.append(Paragraph(
                    f'Total ocurrencias: {total_cantidad}<br/>'
                    f'Total duración: {total_duracion} minutos<br/>'
                    f'Intensidad promedio: {promedio_intensidad:.2f}',
                    styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Generar PDF
            doc.build(story)
            messagebox.showinfo('Éxito', 'Informe generado correctamente')
            
        except Exception as e:
            messagebox.showerror('Error', 
                               f'Error al generar informe: {str(e)}')

    def ejecutar(self):
        """Inicia la aplicación."""
        self.ventana.mainloop()


if __name__ == '__main__':
    app = EstadisticasUI()
    app.ejecutar()

