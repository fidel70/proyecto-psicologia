import sqlite3
from sqlite3 import Error

def modificar_duracion():
    try:
        conexion = sqlite3.connect("db_psicologia_clinic.db")
        cursor = conexion.cursor()
        
        # Crear tabla temporal
        cursor.execute('''
        CREATE TABLE dimensiones_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pensamiento_id INTEGER,
            fecha DATE DEFAULT CURRENT_DATE,
            cantidad INTEGER CHECK(cantidad BETWEEN 0 AND 10),
            duracion INTEGER CHECK(duracion BETWEEN 0 AND 60),
            intensidad INTEGER CHECK(intensidad BETWEEN 0 AND 10),
            FOREIGN KEY (pensamiento_id) REFERENCES pensamientos (id)
        )
        ''')
        
        # Copiar datos existentes
        cursor.execute('''
        INSERT INTO dimensiones_temp (id, pensamiento_id, fecha, cantidad, duracion, intensidad)
        SELECT id, pensamiento_id, fecha, cantidad, 
               CASE WHEN duracion > 60 THEN 60 ELSE duracion END,
               intensidad
        FROM dimensiones
        ''')
        
        # Eliminar tabla original y renombrar la temporal
        cursor.execute('DROP TABLE dimensiones')
        cursor.execute('ALTER TABLE dimensiones_temp RENAME TO dimensiones')
        
        conexion.commit()
        print("Duración modificada exitosamente")
        
    except Error as e:
        print(f"Error modificando la duración: {e}")
    
    finally:
        if conexion:
            conexion.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    modificar_duracion()