import sqlite3
import pandas as pd
import os

def exportar_db_a_excel(db_path, output_folder='exports'):
    # Crear carpeta de exportación si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    
    # Obtener todas las tablas
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cursor.fetchall()
    
    # Crear un Excel writer para guardar múltiples hojas
    excel_path = os.path.join(output_folder, 'db_psicologia_clinic.xlsx')
    writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
    
    # Exportar cada tabla a una hoja diferente
    for tabla in tablas:
        nombre_tabla = tabla[0]
        # Leer tabla completa
        df = pd.read_sql_query(f"SELECT * FROM {nombre_tabla}", conn)
        # Guardar en una hoja del Excel
        df.to_excel(writer, sheet_name=nombre_tabla, index=False)
        print(f"Tabla {nombre_tabla} exportada")
    
    # Guardar y cerrar
    writer.close()
    conn.close()
    
    print(f"\nBase de datos exportada exitosamente a: {excel_path}")

if __name__ == "__main__":
    # Ruta al archivo de base de datos
    db_path = 'db_psicologia_clinic.db'
    
    try:
        exportar_db_a_excel(db_path)
    except Exception as e:
        print(f"Error durante la exportación: {str(e)}")
