def _exportar_datos(self):
    """Exporta los datos actuales a un archivo Excel."""
    if not self.paciente_seleccionado.get():
        messagebox.showwarning('Advertencia', 'Seleccione un paciente')
        return
        
    try:
        from tkinter import filedialog
        import pandas as pd
        
        # Obtener datos
        codigo_paciente = self.paciente_seleccionado.get().split(' - ')[0]
        datos = self.obtener_datos_dimensiones()
        
        if not datos:
            messagebox.showinfo('Información', 'No hay datos para exportar')
            return
            
        # Obtener datos diarios para más detalle
        datos_completos = []
        for codigo, info in datos.items():
            datos_diarios = self.obtener_datos_diarios(codigo)
            for registro in datos_diarios:
                datos_completos.append({
                    'Código': codigo,
                    'Pensamiento': info['pensamiento'],
                    'Fecha': registro[0],
                    'Cantidad': registro[1],
                    'Duración (min)': registro[2],
                    'Intensidad': registro[3],
                    'Máx. Cantidad': info['max_cantidad'],
                    'Máx. Duración': info['max_duracion']
                })
        
        # Crear DataFrame
        df = pd.DataFrame(datos_completos)
        
        # Solicitar ubicación para guardar
        filename = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')],
            initialfile=f'Registro_{codigo_paciente}_{datetime.now().strftime("%Y%m%d")}'
        )
        
        if filename:
            # Crear Excel con formato
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Datos Detallados')
            
            # Obtener el objeto workbook y la hoja
            workbook = writer.book
            worksheet = writer.sheets['Datos Detallados']
            
            # Formatos
            header_format = workbook.add_format({
                'bold': True,
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Formato para las columnas
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
            
            writer.close()
            messagebox.showinfo('Éxito', 'Datos exportados correctamente')
            
    except Exception as e:
        messagebox.showerror('Error', f'Error al exportar datos: {str(e)}')

def _generar_informe(self):
    """Genera un informe detallado en formato PDF."""
    if not self.paciente_seleccionado.get():
        messagebox.showwarning('Advertencia', 'Seleccione un paciente')
        return
        
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.units import inch
        from io import BytesIO
        import matplotlib.pyplot as plt
        
        # Solicitar ubicación para guardar
        filename = filedialog.asksaveasfilename(
            defaultextension='.pdf',
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
            initialfile=f'Informe_{self.paciente_seleccionado.get().split(" - ")[0]}_{datetime.now().strftime("%Y%m%d")}'
        )
        
        if not filename:
            return
            
        # Obtener datos
        datos = self.obtener_datos_dimensiones()
        
        # Crear documento
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Justify',
            alignment=1,
            fontSize=10
        ))
        
        # Contenido
        story = []
        
        # Título
        story.append(Paragraph(
            f'Informe de Registro de Pensamientos',
            styles['Heading1']
        ))
        story.append(Spacer(1, 12))
        
        # Información del paciente
        story.append(Paragraph(
            f'Paciente: {self.paciente_seleccionado.get()}',
            styles['Heading2']
        ))
        story.append(Paragraph(
            f'Período: {self.fecha_inicio.get_date().strftime("%d/%m/%Y")} - '
            f'{self.fecha_fin.get_date().strftime("%d/%m/%Y")}',
            styles['Normal']
        ))
        story.append(Spacer(1, 12))
        
        # Gráfico circular
        story.append(Paragraph('Distribución de Pensamientos:', styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Generar y guardar gráfico circular
        buffer = BytesIO()
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        
        dimension = self.dimension_actual.get()
        valores = []
        etiquetas = []
        
        for codigo, info in datos.items():
            if dimension == 'veces':
                valor = info['cantidad']
            elif dimension == 'minutos':
                valor = info['duracion']
            else:
                valor = info['intensidad']
            
            if valor > 0:
                valores.append(valor)
                etiquetas.append(codigo)
        
        if valores:
            ax.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=90)
            
        fig.savefig(buffer, format='png', bbox_inches='tight')
        img = Image(buffer)
        img.drawHeight = 4*inch
        img.drawWidth = 6*inch
        story.append(img)
        story.append(Spacer(1, 12))
        
        # Tabla de resumen
        story.append(Paragraph('Resumen por Pensamiento:', styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Datos de la tabla
        table_data = [['Código', 'Pensamiento', 'Cantidad', 'Duración (min)', 'Intensidad']]
        
        for codigo, info in datos.items():
            table_data.append([
                codigo,
                info['pensamiento'][:50] + '...' if len(info['pensamiento']) > 50 else info['pensamiento'],
                f"{info['cantidad']:.0f}",
                f"{info['duracion']:.0f}",
                f"{info['intensidad']:.1f}"
            ])
        
        # Crear tabla
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        
        # Generar PDF
        doc.build(story)
        messagebox.showinfo('Éxito', 'Informe generado correctamente')
        
    except Exception as e:
        messagebox.showerror('Error', f'Error al generar informe: {str(e)}')
