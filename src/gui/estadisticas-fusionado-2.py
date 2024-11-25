def crear_grafico_circular(self, datos: List[Dict]):
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
