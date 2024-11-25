import ast
import astor
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Tuple

class PythonMerger:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Fusionador de Clases Python")
        self.window.geometry("800x600")
        
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
        ttk.Entry(main_frame, textvariable=self.source_file, width=60).grid(row=1, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=lambda: self.browse_file(self.source_file)).grid(row=1, column=1, padx=5)
        
        # Archivo destino
        ttk.Label(main_frame, text="Archivo destino (que recibirá los cambios):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.target_file, width=60).grid(row=3, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=lambda: self.browse_file(self.target_file)).grid(row=3, column=1, padx=5)
        
        # Archivo resultante
        ttk.Label(main_frame, text="Nombre del archivo resultante:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_file, width=60).grid(row=5, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=self.save_file).grid(row=5, column=1, padx=5)
        
        # Área de comparación
        ttk.Label(main_frame, text="Comparación de métodos:").grid(row=6, column=0, sticky=tk.W, pady=5)
        
        # Frame para los métodos
        methods_frame = ttk.Frame(main_frame)
        methods_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview para mostrar los métodos
        self.tree = ttk.Treeview(methods_frame, columns=('Estado', 'Método'), show='headings')
        self.tree.heading('Estado', text='Estado')
        self.tree.heading('Método', text='Método')
        self.tree.column('Estado', width=100)
        self.tree.column('Método', width=500)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para el Treeview
        scrollbar = ttk.Scrollbar(methods_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Botones de acción
        ttk.Button(main_frame, text="Analizar archivos", 
                  command=self.analyze_files).grid(row=8, column=0, pady=10)
        ttk.Button(main_frame, text="Iniciar fusión", 
                  command=self.start_merge).grid(row=8, column=1, pady=10)
        
        # Configurar el grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        methods_frame.columnconfigure(0, weight=1)
        methods_frame.rowconfigure(0, weight=1)
        
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
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods[item.name] = item
                break  # Solo procesa la primera clase
                
        return methods
    
    def analyze_files(self):
        """Analiza los archivos y muestra las diferencias en el Treeview."""
        if not self.validate_files():
            return
            
        try:
            # Limpiar el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Obtener métodos de ambos archivos
            self.source_methods = self.get_class_methods(self.source_file.get())
            self.target_methods = self.get_class_methods(self.target_file.get())
            
            # Comparar métodos
            self.method_changes = []
            self.new_methods = []
            
            # Verificar métodos modificados
            for name, source_method in self.source_methods.items():
                if name in self.target_methods:
                    source_code = astor.to_source(source_method)
                    target_code = astor.to_source(self.target_methods[name])
                    
                    if source_code != target_code:
                        self.method_changes.append((name, source_method))
                        self.tree.insert('', 'end', values=('Modificado', name))
                else:
                    self.new_methods.append((name, source_method))
                    self.tree.insert('', 'end', values=('Nuevo', name))
                    
            if not self.method_changes and not self.new_methods:
                messagebox.showinfo("Información", "No se encontraron diferencias entre las clases")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al analizar archivos: {str(e)}")
            
    def start_merge(self):
        """Inicia el proceso de fusión interactivo."""
        if not self.method_changes and not self.new_methods:
            messagebox.showwarning("Advertencia", "No hay cambios para fusionar")
            return
            
        try:
            # Leer el archivo destino
            with open(self.target_file.get(), 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                
            # Encontrar la clase en el árbol AST
            class_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_node = node
                    break
                    
            if not class_node:
                raise Exception("No se encontró ninguna clase en el archivo destino")
                
            # Procesar métodos modificados
            for name, source_method in self.method_changes:
                if messagebox.askyesno("Confirmar cambio", 
                                     f"¿Desea actualizar el método '{name}'?\n\n" +
                                     f"Código nuevo:\n{astor.to_source(source_method)}"):
                    # Eliminar el método existente
                    class_node.body = [m for m in class_node.body 
                                     if not (isinstance(m, ast.FunctionDef) and m.name == name)]
                    # Agregar el nuevo método
                    class_node.body.append(source_method)
                    
            # Procesar métodos nuevos
            for name, method in self.new_methods:
                if messagebox.askyesno("Confirmar adición", 
                                     f"¿Desea agregar el nuevo método '{name}'?\n\n" +
                                     f"Código:\n{astor.to_source(method)}"):
                    class_node.body.append(method)
                    
            # Guardar los cambios
            with open(self.output_file.get(), 'w', encoding='utf-8') as file:
                file.write(astor.to_source(tree))
                
            messagebox.showinfo("Éxito", "Fusión completada correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la fusión: {str(e)}")
            
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
