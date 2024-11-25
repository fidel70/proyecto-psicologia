import ast
import astor
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Tuple
import difflib

class PythonMerger:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Fusionador de Clases Python")
        self.window.geometry("1000x800")
        
        # Variables
        self.source_file = tk.StringVar()
        self.target_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        # Para almacenar los métodos
        self.source_methods: Dict = {}
        self.target_methods: Dict = {}
        self.method_changes: List[Tuple] = []
        self.new_methods: List = []
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Archivo origen
        ttk.Label(main_frame, text="Archivo origen (con los cambios):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.source_file, width=80).grid(row=1, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=lambda: self.browse_file(self.source_file)).grid(row=1, column=1, padx=5)
        
        # Archivo destino
        ttk.Label(main_frame, text="Archivo destino (que recibirá los cambios):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.target_file, width=80).grid(row=3, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=lambda: self.browse_file(self.target_file)).grid(row=3, column=1, padx=5)
        
        # Archivo resultante
        ttk.Label(main_frame, text="Nombre del archivo resultante:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_file, width=80).grid(row=5, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=self.save_file).grid(row=5, column=1, padx=5)
        
        # Frame para la vista previa
        preview_frame = ttk.LabelFrame(main_frame, text="Vista previa de cambios", padding="5")
        preview_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Texto original
        ttk.Label(preview_frame, text="Código Original:").grid(row=0, column=0, sticky=tk.W)
        self.original_text = tk.Text(preview_frame, height=10, width=50)
        self.original_text.grid(row=1, column=0, padx=5)
        
        # Texto nuevo
        ttk.Label(preview_frame, text="Código Nuevo:").grid(row=0, column=1, sticky=tk.W)
        self.new_text = tk.Text(preview_frame, height=10, width=50)
        self.new_text.grid(row=1, column=1, padx=5)
        
        # Lista de métodos
        ttk.Label(main_frame, text="Métodos con cambios:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.tree = ttk.Treeview(main_frame, columns=('Estado', 'Método'), show='headings', height=10)
        self.tree.heading('Estado', text='Estado')
        self.tree.heading('Método', text='Método')
        self.tree.column('Estado', width=100)
        self.tree.column('Método', width=500)
        self.tree.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Bind para mostrar el código cuando se selecciona un método
        self.tree.bind('<<TreeviewSelect>>', self.show_method_code)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Analizar archivos", 
                  command=self.analyze_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Iniciar fusión", 
                  command=self.start_merge).pack(side=tk.LEFT, padx=5)
                  
    def show_method_code(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        method_name = item['values'][1]
        estado = item['values'][0]
        
        # Limpiar los campos de texto
        self.original_text.delete('1.0', tk.END)
        self.new_text.delete('1.0', tk.END)
        
        if estado == "Modificado":
            # Mostrar versión original
            target_code = astor.to_source(self.target_methods[method_name])
            self.original_text.insert('1.0', target_code)
            
            # Mostrar versión nueva
            source_code = astor.to_source(self.source_methods[method_name])
            self.new_text.insert('1.0', source_code)
        else:  # Nuevo método
            source_method = next(m for name, m in self.new_methods if name == method_name)
            source_code = astor.to_source(source_method)
            self.new_text.insert('1.0', source_code)
            
    def browse_file(self, var):
        filename = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("Todos los archivos", "*.*")]
        )
        if filename:
            var.set(filename)
            
    def save_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
            
    def get_class_methods(self, filename: str) -> Dict:
        """Extrae los métodos de la primera clase encontrada en el archivo."""
        with open(filename, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read())
            
        methods = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Ignorar comentarios y ajustar indentación
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Normalizar el código del método
                        method_code = astor.to_source(item).strip()
                        methods[item.name] = item
                break
                
        return methods
    
    def normalize_code(self, code: str) -> str:
        """Normaliza el código para comparación."""
        return '\n'.join(line.strip() for line in code.split('\n') if line.strip())
    
    def analyze_files(self):
        if not self.validate_files():
            return
            
        try:
            # Limpiar el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Obtener métodos
            self.source_methods = self.get_class_methods(self.source_file.get())
            self.target_methods = self.get_class_methods(self.target_file.get())
            
            self.method_changes = []
            self.new_methods = []
            
            # Verificar métodos modificados
            for name, source_method in self.source_methods.items():
                source_code = self.normalize_code(astor.to_source(source_method))
                
                if name in self.target_methods:
                    target_code = self.normalize_code(astor.to_source(self.target_methods[name]))
                    
                    # Usar difflib para una comparación más precisa
                    if source_code != target_code:
                        self.method_changes.append((name, source_method))
                        self.tree.insert('', 'end', values=('Modificado', name))
                else:
                    self.new_methods.append((name, source_method))
                    self.tree.insert('', 'end', values=('Nuevo', name))
                    
            if not self.method_changes and not self.new_methods:
                messagebox.showinfo("Información", "No se encontraron diferencias entre las clases")
            else:
                messagebox.showinfo("Análisis completado", 
                                  f"Se encontraron {len(self.method_changes)} métodos modificados y "
                                  f"{len(self.new_methods)} métodos nuevos")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al analizar archivos: {str(e)}")
            raise e
            
    def start_merge(self):
        if not self.method_changes and not self.new_methods:
            messagebox.showwarning("Advertencia", "No hay cambios para fusionar")
            return
            
        try:
            # Leer el archivo destino completo
            with open(self.target_file.get(), 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                
            # Encontrar la clase
            class_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_node = node
                    break
                    
            if not class_node:
                raise Exception("No se encontró ninguna clase en el archivo destino")
                
            # Procesar cambios
            changes_made = False
            
            # Métodos modificados
            for name, source_method in self.method_changes:
                if messagebox.askyesno("Confirmar cambio", 
                                     f"¿Desea actualizar el método '{name}'?"):
                    # Encontrar y reemplazar el método
                    for i, node in enumerate(class_node.body):
                        if isinstance(node, ast.FunctionDef) and node.name == name:
                            class_node.body[i] = source_method
                            changes_made = True
                            break
                            
            # Métodos nuevos
            for name, method in self.new_methods:
                if messagebox.askyesno("Confirmar adición", 
                                     f"¿Desea agregar el nuevo método '{name}'?"):
                    class_node.body.append(method)
                    changes_made = True
                    
            if changes_made:
                # Guardar los cambios
                with open(self.output_file.get(), 'w', encoding='utf-8') as file:
                    file.write(astor.to_source(tree))
                messagebox.showinfo("Éxito", "Fusión completada correctamente")
            else:
                messagebox.showinfo("Información", "No se realizaron cambios")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la fusión: {str(e)}")
            raise e
            
    def validate_files(self):
        if not self.source_file.get():
            messagebox.showwarning("Advertencia", "Seleccione el archivo origen")
            return False
        if not self.target_file.get():
            messagebox.showwarning("Advertencia", "Seleccione el archivo destino")
            return False
        if not self.output_file.get():
            messagebox.showwarning("Advertencia", "Especifique el nombre del archivo resultante")
            return False
        return True
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = PythonMerger()
    app.run()
