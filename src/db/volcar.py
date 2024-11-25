import pandas as pd
import sqlite3
from datetime import datetime

def exportar_a_excel():
    try:
        conn = sqlite3.connect('db_psicologia_clinic.db')
        
        # Obtener datos del paciente
        df_paciente = pd.read_sql_query("""
            SELECT codigo, nombre, fecha_nacimiento, sexo, enfermedad, observaciones, fecha_registro
            FROM pacientes 
            WHERE codigo = 'P001'
        """, conn)
        
        # Obtener pensamientos
        df_pensamientos = pd.read_sql_query("""
            SELECT p.codigo, p.pensamiento, p.fecha_registro
            FROM pensamientos p
            WHERE p.codigo LIKE 'P001%'
            ORDER BY p.codigo
        """, conn)
        
        # Obtener dimensiones
        df_dimensiones = pd.read_sql_query("""
            SELECT p.codigo as codigo_pensamiento, 
                   d.fecha, d.cantidad, d.duracion, d.intensidad
            FROM dimensiones d
            JOIN pensamientos p ON d.pensamiento_id = p.id
            WHERE p.codigo LIKE 'P001%'
            ORDER BY p.codigo, d.fecha
        """, conn)
        
        conn.close()
        
        # Crear archivo Excel
        nombre_archivo = f"Paciente_P001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with pd.ExcelWriter(nombre_archivo) as writer:
            df_paciente.to_excel(writer, sheet_name='Datos Paciente', index=False)
            df_pensamientos.to_excel(writer, sheet_name='Pensamientos', index=False)
            df_dimensiones.to_excel(writer, sheet_name='Dimensiones', index=False)
            
        return f"Archivo creado: {nombre_archivo}"
        
    except Exception as e:
        return f"Error exportando datos: {str(e)}"

if __name__ == "__main__":
    print(exportar_a_excel())