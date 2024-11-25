import pandas as pd
import os
from tkinter import filedialog, messagebox
import tkinter as tk
from typing import Optional, List, Dict
import logging

class ExcelToTxtExporter:
    def __init__(self):
        """Inicializa el exportador con configuración básica de logging."""
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('excel_export.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def seleccionar_archivo(self, titulo: str, tipos: tuple) -> Optional[str]:
        """
        Abre un diálogo para seleccionar un archivo.
        
        Args:
            titulo: Título de la ventana de diálogo
            tipos: Tupla con los tipos de archivo permitidos
            
        Returns:
            str: Ruta del archivo seleccionado o None si se canceló
        """
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        archivo = filedialog.askopenfilename(
            title=titulo,
            filetypes=tipos
        )
        return archivo if archivo else None

    def seleccionar_destino(self) -> Optional[str]:
        """
        Abre un diálogo para seleccionar la ubicación del archivo de destino.
        
        Returns:
            str: Ruta del archivo de destino o None si se canceló
        """
        root = tk.Tk()
        root.withdraw()
        destino = filedialog.asksaveasfilename(
            title="Guardar archivo TXT",
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")]
        )
        return destino if destino else None

    def exportar_excel_a_txt(self, 
                           archivo_excel: str, 
                           archivo_destino: str,
                           columnas: Optional[List[str]] = None,
                           separador: str = "|",
                           incluir_encabezados: bool = True,
                           formato_personalizado: Optional[Dict[str, str]] = None) -> bool:
        """
        Exporta datos de un archivo Excel a un archivo TXT.
        
        Args:
            archivo_excel: Ruta del archivo Excel
            archivo_destino: Ruta del archivo TXT de destino
            columnas: Lista de columnas a exportar (None para todas)
            separador: Carácter separador para el archivo TXT
            incluir_encabezados: Si se debe incluir la fila de encabezados
            formato_personalizado: Diccionario con formatos personalizados para columnas
            
        Returns:
            bool: True si la exportación fue exitosa, False en caso contrario
        """
        try:
            # Leer archivo Excel
            self.logger.info(f"Leyendo archivo Excel: {archivo_excel}")
            df = pd.read_excel(archivo_excel)
            
            # Seleccionar columnas si se especificaron
            if columnas:
                df = df[columnas]
            
            # Aplicar formatos personalizados si existen
            if formato_personalizado:
                for columna, formato in formato_personalizado.items():
                    if columna in df.columns:
                        df[columna] = df[columna].apply(lambda x: format(x, formato))
            
            # Crear archivo TXT
            self.logger.info(f"Creando archivo TXT: {archivo_destino}")
            with open(archivo_destino, 'w', encoding='utf-8') as f:
                # Escribir encabezados si se requiere
                if incluir_encabezados:
                    f.write(separador.join(df.columns) + '\n')
                
                # Escribir datos
                for _, row in df.iterrows():
                    linea = separador.join(str(valor) for valor in row)
                    f.write(linea + '\n')
            
            self.logger.info("Exportación completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la exportación: {str(e)}")
            messagebox.showerror("Error", f"Error durante la exportación: {str(e)}")
            return False

def main():
    """Función principal que ejecuta el proceso de exportación."""
    exportador = ExcelToTxtExporter()
    
    # Seleccionar archivo Excel
    archivo_excel = exportador.seleccionar_archivo(
        "Seleccionar archivo Excel",
        [("Archivos Excel", "*.xlsx *.xls")]
    )
    
    if not archivo_excel:
        print("Operación cancelada")
        return
    
    # Seleccionar destino
    archivo_destino = exportador.seleccionar_destino()
    
    if not archivo_destino:
        print("Operación cancelada")
        return
    
    # Realizar exportación
    if exportador.exportar_excel_a_txt(
        archivo_excel=archivo_excel,
        archivo_destino=archivo_destino,
        separador="|",
        incluir_encabezados=True
    ):
        messagebox.showinfo("Éxito", "Exportación completada exitosamente")
    
if __name__ == "__main__":
    main()
