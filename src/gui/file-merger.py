import difflib
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class FileMerger:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Fusionador de Archivos")
        self.window.geometry("600x400")
        
        # Variables
        self.source_file = tk.StringVar()
        self.target_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Archivo origen
        ttk.Label(main_frame, text="Archivo origen (con los cambios):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.source_file, width=50).grid(row=1, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=lambda: self.browse_file(self.source_file)).grid(row=1, column=1, padx=5)
        
        # Archivo destino
        ttk.Label(main_frame, text="Archivo destino (que recibirá los cambios):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.target_file, width=50).grid(row=3, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=lambda: self.browse_file(self.target_file)).grid(row=3, column=1, padx=5)
        
        # Archivo resultante
        ttk.Label(main_frame, text="Nombre del archivo resultante:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_file, width=50).grid(row=5, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Examinar", command=lambda: self.save_file()).grid(row=5, column=1, padx=5)
        
        # Preview
        ttk.Label(main_frame, text="Vista previa de cambios:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.preview_text = tk.Text(main_frame, height=10, width=60)
        self.preview_text.grid(row=7, column=0, columnspan=2, pady=5)
        
        # Botones
        ttk.Button(main_frame, text="Vista previa", command=self.preview_changes).grid(row=8, column=0, pady=10, padx=5)
        ttk.Button(main_frame, text="Fusionar archivos", command=self.merge_files).grid(row=8, column=1, pady=10, padx=5)
        
    def browse_file(self, var):
        filename = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if filename:
            var.set(filename)
            
    def save_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
            
    def preview_changes(self):
        if not self.validate_files():
            return
            
        try:
            with open(self.source_file.get(), 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            with open(self.target_file.get(), 'r', encoding='utf-8') as f:
                target_lines = f.readlines()
                
            differ = difflib.Differ()
            diff = list(differ.compare(target_lines, source_lines))
            
            self.preview_text.delete('1.0', tk.END)
            for line in diff:
                if line.startswith('  '):  # línea sin cambios
                    self.preview_text.insert(tk.END, line)
                elif line.startswith('- '):  # línea eliminada
                    self.preview_text.insert(tk.END, line, 'removed')
                    self.preview_text.tag_configure('removed', foreground='red')
                elif line.startswith('+ '):  # línea agregada
                    self.preview_text.insert(tk.END, line, 'added')
                    self.preview_text.tag_configure('added', foreground='green')
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al previsualizar cambios: {str(e)}")
            
    def merge_files(self):
        if not self.validate_files():
            return
            
        try:
            with open(self.source_file.get(), 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            with open(self.target_file.get(), 'r', encoding='utf-8') as f:
                target_lines = f.readlines()
                
            # Crear un objeto Differ para comparar los archivos
            differ = difflib.Differ()
            diff = list(differ.compare(target_lines, source_lines))
            
            # Aplicar los cambios
            merged_lines = []
            for line in diff:
                if line.startswith('  ') or line.startswith('+ '):
                    merged_lines.append(line[2:])
                    
            # Guardar el resultado
            with open(self.output_file.get(), 'w', encoding='utf-8') as f:
                f.writelines(merged_lines)
                
            messagebox.showinfo("Éxito", "Archivos fusionados correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al fusionar archivos: {str(e)}")
            
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
    app = FileMerger()
    app.run()
