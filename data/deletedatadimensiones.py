import sqlite3
from sqlite3 import Error

def borrar_dimensiones():
    try:
        conexion = sqlite3.connect("db_psicologia_clinic.db")
        cursor = conexion.cursor()
        
        cursor.execute('DELETE FROM dimensiones')
        conexion.commit()
        
        # Verificar registros eliminados
        cursor.execute('SELECT COUNT(*) FROM dimensiones')
        count = cursor.fetchone()[0]
        
        print(f"Registros borrados. Quedan {count} registros en la tabla dimensiones.")
        
    except Error as e:
        print(f"Error: {e}")
    
    finally:
        if conexion:
            conexion.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    borrar_dimensiones()