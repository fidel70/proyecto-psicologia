import sqlite3
from datetime import datetime

def create_psychology_database():
    """Crear base de datos para gestión de pacientes psicológicos."""
    
    conexion = sqlite3.connect("bd_psicologia.db")
    cursor = conexion.cursor()

    # Crear tabla de pacientes con información más completa
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        fecha_nacimiento DATE NOT NULL,
        sexo TEXT CHECK(sexo IN ('F', 'M')) NOT NULL,
        email TEXT UNIQUE,
        telefono TEXT,
        direccion TEXT,
        ocupacion TEXT,
        estado_civil TEXT CHECK(estado_civil IN ('Soltero', 'Casado', 'Divorciado', 'Viudo', 'Otro')),
        fecha_primera_consulta DATE NOT NULL,
        motivo_consulta TEXT,
        diagnostico_principal TEXT,
        medicacion_actual TEXT,
        antecedentes_medicos TEXT,
        estado TEXT CHECK(estado IN ('Activo', 'Inactivo', 'Alta', 'Abandonó')) NOT NULL DEFAULT 'Activo',
        fecha_ultima_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notas_confidenciales TEXT
    )''')

    # Crear tabla de sesiones para registro de consultas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sesiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        fecha DATETIME NOT NULL,
        duracion INTEGER NOT NULL, -- duración en minutos
        tipo_sesion TEXT CHECK(tipo_sesion IN ('Individual', 'Grupal', 'Familiar', 'Evaluación', 'Urgencia')) NOT NULL,
        asistencia TEXT CHECK(asistencia IN ('Asistió', 'Canceló', 'No asistió')) NOT NULL,
        notas_sesion TEXT,
        plan_tratamiento TEXT,
        proxima_cita DATE,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE RESTRICT
    )''')

    # Crear tabla de pensamientos con más contexto
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pensamientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        paciente_id INTEGER NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        situacion TEXT NOT NULL,
        pensamiento TEXT NOT NULL,
        emocion TEXT NOT NULL,
        intensidad_emocion INTEGER CHECK(intensidad_emocion BETWEEN 0 AND 10),
        respuesta_adaptativa TEXT,
        resultado TEXT,
        categoria TEXT CHECK(categoria IN ('Automático', 'Distorsión', 'Nuclear', 'Otro')),
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )''')

    # Crear tabla de seguimiento de dimensiones más detallada
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dimensiones_seguimiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pensamiento_id INTEGER NOT NULL,
        fecha_evaluacion DATE NOT NULL,
        frecuencia INTEGER CHECK(frecuencia BETWEEN 0 AND 10) NOT NULL,
        duracion INTEGER CHECK(duracion BETWEEN 0 AND 10) NOT NULL,
        intensidad INTEGER CHECK(intensidad BETWEEN 0 AND 10) NOT NULL,
        grado_creencia INTEGER CHECK(grado_creencia BETWEEN 0 AND 10),
        interferencia_vida INTEGER CHECK(interferencia_vida BETWEEN 0 AND 10),
        estrategias_afrontamiento TEXT,
        progreso_observado TEXT,
        FOREIGN KEY (pensamiento_id) REFERENCES pensamientos(id) ON DELETE CASCADE
    )''')

    # Crear tabla de objetivos terapéuticos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS objetivos_terapeuticos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        fecha_establecimiento DATE NOT NULL,
        descripcion TEXT NOT NULL,
        prioridad INTEGER CHECK(prioridad BETWEEN 1 AND 5),
        estado TEXT CHECK(estado IN ('Pendiente', 'En progreso', 'Logrado', 'Abandonado')) NOT NULL,
        fecha_logro DATE,
        notas_progreso TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )''')

    # Crear tabla de evaluaciones psicológicas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evaluaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        fecha_evaluacion DATE NOT NULL,
        tipo_prueba TEXT NOT NULL,
        resultados TEXT NOT NULL,
        interpretacion TEXT,
        recomendaciones TEXT,
        archivo_adjunto BLOB,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE RESTRICT
    )''')

    # Crear índices para optimizar búsquedas frecuentes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pacientes_codigo ON pacientes(codigo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_fecha ON sesiones(fecha)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pensamientos_paciente ON pensamientos(paciente_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluaciones_paciente ON evaluaciones(paciente_id)')

    # Crear vista para resumen de pacientes
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS resumen_pacientes AS
    SELECT 
        p.id,
        p.codigo,
        p.nombre || ' ' || p.apellidos as nombre_completo,
        p.fecha_primera_consulta,
        p.diagnostico_principal,
        p.estado,
        COUNT(DISTINCT s.id) as total_sesiones,
        MAX(s.fecha) as ultima_sesion
    FROM pacientes p
    LEFT JOIN sesiones s ON p.id = s.paciente_id
    GROUP BY p.id
    ''')

    # Crear disparadores para mantener la integridad de los datos
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_fecha_modificacion
    AFTER UPDATE ON pacientes
    BEGIN
        UPDATE pacientes 
        SET fecha_ultima_modificacion = CURRENT_TIMESTAMP
        WHERE id = NEW.id;
    END;
    ''')

    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    create_psychology_database()