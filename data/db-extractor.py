import sqlite3

def export_tables_to_txt():
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('db_psicologia_clinic.db')
        cursor = conn.cursor()

        # Exportar tabla pacientes
        cursor.execute("""
            SELECT id, codigo, nombre, fecha_nacimiento, sexo, 
                   enfermedad, observaciones, fecha_registro 
            FROM pacientes 
            ORDER BY id
        """)
        
        with open('pacientes_data.txt', 'w', encoding='utf-8') as f:
            # Escribir encabezados
            f.write('id|codigo|nombre|fecha_nacimiento|sexo|enfermedad|observaciones|fecha_registro\n')
            # Escribir datos
            for row in cursor.fetchall():
                f.write('|'.join(str(value) if value is not None else 'nan' for value in row) + '\n')

        # Exportar tabla pensamientos
        cursor.execute("""
            SELECT id, codigo, pensamiento 
            FROM pensamientos 
            ORDER BY codigo
        """)
        
        with open('pensamientos_data.txt', 'w', encoding='utf-8') as f:
            # Escribir encabezados
            f.write('id|codigo|pensamiento\n')
            # Escribir datos
            for row in cursor.fetchall():
                f.write('|'.join(str(value) if value is not None else 'nan' for value in row) + '\n')

        # Exportar tabla dimensiones
        cursor.execute("""
            SELECT d.id, p.codigo as pensamiento_codigo, 
                   d.fecha, d.cantidad, d.duracion, d.intensidad
            FROM dimensiones d
            JOIN pensamientos p ON d.pensamiento_id = p.id
            ORDER BY d.fecha, p.codigo
        """)
        
        with open('dimensiones_data.txt', 'w', encoding='utf-8') as f:
            # Escribir encabezados
            f.write('id|pensamiento_codigo|fecha|cantidad|duracion|intensidad\n')
            # Escribir datos
            for row in cursor.fetchall():
                f.write('|'.join(str(value) if value is not None else 'nan' for value in row) + '\n')

        print("Datos exportados exitosamente a archivos txt:")
        print("- pacientes_data.txt")
        print("- pensamientos_data.txt")
        print("- dimensiones_data.txt")

    except sqlite3.Error as e:
        print(f"Error al exportar datos: {e}")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    export_tables_to_txt()
