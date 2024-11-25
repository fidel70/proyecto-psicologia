# Agregar método para eliminar dimensión:
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

# Modificar el método mostrar_dimensiones para incluir el botón eliminar y obtener el ID:
def mostrar_dimensiones(self, codigo_pensamiento):
    # ... código existente hasta la creación de lista_dims ...

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

    # Frame para botones
    frame_botones = ttk.Frame(self.panel_dimensiones)
    frame_botones.grid(row=5, column=0, pady=20)

    # Botón actualizar
    ttk.Button(frame_botones, text="Actualizar",
              command=lambda: self.guardar_dimension(codigo_pensamiento)).pack(side=tk.LEFT, padx=5)

    # Botón eliminar
    ttk.Button(frame_botones, text="Eliminar Seleccionado",
              command=lambda: self.eliminar_seleccionado(codigo_pensamiento)).pack(side=tk.LEFT, padx=5)

# Agregar método para manejar la eliminación del registro seleccionado:
def eliminar_seleccionado(self, codigo_pensamiento):
    seleccion = self.lista_dims.selection()
    if not seleccion:
        messagebox.showwarning("Advertencia", "Seleccione una dimensión para eliminar")
        return
        
    if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta dimensión?"):
        item = self.lista_dims.item(seleccion[0])
        dimension_id = item['values'][0]
        self.eliminar_dimension(codigo_pensamiento, dimension_id)

# Modificar el método cargar_dimensiones_dia para incluir el ID:
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
