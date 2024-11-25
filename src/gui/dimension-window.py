class VentanaP001:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Registro de Dimensiones - Paciente P001")
        self.ventana.geometry("1280x600")
        
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Diccionario para almacenar las dimensiones de cada pensamiento
        self.dimensiones = {}
        
        self.crear_widgets()
        self.cargar_pensamientos()

    # [Los métodos anteriores permanecen sin cambios hasta mostrar_dimensiones]

    def mostrar_dimensiones(self, codigo_pensamiento):
        # Limpiar panel de dimensiones
        for widget in self.panel_dimensiones.winfo_children():
            widget.destroy()
            
        # Si no existe en el diccionario, crear nuevo registro
        if codigo_pensamiento not in self.dimensiones:
            self.dimensiones[codigo_pensamiento] = {
                'cantidad': tk.IntVar(value=0),
                'duracion': tk.StringVar(value=''),
                'intensidad': tk.IntVar(value=0)
            }
            
        dims = self.dimensiones[codigo_pensamiento]
        
        # Cantidad
        frame_cantidad = ttk.Frame(self.panel_dimensiones)
        frame_cantidad.grid(row=0, column=0, pady=20, sticky='w')
        
        ttk.Label(frame_cantidad, text="Cantidad de veces:").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_cantidad, text="-", width=3,
                  command=lambda: self.disminuir_cantidad(dims['cantidad'])).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_cantidad, textvariable=dims['cantidad'], width=5).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_cantidad, text="+", width=3,
                  command=lambda: self.aumentar_cantidad(dims['cantidad'])).pack(side=tk.LEFT, padx=5)
        
        # Duración
        frame_duracion = ttk.Frame(self.panel_dimensiones)
        frame_duracion.grid(row=1, column=0, pady=20, sticky='w')
        
        ttk.Label(frame_duracion, text="Duración (0-60 min):").pack(side=tk.LEFT, padx=5)
        vcmd = (self.ventana.register(self.validar_duracion), '%P')
        ttk.Entry(frame_duracion, textvariable=dims['duracion'],
                 validate='key', validatecommand=vcmd, width=10).pack(side=tk.LEFT, padx=5)
        
        # Intensidad
        frame_intensidad = ttk.Frame(self.panel_dimensiones)
        frame_intensidad.grid(row=2, column=0, pady=20, sticky='ew')
        
        ttk.Label(frame_intensidad, text="Intensidad (0-10):").pack(side=tk.LEFT, padx=5)
        ttk.Scale(frame_intensidad, from_=0, to=10,
                 orient='horizontal', variable=dims['intensidad']).pack(side=tk.LEFT, padx=5, fill='x', expand=True)
        
        # Lista de dimensiones del día
        frame_lista = ttk.Frame(self.panel_dimensiones)
        frame_lista.grid(row=3, column=0, pady=20, sticky='ew')
        
        ttk.Label(frame_lista, text="Dimensiones registradas hoy:").pack(side=tk.LEFT, padx=5)
        
        # Treeview actualizado para incluir columna ID oculta
        self.lista_dims = ttk.Treeview(frame_lista, 
                                     columns=('ID', 'Cantidad', 'Duración', 'Intensidad'),
                                     show='headings', height=5)
        self.lista_dims.heading('ID', text='ID')
        self.lista_dims.heading('Cantidad', text='Cantidad')
        self.lista_dims.heading('Duración', text='Duración')
        self.lista_dims.heading('Intensidad', text='Intensidad')
        
        # Ocultar columna ID
        self.lista_dims.column('ID', width=0, stretch=False)
        self.lista_dims.pack(side=tk.LEFT, padx=5, fill='x', expand=True)
        
        # Frame para totales
        frame_totales = ttk.Frame(self.panel_dimensiones)
        frame_totales.grid(row=4, column=0, pady=10, sticky='ew')
        
        ttk.Label(frame_totales, text="Total de veces:").grid(row=0, column=0, padx=5, sticky='w')
        self.lbl_total_veces = ttk.Label(frame_totales, text="0")
        self.lbl_total_veces.grid(row=0, column=1, padx=5, sticky='w')
        
        ttk.Label(frame_totales, text="Total minutos:").grid(row=1, column=0, padx=5, sticky='w')
        self.lbl_total_minutos = ttk.Label(frame_totales, text="0")
        self.lbl_total_minutos.grid(row=1, column=1, padx=5, sticky='w')
        
        # Cargar dimensiones existentes
        self.cargar_dimensiones_dia(codigo_pensamiento)
        
        # Frame para botones
        frame_botones = ttk.Frame(self.panel_dimensiones)
        frame_botones.grid(row=5, column=0, pady=20)

        # Botones de actualizar y eliminar
        ttk.Button(frame_botones, text="Actualizar",
                  command=lambda: self.guardar_dimension(codigo_pensamiento)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Eliminar Seleccionado",
                  command=lambda: self.eliminar_seleccionado(codigo_pensamiento)).pack(side=tk.LEFT, padx=5)

    def cargar_dimensiones_dia(self, codigo_pensamiento):
        fecha_actual = self.fecha_actual.get_date().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            for item in self.lista_dims.get_children():
                self.lista_dims.delete(item)
            
            cursor.execute("""
                SELECT d.id, d.cantidad, d.duracion, d.intensidad
                FROM dimensiones d
                JOIN pensamientos p ON d.pensamiento_id = p.id
                WHERE p.codigo = ? AND d.fecha = ?
                ORDER BY d.id DESC
            """, (codigo_pensamiento, fecha_actual))
            
            total_veces = 0
            total_minutos = 0
            
            for dim in cursor.fetchall():
                self.lista_dims.insert('', 'end', values=dim)
                total_veces += dim[1]
                if dim[2] is not None:
                    total_minutos += dim[2]
            
            self.lbl_total_veces.config(text=str(total_veces))
            self.lbl_total_minutos.config(text=str(total_minutos))
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar dimensiones: {str(e)}")

    def eliminar_dimension(self, codigo_pensamiento, dimension_id):
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dimensiones WHERE id = ?", (dimension_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Dimensión eliminada correctamente")
            self.cargar_dimensiones_dia(codigo_pensamiento)
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")

    def eliminar_seleccionado(self, codigo_pensamiento):
        seleccion = self.lista_dims.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una dimensión para eliminar")
            return
            
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta dimensión?"):
            item = self.lista_dims.item(seleccion[0])
            dimension_id = item['values'][0]
            self.eliminar_dimension(codigo_pensamiento, dimension_id)
