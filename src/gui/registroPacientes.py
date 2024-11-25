import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry  # Para el selector de fecha
import os

class GestionPacientes:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Gestión de Pacientes")
        self.ventana.geometry("800x600")
        
        # Crear marcos principales
        self.frame_form = ttk.LabelFrame(self.ventana, text="Formulario de Paciente", padding="10")
        self.frame_form.pack(fill="x", padx=10, pady=5)
        
        self.frame_lista = ttk.LabelFrame(self.ventana, text="Lista de Pacientes", padding="10")
        self.frame_lista.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Variables para el formulario
        self.var_codigo = tk.StringVar()
        self.var_nombre = tk.StringVar()
        self.var_sexo = tk.StringVar()
        self.var_enfermedad = tk.StringVar()
        
        # Crear formulario
        self.crear_formulario()
        
        # Crear lista de pacientes
        self.crear_lista_pacientes()
        
        # Crear botones de acción
        self.crear_botones()
        
        # Cargar datos iniciales
        self.cargar_pacientes()
        
        # Variable para rastrear si estamos editando
        self.editando = False
        self.id_editando = None

    def crear_formulario(self):
        """Crear los campos del formulario"""
        # Código (solo lectura)
        ttk.Label(self.frame_form, text="Código:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(self.frame_form, textvariable=self.var_codigo, state='readonly', width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Nombre
        ttk.Label(self.frame_form, text="Nombre:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.entry_nombre = ttk.Entry(self.frame_form, textvariable=self.var_nombre, width=40)
        self.entry_nombre.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=2)
        
        # Fecha de nacimiento
        ttk.Label(self.frame_form, text="Fecha de Nacimiento:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.fecha_nac = DateEntry(self.frame_form, width=12, background='darkblue',
                                 foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.fecha_nac.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Sexo
        ttk.Label(self.frame_form, text="Sexo:").grid(row=2, column=2, sticky="e", padx=5, pady=2)
        self.combo_sexo = ttk.Combobox(self.frame_form, textvariable=self.var_sexo, values=["F", "M"], width=5, state="readonly")
        self.combo_sexo.grid(row=2, column=3, sticky="w", padx=5, pady=2)
        
        # Enfermedad
        ttk.Label(self.frame_form, text="Enfermedad:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.entry_enfermedad = ttk.Entry(self.frame_form, textvariable=self.var_enfermedad, width=40)
        self.entry_enfermedad.grid(row=3, column=1, columnspan=3, sticky="w", padx=5, pady=2)
        
        # Observaciones
        ttk.Label(self.frame_form, text="Observaciones:").grid(row=4, column=0, sticky="ne", padx=5, pady=2)
        self.text_observaciones = tk.Text(self.frame_form, width=50, height=4)
        self.text_observaciones.grid(row=4, column=1, columnspan=3, sticky="w", padx=5, pady=2)

    def crear_lista_pacientes(self):
        """Crear la tabla de pacientes"""
        # Crear Treeview
        columns = ('codigo', 'nombre', 'fecha_nac', 'sexo', 'enfermedad')
        self.tabla = ttk.Treeview(self.frame_lista, columns=columns, show='headings')
        
        # Definir encabezados
        self.tabla.heading('codigo', text='Código')
        self.tabla.heading('nombre', text='Nombre')
        self.tabla.heading('fecha_nac', text='Fecha Nac.')
        self.tabla.heading('sexo', text='Sexo')
        self.tabla.heading('enfermedad', text='Enfermedad')
        
        # Definir anchos de columna
        self.tabla.column('codigo', width=70)
        self.tabla.column('nombre', width=200)
        self.tabla.column('fecha_nac', width=100)
        self.tabla.column('sexo', width=50)
        self.tabla.column('enfermedad', width=200)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(self.frame_lista, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar tabla y scrollbar
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Vincular evento de selección
        self.tabla.bind('<<TreeviewSelect>>', self.on_select)

    def crear_botones(self):
        """Crear botones de acción"""
        frame_botones = ttk.Frame(self.ventana)
        frame_botones.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame_botones, text="Nuevo", command=self.nuevo_paciente).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Guardar", command=self.guardar_paciente).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_paciente).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Limpiar", command=self.limpiar_formulario).pack(side="left", padx=5)

    def obtener_siguiente_codigo(self):
        """Obtener el siguiente código disponible"""


        folder_path = "../../data/"
        db_name = "db_psicologia_clinic.db"
        db_path = os.path.join(folder_path, db_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CAST(SUBSTR(codigo, 2) AS INTEGER)) FROM pacientes")
        resultado = cursor.fetchone()[0]
        conn.close()
        
        if resultado is None:
            return "P001"
        else:
            siguiente = resultado + 1
            return f"P{siguiente:03d}"

    def cargar_pacientes(self):
        """Cargar la lista de pacientes desde la base de datos"""
        # Limpiar tabla actual
        for item in self.tabla.get_children():
            self.tabla.delete(item)
            
        # Cargar datos de la BD
        folder_path = "../../data/"
        db_name = "db_psicologia_clinic.db"
        db_path = os.path.join(folder_path, db_name)
        print("folder :" + db_path )
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT codigo, nombre, fecha_nacimiento, sexo, enfermedad 
            FROM pacientes 
            ORDER BY codigo
        """)
        
        for row in cursor.fetchall():
            self.tabla.insert('', 'end', values=row)
            
        conn.close()

    def on_select(self, event):
        """Manejar la selección de un paciente en la tabla"""
        seleccion = self.tabla.selection()
        if not seleccion:
            return
            
        # Obtener datos del paciente seleccionado
        item = self.tabla.item(seleccion[0])
        paciente = item['values']
        
        # Cargar datos en el formulario
        self.var_codigo.set(paciente[0])
        self.var_nombre.set(paciente[1])
        # Convertir fecha al formato correcto
        self.fecha_nac.set_date(datetime.strptime(paciente[2], '%d/%m/%Y'))
        self.var_sexo.set(paciente[3])
        self.var_enfermedad.set(paciente[4])
        
        # Cargar observaciones
        folder_path = "../../data/"
        db_name = "db_psicologia_clinic.db"
        db_path = os.path.join(folder_path, db_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()        
        cursor.execute("SELECT observaciones FROM pacientes WHERE codigo = ?", (paciente[0],))
        observaciones = cursor.fetchone()[0]
        conn.close()
        
        self.text_observaciones.delete('1.0', tk.END)
        self.text_observaciones.insert('1.0', observaciones if observaciones else '')
        
        # Activar modo edición
        self.editando = True
        self.id_editando = paciente[0]

    def nuevo_paciente(self):
        """Preparar formulario para nuevo paciente"""
        self.limpiar_formulario()
        self.var_codigo.set(self.obtener_siguiente_codigo())
        self.editando = False

    def guardar_paciente(self):
        """Guardar o actualizar paciente en la BD"""
        # Validar campos obligatorios
        if not self.var_nombre.get().strip():
            messagebox.showerror("Error", "El nombre es obligatorio")
            return
            
        # Preparar datos
        datos = {
            'codigo': self.var_codigo.get(),
            'nombre': self.var_nombre.get(),
            'fecha_nacimiento': self.fecha_nac.get_date().strftime('%d/%m/%Y'),
            'sexo': self.var_sexo.get(),
            'enfermedad': self.var_enfermedad.get(),
            'observaciones': self.text_observaciones.get('1.0', tk.END).strip()
        }
        
        try:
            folder_path = "../../data/"
            db_name = "db_psicologia_clinic.db"
            db_path = os.path.join(folder_path, db_name)
            print("ruta: "+db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            if self.editando:
                # Actualizar paciente existente
                cursor.execute("""
                    UPDATE pacientes 
                    SET nombre=?, fecha_nacimiento=?, sexo=?, enfermedad=?, observaciones=?
                    WHERE codigo=?
                """, (datos['nombre'], datos['fecha_nacimiento'], datos['sexo'], 
                      datos['enfermedad'], datos['observaciones'], datos['codigo']))
            else:
                # Insertar nuevo paciente
                cursor.execute("""
                    INSERT INTO pacientes (codigo, nombre, fecha_nacimiento, sexo, enfermedad, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (datos['codigo'], datos['nombre'], datos['fecha_nacimiento'], 
                      datos['sexo'], datos['enfermedad'], datos['observaciones']))
            
            conn.commit()
            messagebox.showinfo("Éxito", "Paciente guardado correctamente")
            self.cargar_pacientes()
            self.limpiar_formulario()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error en la base de datos: {str(e)}")
            
        finally:
            conn.close()

    def eliminar_paciente(self):
        """Eliminar paciente seleccionado"""
        if not self.editando:
            messagebox.showwarning("Advertencia", "Por favor seleccione un paciente para eliminar")
            return
            
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este paciente?"):
            try:
                folder_path = "../../data/"
                db_name = "db_psicologia_clinic.db"
                db_path = os.path.join(folder_path, db_name)
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pacientes WHERE codigo = ?", (self.var_codigo.get(),))
                conn.commit()
                messagebox.showinfo("Éxito", "Paciente eliminado correctamente")
                self.cargar_pacientes()
                self.limpiar_formulario()
                
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error en la base de datos: {str(e)}")
                
            finally:
                conn.close()

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.var_codigo.set('')
        self.var_nombre.set('')
        self.fecha_nac.set_date(datetime.now())
        self.var_sexo.set('')
        self.var_enfermedad.set('')
        self.text_observaciones.delete('1.0', tk.END)
        self.editando = False
        self.id_editando = None

# Para probar la ventana individualmente
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    app = GestionPacientes(root)
    root.mainloop()