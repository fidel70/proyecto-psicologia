import sqlite3
from sqlite3 import Error

def crear_base_datos():
    try:
        # Conectar a la base de datos (la creará si no existe)
        conexion = sqlite3.connect("db_psicologia_clinic.db")
        cursor = conexion.cursor()
        
        # Crear tabla pacientes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE CHECK(codigo LIKE 'P%' AND length(codigo) = 4),
            nombre TEXT NOT NULL,
            fecha_nacimiento DATE NOT NULL,
            sexo TEXT CHECK(sexo IN ('F', 'M')),
            enfermedad TEXT,
            observaciones TEXT,
            fecha_registro DATE DEFAULT CURRENT_DATE
        )
        ''')
        
        # Crear tabla pensamientos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pensamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE CHECK(codigo LIKE 'P___-PS%'),
            paciente_id INTEGER,
            pensamiento TEXT NOT NULL,
            fecha_registro DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
        ''')
        
        # Crear tabla dimensiones
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dimensiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pensamiento_id INTEGER,
            fecha DATE DEFAULT CURRENT_DATE,
            cantidad INTEGER CHECK(cantidad BETWEEN 0 AND 10),
            duracion INTEGER CHECK(duracion BETWEEN 0 AND 120),
            intensidad INTEGER CHECK(intensidad BETWEEN 0 AND 10),
            FOREIGN KEY (pensamiento_id) REFERENCES pensamientos (id)
        )
        ''')
        
        # Confirmar los cambios
        conexion.commit()
        print("Base de datos creada exitosamente")
        
    except Error as e:
        print(f"Error creando la base de datos: {e}")
    
    finally:
        if conexion:
            conexion.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    crear_base_datos()