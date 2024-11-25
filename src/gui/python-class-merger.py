import ast
import astor
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Tuple, Set
import difflib

class PythonMerger:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Python Class Merger")
        self.window.geometry("800x600")
        
        # Variables
        self.source_file = tk.StringVar()
        self.target_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        # Almacenamiento de métodos y clases
        self.source_classes: Dict[str, ast.ClassDef] = {}
        self.target_classes: Dict[str, ast.ClassDef] = {}
        self.source_methods: Dict[str, Dict] = {}  # {class_name: {method_name: method}}
        self.target_methods: Dict[str, Dict] = {}
        self.method_changes: List[Tuple] = []  # (class_name, method_name, method)
        self.new_methods: List = []  # (class_name, method_name, method)
        self.new_classes: List[Tuple[str, ast.ClassDef]] = []  # (class_name, class_node)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal con scrollbar
        main_canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Grid configuration para el scroll
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Frame principal
        main_frame = ttk.Frame(scrollable_frame, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame superior para archivos
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Archivo origen
        ttk.Label(file_frame, text="Source:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.source_file, width=50).grid(row=0, column=1, padx=2)
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_file(self.source_file)).grid(row=0, column=2)

        # Archivo destino
        ttk.Label(file_frame, text="Target:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.target_file, width=50).grid(row=1, column=1, padx=2)
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_file(self.target_file)).grid(row=1, column=2)

        # Archivo salida
        ttk.Label(file_frame, text="Output:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.output_file, width=50).grid(row=2, column=1, padx=2)
        ttk.Button(file_frame, text="...", width=3, command=self.save_file).grid(row=2, column=2)

        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=5)
        ttk.Button(button_frame, text="Analyze Files", command=self.analyze_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Merge Changes", command=self.start_merge).pack(side=tk.LEFT, padx=5)

        # Lista de cambios
        ttk.Label(main_frame, text="Changes:").grid(row=2, column=0, sticky=tk.W)
        self.tree = ttk.Treeview(main_frame, columns=('Status', 'Class', 'Item'), show='headings', height=10)
        self.tree.heading('Status', text='Status')
        self.tree.heading('Class', text='Class')
        self.tree.heading('Item', text='Item')
        self.tree.column('Status', width=80)
        self.tree.column('Class', width=160)
        self.tree.column('Item', width=160)
        self.tree.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Frame para la vista previa
        preview_frame = ttk.LabelFrame(main_frame, text="Code Preview", padding="5")
        preview_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Texto original
        ttk.Label(preview_frame, text="Original:").grid(row=0, column=0, sticky=tk.W)
        self.original_text = tk.Text(preview_frame, height=8, width=45)
        self.original_text.grid(row=1, column=0, padx=2)
        
        # Texto nuevo
        ttk.Label(preview_frame, text="New:").grid(row=0, column=1, sticky=tk.W)
        self.new_text = tk.Text(preview_frame, height=8, width=45)
        self.new_text.grid(row=1, column=1, padx=2)
        
        # Bind para mostrar el código
        self.tree.bind('<<TreeviewSelect>>', self.show_code)

    def find_classes(self, filename: str) -> Dict[str, ast.ClassDef]:
        """Encuentra y retorna todas las clases en el archivo."""
        with open(filename, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read())
            
        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
        return classes

    def extract_methods(self, class_node: ast.ClassDef) -> Dict:
        """Extrae los métodos de una clase."""
        methods = {}
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                methods[node.name] = node
        return methods

    def compare_method_bodies(self, method1: ast.FunctionDef, method2: ast.FunctionDef) -> bool:
        """Compara dos métodos ignorando diferencias en espacios y comentarios."""
        code1 = astor.to_source(method1).strip()
        code2 = astor.to_source(method2).strip()
        
        code1 = '\n'.join(line.strip() for line in code1.split('\n') if line.strip() and not line.strip().startswith('#'))
        code2 = '\n'.join(line.strip() for line in code2.split('\n') if line.strip() and not line.strip().startswith('#'))
        
        return code1 != code2

    def analyze_files(self):
        """Analiza los archivos y detecta cambios en clases y métodos."""
        if not self.validate_files():
            return

        try:
            # Limpiar el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Obtener todas las clases
            self.source_classes = self.find_classes(self.source_file.get())
            self.target_classes = self.find_classes(self.target_file.get())

            if not self.source_classes:
                raise Exception("No classes found in source file")

            self.method_changes = []
            self.new_methods = []
            self.new_classes = []

            # Analizar cada clase
            for class_name, source_class in self.source_classes.items():
                if class_name in self.target_classes:
                    # Clase existente - analizar métodos
                    source_methods = self.extract_methods(source_class)
                    target_methods = self.extract_methods(self.target_classes[class_name])
                    
                    for method_name, source_method in source_methods.items():
                        if method_name in target_methods:
                            if self.compare_method_bodies(source_method, target_methods[method_name]):
                                self.method_changes.append((class_name, method_name, source_method))
                                self.tree.insert('', 'end', values=('Modified', class_name, f"Method: {method_name}"))
                        else:
                            self.new_methods.append((class_name, method_name, source_method))
                            self.tree.insert('', 'end', values=('New', class_name, f"Method: {method_name}"))
                else:
                    # Nueva clase
                    self.new_classes.append((class_name, source_class))
                    self.tree.insert('', 'end', values=('New', class_name, 'Entire Class'))

            # Mostrar resultados
            total_changes = len(self.method_changes) + len(self.new_methods) + len(self.new_classes)
            if total_changes == 0:
                messagebox.showinfo("Results", "No differences found")
            else:
                messagebox.showinfo("Analysis Complete", 
                                  f"Found {len(self.method_changes)} modified methods, "
                                  f"{len(self.new_methods)} new methods, and "
                                  f"{len(self.new_classes)} new classes")

        except Exception as e:
            messagebox.showerror("Error", f"Error analyzing files: {str(e)}")
            raise e

    def start_merge(self):
        """Inicia el proceso de fusión de cambios."""
        if not any([self.method_changes, self.new_methods, self.new_classes]):
            messagebox.showwarning("Warning", "No changes to merge")
            return

        try:
            # Leer el archivo destino completo
            with open(self.target_file.get(), 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())

            changes_made = False

            # Procesar clases existentes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    
                    # Procesar métodos modificados
                    for c_name, m_name, source_method in self.method_changes:
                        if c_name == class_name:
                            if messagebox.askyesno("Confirm Change", 
                                                 f"Update method '{m_name}' in class '{c_name}'?"):
                                for i, method_node in enumerate(node.body):
                                    if isinstance(method_node, ast.FunctionDef) and method_node.name == m_name:
                                        if hasattr(method_node, 'decorator_list'):
                                            source_method.decorator_list = method_node.decorator_list
                                        node.body[i] = source_method
                                        changes_made = True
                                        break

                    # Procesar métodos nuevos
                    for c_name, m_name, method in self.new_methods:
                        if c_name == class_name:
                            if messagebox.askyesno("Confirm Addition", 
                                                 f"Add new method '{m_name}' to class '{c_name}'?"):
                                node.body.append(method)
                                changes_made = True

            # Procesar clases nuevas
            for class_name, class_node in self.new_classes:
                if messagebox.askyesno("Confirm Addition", 
                                     f"Add new class '{class_name}'?"):
                    tree.body.append(class_node)
                    changes_made = True

            if changes_made:
                # Guardar cambios
                with open(self.output_file.get(), 'w', encoding='utf-8') as file:
                    file.write(astor.to_source(tree))
                messagebox.showinfo("Success", "Merge completed successfully")
            else:
                messagebox.showinfo("Information", "No changes were made")

        except Exception as e:
            messagebox.showerror("Error", f"Error during merge: {str(e)}")
            raise e

    def show_code(self, event):
        """Muestra el código del elemento seleccionado."""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        status = item['values'][0]
        class_name = item['values'][1]
        item_type = item['values'][2]

        # Limpiar los campos de texto
        self.original_text.delete('1.0', tk.END)
        self.new_text.delete('1.0', tk.END)

        if status == "Modified":
            # Mostrar método modificado
            method_name = item_type.split(": ")[1]
            target_method = self.extract_methods(self.target_classes[class_name])[method_name]
            source_method = next(m for c, n, m in self.method_changes 
                               if c == class_name and n == method_name)
            
            self.original_text.insert('1.0', astor.to_source(target_method))
            self.new_text.insert('1.0', astor.to_source(source_method))
            
        elif "Method" in item_type:
            # Mostrar nuevo método
            method_name = item_type.split(": ")[1]
            source_method = next(m for c, n, m in self.new_methods 
                               if c == class_name and n == method_name)
            self.new_text.insert('1.0', astor.to_source(source_method))
            
        else:  # Nueva clase
            # Mostrar clase completa
            source_class = next(c for n, c in self.new_classes if n == class_name)
            self.new_text.insert('1.0', astor.to_source(source_class))

    def browse_file(self, var):
        """Abre el diálogo para seleccionar archivo."""
        filename = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            var.set(filename)

    def save_file(self):
        """Abre el diálogo para guardar archivo."""
        filename = filedialog.asksaveasfilename(defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)

    def validate_files(self):
        """Valida que se hayan seleccionado todos los archivos necesarios."""
        if not self.source_file.get():
            messagebox.showwarning("Warning", "Please select source file")
            return False
        if not self.target_file.get():
            messagebox.showwarning("Warning", "Please select target file")
            return False
        if not self.output_file.get():
            messagebox.showwarning("Warning", "Please specify output file")
            return False
            
        # Validar que los archivos existan y sean diferentes
        if not all(map(os.path.exists, [self.source_file.get(), self.target_file.get()])):
            messagebox.showwarning("Warning", "One or more files do not exist")
            return False
            
        if self.source_file.get() == self.target_file.get():
            messagebox.showwarning("Warning", "Source and target files must be different")
            return False
            
        return True

    def compare_class_structure(self, class1: ast.ClassDef, class2: ast.ClassDef) -> Dict:
        """
        Compara la estructura de dos clases y retorna las diferencias.
        """
        differences = {
            'base_classes': [],
            'decorators': [],
            'class_vars': [],
            'methods': []
        }
        
        # Comparar clases base
        bases1 = [astor.to_source(b).strip() for b in class1.bases]
        bases2 = [astor.to_source(b).strip() for b in class2.bases]
        differences['base_classes'] = list(set(bases1) - set(bases2))
        
        # Comparar decoradores
        dec1 = [astor.to_source(d).strip() for d in getattr(class1, 'decorator_list', [])]
        dec2 = [astor.to_source(d).strip() for d in getattr(class2, 'decorator_list', [])]
        differences['decorators'] = list(set(dec1) - set(dec2))
        
        # Comparar variables de clase
        vars1 = [(n.targets[0].id, astor.to_source(n.value).strip()) 
                for n in class1.body if isinstance(n, ast.Assign)]
        vars2 = [(n.targets[0].id, astor.to_source(n.value).strip()) 
                for n in class2.body if isinstance(n, ast.Assign)]
        differences['class_vars'] = list(set(vars1) - set(vars2))
        
        return differences

    def show_structure_changes(self, class_name: str):
        """
        Muestra los cambios estructurales entre dos versiones de una clase.
        """
        if class_name not in self.source_classes or class_name not in self.target_classes:
            return
            
        source_class = self.source_classes[class_name]
        target_class = self.target_classes[class_name]
        
        differences = self.compare_class_structure(source_class, target_class)
        
        # Crear ventana de diálogo para mostrar diferencias
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Structure Changes - {class_name}")
        dialog.geometry("600x400")
        
        # Crear notebook para las diferentes categorías
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Página para clases base
        bases_frame = ttk.Frame(notebook)
        notebook.add(bases_frame, text='Base Classes')
        if differences['base_classes']:
            for base in differences['base_classes']:
                ttk.Label(bases_frame, text=f"+ {base}").pack(anchor='w', padx=5)
        else:
            ttk.Label(bases_frame, text="No changes in base classes").pack(anchor='w', padx=5)
        
        # Página para decoradores
        dec_frame = ttk.Frame(notebook)
        notebook.add(dec_frame, text='Decorators')
        if differences['decorators']:
            for dec in differences['decorators']:
                ttk.Label(dec_frame, text=f"+ {dec}").pack(anchor='w', padx=5)
        else:
            ttk.Label(dec_frame, text="No changes in decorators").pack(anchor='w', padx=5)
        
        # Página para variables de clase
        vars_frame = ttk.Frame(notebook)
        notebook.add(vars_frame, text='Class Variables')
        if differences['class_vars']:
            for name, value in differences['class_vars']:
                ttk.Label(vars_frame, text=f"+ {name} = {value}").pack(anchor='w', padx=5)
        else:
            ttk.Label(vars_frame, text="No changes in class variables").pack(anchor='w', padx=5)

    def add_compare_button(self):
        """Añade un botón para comparar estructuras de clases."""
        ttk.Button(self.window, text="Compare Structure", 
                  command=self.show_structure_dialog).grid(row=5, column=0, pady=5)

    def show_structure_dialog(self):
        """Muestra un diálogo para seleccionar la clase a comparar."""
        if not self.source_classes or not self.target_classes:
            messagebox.showwarning("Warning", "Please analyze files first")
            return
            
        # Crear diálogo
        dialog = tk.Toplevel(self.window)
        dialog.title("Compare Class Structure")
        dialog.geometry("300x150")
        
        # Obtener clases comunes
        common_classes = set(self.source_classes.keys()) & set(self.target_classes.keys())
        if not common_classes:
            ttk.Label(dialog, text="No common classes found").pack(pady=20)
            return
            
        # Crear combobox para seleccionar clase
        ttk.Label(dialog, text="Select class to compare:").pack(pady=10)
        class_var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=class_var, values=list(common_classes))
        combo.pack(pady=10)
        
        # Botón para comparar
        ttk.Button(dialog, text="Compare", 
                  command=lambda: self.show_structure_changes(class_var.get())).pack(pady=10)

    def run(self):
        """Inicia la aplicación."""
        self.add_compare_button()  # Añadir botón de comparación
        self.window.mainloop()

if __name__ == "__main__":
    import os  # Añadido para validación de archivos
    app = PythonMerger()
    app.run()