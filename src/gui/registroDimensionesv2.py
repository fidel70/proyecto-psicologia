import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry

class VentanaDimensiones:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Registro de Dimensiones")
        self.ventana.geometry("1000x600")
        
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Variables
        self.paciente_seleccionado = tk.StringVar()
        self.pensamiento_seleccionado = None
        
        # Diccionario para almacenar las dimensiones de cada pensamiento
        self.dimensiones = {}
        
        self.crear_widgets()
        self.cargar_pacientes()

    def crear_widgets(self):
        # Panel izquierdo
        panel_izq = ttk.Frame(self.main_frame)
        panel_izq.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # Panel derecho (dimensiones)
        panel_der = ttk.LabelFrame(self.main_frame, text="Dimensiones del pensamiento", padding=10)
        panel_der.grid(row=0, column=1, sticky='nsew')
        
        # Configuración del grid
        self.main_frame.columnconfigure(1, weight=1)
        
        # === Panel Izquierdo ===
        # Selección de paciente
        ttk.Label(panel_izq, text="Paciente:").grid(row=0, column=0, pady=5, sticky='w')
        self.combo_pacientes = ttk.Combobox(panel_izq, 
                                          textvariable=self.paciente_seleccionado,
                                          state='readonly',
                                          width=40)
        self.combo_pacientes.grid(row=1, column=0, pady=5, sticky='ew')
        self.combo_pacientes.bind('<<ComboboxSelected>>', self.cargar_pensamientos)
        
        # Fecha actual
        ttk.Label(panel_izq, text="Fecha:").grid(row=2, column=0, pady=5, sticky='w')
        self.fecha_actual = DateEntry(panel_izq, width=12, 
                                    background='darkblue', foreground='white',
                                    date_pattern='dd/MM/yyyy')
        self.fecha_actual.grid(row=3, column=0, pady=5, sticky='w')
        
        # Lista de pensamientos
        ttk.Label(panel_izq, text="Pensamientos registrados:").grid(row=4, column=0, pady=5, sticky='w')
        
        # Treeview y scrollbar
        self.tree = ttk.Treeview(panel_izq, columns=('Código', 'Pensamiento'), 
                                show='headings', height=15)
        self.tree.heading('Código', text='Código')
        self.tree.heading('Pensamiento', text='Pensamiento')
        self.tree.column('Código', width=100)
        self.tree.column('Pensamiento', width=300)
        
        scrollbar = ttk.Scrollbar(panel_izq, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=5, column=0, sticky='nsew')
        scrollbar.grid(row=5, column=1, sticky='ns')
        
        # Doble click para ver pensamiento completo
        self.tree.bind('<Double-1>', self.mostrar_pensamiento_completo)
        # Click simple para mostrar/crear dimensiones
        self.tree.bind('<<TreeviewSelect>>', self.seleccionar_pensamiento)
        
        # === Panel Derecho (Dimensiones) ===
        self.panel_dimensiones = panel_der
        
        # Inicialmente mostrar mensaje
        self.lbl_sin_seleccion = ttk.Label(panel_der, 
                                          text="Seleccione un pensamiento para registrar sus dimensiones")
        self.lbl_sin_seleccion.grid(row=0, column=0, pady=20)
    def seleccionar_pensamiento(self, event=None):
        seleccion = self.tree.selection()
        if seleccion:
            item = self.tree.item(seleccion[0])
            codigo_pensamiento = item['values'][0]
            self.pensamiento_seleccionado = codigo_pensamiento
            self.mostrar_dimensiones(codigo_pensamiento)


    def mostrar_pensamiento_completo(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        pensamiento = self.tree.item(seleccion[0])['values'][1]
        ventana = tk.Toplevel(self.ventana)
        ventana.title("Detalle del Pensamiento")
        ventana.geometry("400x300")
        
        text = tk.Text(ventana, wrap=tk.WORD, padx=10, pady=10)
        text.insert('1.0', pensamiento)
        text.config(state='disabled')
        text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)



    


    
    def cargar_pensamientos(self, event=None):
        if not self.paciente_seleccionado.get():
            return
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            cursor.execute("""
                SELECT codigo, pensamiento
                FROM pensamientos
                WHERE codigo LIKE ?
                ORDER BY codigo
            """, (f'{codigo_paciente}%',))
            
            for pensamiento in cursor.fetchall():
                self.tree.insert('', 'end', values=pensamiento)
                
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar pensamientos: {str(e)}")


    

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

    def cargar_pensamientos(self, event=None):
        if not self.paciente_seleccionado.get():
            return
            
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            cursor.execute("""
                SELECT codigo, pensamiento
                FROM pensamientos
                WHERE codigo LIKE ?
                ORDER BY codigo
            """, (f'{codigo_paciente}%',))
            
            for pensamiento in cursor.fetchall():
                self.tree.insert('', 'end', values=pensamiento)
                
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar pensamientos: {str(e)}")


    #[resto de los métodos se mantienen igual]

# [Previous imports and class definition remain the same]

    def mostrar_dimensiones(self, codigo_pensamiento):
        # Limpiar panel
        for widget in self.panel_dimensiones.winfo_children():
            widget.destroy()
            
        if codigo_pensamiento not in self.dimensiones:
            self.dimensiones[codigo_pensamiento] = {
                'cantidad': tk.IntVar(value=0),
                'duracion': tk.StringVar(value=''),
                'intensidad': tk.IntVar(value=0)
            }
            
        dims = self.dimensiones[codigo_pensamiento]
        
        # Cargar dimensiones existentes
        self.cargar_dimensiones_existentes(codigo_pensamiento)
        
        # UI setup remains same but with modified validation
        frame_cantidad = ttk.Frame(self.panel_dimensiones)
        frame_cantidad.grid(row=0, column=0, pady=20, sticky='w')
        
        ttk.Label(frame_cantidad, text="Cantidad de veces:").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_cantidad, text="-", width=3,
                  command=lambda: self.disminuir_cantidad(dims['cantidad'])).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_cantidad, textvariable=dims['cantidad'], width=5).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_cantidad, text="+", width=3,
                  command=lambda: self.aumentar_cantidad(dims['cantidad'])).pack(side=tk.LEFT, padx=5)
        
        # Duración (opcional, máximo 60 minutos)
        frame_duracion = ttk.Frame(self.panel_dimensiones)
        frame_duracion.grid(row=1, column=0, pady=20, sticky='w')
        
        ttk.Label(frame_duracion, text="Duración (minutos, máx. 60):").pack(side=tk.LEFT, padx=5)
        vcmd = (self.ventana.register(self.validar_duracion), '%P')
        ttk.Entry(frame_duracion, textvariable=dims['duracion'],
                 validate='key', validatecommand=vcmd, width=10).pack(side=tk.LEFT, padx=5)
        
        # Intensidad (opcional)
        frame_intensidad = ttk.Frame(self.panel_dimensiones)
        frame_intensidad.grid(row=2, column=0, pady=20, sticky='ew')
        
        ttk.Label(frame_intensidad, text="Intensidad (0-10):").pack(side=tk.LEFT, padx=5)
        ttk.Scale(frame_intensidad, from_=0, to=10,
                 orient='horizontal', variable=dims['intensidad']).pack(side=tk.LEFT, padx=5, fill='x', expand=True)
        
        # Mostrar dimensiones registradas hoy
        self.mostrar_dimensiones_del_dia(codigo_pensamiento)
        
        # Botón guardar
        ttk.Button(self.panel_dimensiones, text="Guardar Dimensión",
                  command=lambda: self.guardar_dimension(codigo_pensamiento)).grid(row=4, column=0, pady=20)

    def validar_duracion(self, valor):
        if valor == "":  # Permite campo vacío
            return True
        try:
            num = int(valor)
            return 0 <= num <= 60  # Valida rango 0-60
        except ValueError:
            return False

    def cargar_dimensiones_existentes(self, codigo_pensamiento):
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            fecha_actual = self.fecha_actual.get_date().strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT cantidad, duracion, intensidad
                FROM dimensiones
                WHERE pensamiento_id = (SELECT id FROM pensamientos WHERE codigo = ?)
                AND fecha = ?
                ORDER BY id DESC
            """, (codigo_pensamiento, fecha_actual))
            
            dimensiones_hoy = cursor.fetchone()  # Removido .execute
            if dimensiones_hoy:
                self.dimensiones[codigo_pensamiento]['cantidad'].set(dimensiones_hoy[0])
                self.dimensiones[codigo_pensamiento]['duracion'].set(str(dimensiones_hoy[1]) if dimensiones_hoy[1] else '')
                self.dimensiones[codigo_pensamiento]['intensidad'].set(dimensiones_hoy[2])
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar dimensiones: {str(e)}")
    def mostrar_dimensiones_del_dia(self, codigo_pensamiento):
        # Crear frame para lista de dimensiones
        frame_lista = ttk.LabelFrame(self.panel_dimensiones, text="Dimensiones registradas hoy")
        frame_lista.grid(row=3, column=0, pady=10, sticky='ew')
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            fecha_actual = self.fecha_actual.get_date().strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT cantidad, duracion, intensidad
                FROM dimensiones
                WHERE pensamiento_id = (SELECT id FROM pensamientos WHERE codigo = ?)
                AND fecha = ?
                ORDER BY id DESC
            """, (codigo_pensamiento, fecha_actual))
            
            dimensiones = cursor.fetchall()
            
            if dimensiones:
                # Crear Treeview para mostrar dimensiones
                tree = ttk.Treeview(frame_lista, columns=('Cantidad', 'Duración', 'Intensidad'), 
                                  show='headings', height=3)
                tree.heading('Cantidad', text='Cantidad')
                tree.heading('Duración', text='Duración (min)')
                tree.heading('Intensidad', text='Intensidad')
                
                for dim in dimensiones:
                    tree.insert('', 'end', values=dim)
                
                tree.pack(fill='x', padx=5, pady=5)
            else:
                ttk.Label(frame_lista, text="No hay dimensiones registradas hoy").pack(pady=5)
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al mostrar dimensiones: {str(e)}")

    def guardar_dimension(self, codigo_pensamiento):
        if not codigo_pensamiento:
            messagebox.showwarning("Advertencia", "Seleccione un pensamiento")
            return
            
        dims = self.dimensiones[codigo_pensamiento]
        duracion_valor = dims['duracion'].get()
        
        # Validar duración si se ingresó
        if duracion_valor and not (0 <= int(duracion_valor) <= 60):
            messagebox.showwarning("Advertencia", "La duración debe estar entre 0 y 60 minutos")
            return
            
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO dimensiones (pensamiento_id, fecha, cantidad, duracion, intensidad)
                VALUES (
                    (SELECT id FROM pensamientos WHERE codigo = ?),
                    ?,
                    ?,
                    ?,
                    ?
                )
            """, (
                codigo_pensamiento,
                self.fecha_actual.get_date().strftime('%Y-%m-%d'),
                dims['cantidad'].get(),
                int(duracion_valor) if duracion_valor else None,
                dims['intensidad'].get()
            ))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Dimensión guardada correctamente")
            
            # Actualizar vista de dimensiones
            self.mostrar_dimensiones_del_dia(codigo_pensamiento)
            
            # Limpiar campos
            dims['cantidad'].set(0)
            dims['duracion'].set('')
            dims['intensidad'].set(0)
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")

# [Rest of the class implementation remains the same]





if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = VentanaDimensiones(root)
    root.mainloop()