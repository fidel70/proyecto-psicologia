import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
from registroPacientes import GestionPacientes
from registraPensamientos import VentanaPensamientos
from registroDimensionesbu import VentanaDimensiones
from estadisticasfecha import VentanaEstadisticas
class AppPsicologia:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Seguimiento Psicológico")
        
        # Configurar tamaño de ventana
        self.root.geometry("300x300")
        
        # Crear menú principal
        self.crear_menu()
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botones principales
        ttk.Button(self.main_frame, text="Gestión de Pacientes", 
                  command=self.abrir_gestion_pacientes).grid(row=0, column=0, pady=5)
        
        self.btn_pensamientos = ttk.Button(self.main_frame, text="Registro de Pensamientos", 
                                         command=self.abrir_registro_pensamientos)
        self.btn_pensamientos.grid(row=1, column=0, pady=5)
        
        self.btn_dimensiones = ttk.Button(self.main_frame, text="Registro de Dimensiones", 
                                        command=self.abrir_registro_dimensiones)
        self.btn_dimensiones.grid(row=2, column=0, pady=5)
        
        self.btn_estadisticas = ttk.Button(self.main_frame, text="Estadísticas", 
                                         command=self.abrir_estadisticas)
        self.btn_estadisticas.grid(row=3, column=0, pady=5)
        
        # Verificar estado inicial
        self.verificar_estado_botones()

    def verificar_estado_botones(self):
        """Verifica si hay datos para activar/desactivar botones"""

        # Define la carpeta específica y el nombre del archivo
        folder_path = "../../data/"
        db_name = "db_psicologia_clinic.db"
        db_path = os.path.join(folder_path, db_name)
        print(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si hay pacientes
        cursor.execute("SELECT COUNT(*) FROM pacientes")
        hay_pacientes = cursor.fetchone()[0] > 0
        
        # Verificar si hay pensamientos
        cursor.execute("SELECT COUNT(*) FROM pensamientos")
        hay_pensamientos = cursor.fetchone()[0] > 0
        
        # Verificar si hay dimensiones
        cursor.execute("SELECT COUNT(*) FROM dimensiones")
        hay_dimensiones = cursor.fetchone()[0] > 0
        
        conn.close()
        
        # Activar/desactivar botones según corresponda
        self.btn_pensamientos['state'] = 'normal' if hay_pacientes else 'disabled'
        self.btn_dimensiones['state'] = 'normal' if hay_pensamientos else 'disabled'
        self.btn_estadisticas['state'] = 'normal' if hay_dimensiones else 'disabled'

    def crear_menu(self):
        """Crear barra de menú"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.mostrar_acerca_de)

    def abrir_gestion_pacientes(self):
        """Abrir ventana de gestión de pacientes"""
        #ventana = tk.Toplevel(self.root)
        #ventana.title("Gestión de Pacientes")
        #ventana.geometry("600x400")
        ventana = GestionPacientes(root)
        
        # Aquí irían los widgets para gestionar pacientes
        # Se implementará en un método separado

    def abrir_registro_pensamientos(self):
        """Abrir ventana de registro de pensamientos"""
        #ventana = tk.Toplevel(self.root)
        #ventana.title("Registro de Pensamientos")
        #ventana.geometry("600x400")
        ventana = VentanaPensamientos(root)
        
        # Aquí irían los widgets para registrar pensamientos
        # Se implementará en un método separado

    def abrir_registro_dimensiones(self):
        """Abrir ventana de registro de dimensiones"""
        #ventana = tk.Toplevel(self.root)
        #ventana.title("Registro de Dimensiones")
        #ventana.geometry("600x400")
        ventana = VentanaDimensiones(root)
        # Aquí irían los widgets para registrar dimensiones
        # Se implementará en un método separado

    def abrir_estadisticas(self):
        """Abrir ventana de estadísticas"""
        # ventana = tk.Toplevel(self.root)
        # ventana.title("Estadísticas")
        # ventana.geometry("1600x700")
        #from estadisticasfecha import VentanaEstadisticas
        #if __name__ == "__main__":
        ventana = VentanaEstadisticas(root)
        #app.ventana.mainloop()

        #ventana = VentanaEstadisticas()
        #ventana.correr_estadisticas()
        
        # Aquí irían los widgets para mostrar estadísticas
        # Se implementará en un método separado

    def mostrar_acerca_de(self):
        """Mostrar información sobre la aplicación"""
        messagebox.showinfo(
            "Acerca de",
            "Sistema de Seguimiento Psicológico\nVersión 1.0\n\nDesarrollado para uso clínico"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = AppPsicologia(root)
    root.mainloop()