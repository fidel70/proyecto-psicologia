import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class VentanaPensamientos:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Registro de Pensamientos")
        self.ventana.geometry("800x600")
        
        # Crear marco principal con padding
        self.main_frame = ttk.Frame(self.ventana, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sección de selección de paciente
        self.crear_seccion_paciente()
        
        # Sección de gestión de pensamientos
        self.crear_seccion_pensamientos()
        
        # Variables para el formulario de pensamientos
        self.pensamiento_text = tk.StringVar()
        
        # Cargar pacientes al inicio
        self.cargar_pacientes()
        
    def crear_seccion_paciente(self):
        """Crear sección para seleccionar paciente"""
        # Frame para selección de paciente
        paciente_frame = ttk.LabelFrame(self.main_frame, text="Seleccionar Paciente", padding="5")
        paciente_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Combobox para seleccionar paciente
        ttk.Label(paciente_frame, text="Paciente:").grid(row=0, column=0, padx=5)
        self.paciente_combo = ttk.Combobox(paciente_frame, width=50, state='readonly')
        self.paciente_combo.grid(row=0, column=1, padx=5)
        self.paciente_combo.bind('<<ComboboxSelected>>', self.on_paciente_selected)

    def crear_seccion_pensamientos(self):
        """Crear sección para gestionar pensamientos"""
        # Frame para pensamientos
        pensamiento_frame = ttk.LabelFrame(self.main_frame, text="Gestión de Pensamientos", padding="5")
        pensamiento_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Área de texto para el pensamiento
        ttk.Label(pensamiento_frame, text="Pensamiento:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.pensamiento_text_widget = tk.Text(pensamiento_frame, height=4, width=50)
        self.pensamiento_text_widget.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Botones de acción
        btn_frame = ttk.Frame(pensamiento_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="Añadir Pensamiento", 
                  command=self.añadir_pensamiento).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Modificar Pensamiento", 
                  command=self.modificar_pensamiento).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Eliminar Pensamiento", 
                  command=self.eliminar_pensamiento).grid(row=0, column=2, padx=5)
        
        # Lista de pensamientos
        ttk.Label(pensamiento_frame, text="Pensamientos registrados:").grid(row=3, column=0, 
                                                                          sticky=tk.W, padx=5, pady=5)
        
        # Treeview para mostrar pensamientos
        self.tree = ttk.Treeview(pensamiento_frame, columns=('Código', 'Pensamiento', 'Fecha'), 
                                show='headings', height=10)
        self.tree.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        
        # Configurar columnas
        self.tree.heading('Código', text='Código')
        self.tree.heading('Pensamiento', text='Pensamiento')
        self.tree.heading('Fecha', text='Fecha Registro')
        
        self.tree.column('Código', width=100)
        self.tree.column('Pensamiento', width=400)
        self.tree.column('Fecha', width=100)
        
        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(pensamiento_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=4, column=2, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind para selección en el treeview
        self.tree.bind('<<TreeviewSelect>>', self.on_pensamiento_selected)

    def cargar_pacientes(self):
        """Cargar lista de pacientes en el combobox"""
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nombre FROM pacientes ORDER BY codigo")
            pacientes = cursor.fetchall()
            conn.close()
            
            # Formatear para el combobox
            self.pacientes_lista = [f"{p[0]} - {p[1]}" for p in pacientes]
            self.paciente_combo['values'] = self.pacientes_lista
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar pacientes: {str(e)}")

    def generar_codigo_pensamiento(self, paciente_codigo):
        """Generar código único para pensamiento"""
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            # Obtener el último número de pensamiento para este paciente
            cursor.execute("""
                SELECT MAX(CAST(SUBSTR(codigo, -3) AS INTEGER))
                FROM pensamientos
                WHERE codigo LIKE ?
            """, (f'{paciente_codigo}-PS%',))
            
            ultimo_numero = cursor.fetchone()[0]
            conn.close()
            
            # Generar nuevo número
            nuevo_numero = 1 if ultimo_numero is None else ultimo_numero + 1
            
            return f"{paciente_codigo}-PS{nuevo_numero:03d}"
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al generar código: {str(e)}")
            return None

    def cargar_pensamientos(self, paciente_codigo):
        """Cargar pensamientos del paciente seleccionado"""
        try:
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            # Limpiar treeview actual
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Cargar pensamientos
            cursor.execute("""
                SELECT codigo, pensamiento, fecha_registro
                FROM pensamientos
                WHERE codigo LIKE ?
                ORDER BY codigo
            """, (f'{paciente_codigo}%',))
            
            for pensamiento in cursor.fetchall():
                self.tree.insert('', 'end', values=pensamiento)
                
            conn.close()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar pensamientos: {str(e)}")

    def añadir_pensamiento(self):
        """Añadir nuevo pensamiento"""
        if not self.paciente_combo.get():
            messagebox.showwarning("Advertencia", "Por favor seleccione un paciente")
            return
            
        pensamiento = self.pensamiento_text_widget.get("1.0", "end-1c").strip()
        if not pensamiento:
            messagebox.showwarning("Advertencia", "Por favor ingrese un pensamiento")
            return
            
        if len(pensamiento) > 500:
            messagebox.showwarning("Advertencia", "El pensamiento excede los 500 caracteres")
            return
            
        try:
            paciente_codigo = self.paciente_combo.get().split(' - ')[0]
            nuevo_codigo = self.generar_codigo_pensamiento(paciente_codigo)
            
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pensamientos (codigo, pensamiento, fecha_registro)
                VALUES (?, ?, date('now'))
            """, (nuevo_codigo, pensamiento))
            
            conn.commit()
            conn.close()
            
            # Actualizar lista de pensamientos
            self.cargar_pensamientos(paciente_codigo)
            
            # Limpiar campo de texto
            self.pensamiento_text_widget.delete("1.0", tk.END)
            
            messagebox.showinfo("Éxito", "Pensamiento registrado correctamente")
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al registrar pensamiento: {str(e)}")

    def modificar_pensamiento(self):
        """Modificar pensamiento seleccionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un pensamiento para modificar")
            return
            
        pensamiento = self.pensamiento_text_widget.get("1.0", "end-1c").strip()
        if not pensamiento:
            messagebox.showwarning("Advertencia", "Por favor ingrese un pensamiento")
            return
            
        if len(pensamiento) > 500:
            messagebox.showwarning("Advertencia", "El pensamiento excede los 500 caracteres")
            return
            
        try:
            codigo = self.tree.item(selected[0])['values'][0]
            
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE pensamientos
                SET pensamiento = ?
                WHERE codigo = ?
            """, (pensamiento, codigo))
            
            conn.commit()
            conn.close()
            
            # Actualizar lista de pensamientos
            paciente_codigo = self.paciente_combo.get().split(' - ')[0]
            self.cargar_pensamientos(paciente_codigo)
            
            # Limpiar campo de texto
            self.pensamiento_text_widget.delete("1.0", tk.END)
            
            messagebox.showinfo("Éxito", "Pensamiento modificado correctamente")
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al modificar pensamiento: {str(e)}")

    def eliminar_pensamiento(self):
        """Eliminar pensamiento seleccionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un pensamiento para eliminar")
            return
            
        if not messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este pensamiento?"):
            return
            
        try:
            codigo = self.tree.item(selected[0])['values'][0]
            
            conn = sqlite3.connect('../../data/db_psicologia_clinic.db')
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM pensamientos WHERE codigo = ?", (codigo,))
            
            conn.commit()
            conn.close()
            
            # Actualizar lista de pensamientos
            paciente_codigo = self.paciente_combo.get().split(' - ')[0]
            self.cargar_pensamientos(paciente_codigo)
            
            # Limpiar campo de texto
            self.pensamiento_text_widget.delete("1.0", tk.END)
            
            messagebox.showinfo("Éxito", "Pensamiento eliminado correctamente")
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al eliminar pensamiento: {str(e)}")

    def on_paciente_selected(self, event):
        """Manejar selección de paciente"""
        if self.paciente_combo.get():
            paciente_codigo = self.paciente_combo.get().split(' - ')[0]
            self.cargar_pensamientos(paciente_codigo)

    def on_pensamiento_selected(self, event):
        """Manejar selección de pensamiento en el treeview"""
        selected = self.tree.selection()
        if selected:
            # Obtener valores del item seleccionado
            valores = self.tree.item(selected[0])['values']
            # Mostrar pensamiento en el campo de texto
            self.pensamiento_text_widget.delete("1.0", tk.END)
            self.pensamiento_text_widget.insert("1.0", valores[1])


def main():
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    app = VentanaPensamientos(root)
    root.mainloop()

if __name__ == "__main__":
    main()            