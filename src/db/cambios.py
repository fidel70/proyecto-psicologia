    def obtener_nombre_paciente(self):
        try:
            conn = sqlite3.connect('db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM pacientes WHERE codigo = 'P001'")
            nombre = cursor.fetchone()[0]
            conn.close()
            return nombre
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener nombre del paciente: {str(e)}")
            return "Desconocido"

    def crear_widgets(self):
        # Panel izquierdo
        panel_izq = ttk.Frame(self.main_frame)
        panel_izq.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # Panel derecho
        panel_der = ttk.LabelFrame(self.main_frame, text="Dimensiones", padding=10)
        panel_der.grid(row=0, column=1, sticky='nsew')
        
        # Configuración del grid
        self.main_frame.columnconfigure(1, weight=1)
        
        # === Panel Izquierdo ===
        # Información del paciente en un frame
        frame_paciente = ttk.Frame(panel_izq)
        frame_paciente.grid(row=0, column=0, columnspan=2, pady=5, sticky='ew')
        
        ttk.Label(frame_paciente, text="Código:").pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_paciente, text="P001").pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_paciente, text=" - ").pack(side=tk.LEFT)
        ttk.Label(frame_paciente, text=self.obtener_nombre_paciente()).pack(side=tk.LEFT, padx=5)

        # Rest of the widgets remain the same...