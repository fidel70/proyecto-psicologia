import difflib
import os
from typing import List, Tuple
import sys

class FileMerger:
    def __init__(self):
        self.origin_file = ""
        self.target_file = ""
        self.result_file = ""
        self.changes: List[Tuple[str, str, int]] = []  # [(tipo, contenido, línea)]

    def request_filenames(self):
        """Solicita y valida los nombres de archivo."""
        while True:
            self.origin_file = input("\nIngrese el nombre del archivo origen (con los cambios): ").strip()
            if os.path.exists(self.origin_file):
                break
            print(f"Error: El archivo '{self.origin_file}' no existe.")

        while True:
            self.target_file = input("Ingrese el nombre del archivo destino (donde aplicar los cambios): ").strip()
            if os.path.exists(self.target_file):
                break
            print(f"Error: El archivo '{self.target_file}' no existe.")

        while True:
            self.result_file = input("Ingrese el nombre del archivo resultante: ").strip()
            if self.result_file:
                if os.path.exists(self.result_file):
                    overwrite = input(f"El archivo '{self.result_file}' ya existe. ¿Desea sobrescribirlo? (s/n): ").lower()
                    if overwrite != 's':
                        continue
                break
            print("Error: Debe especificar un nombre de archivo.")

    def read_file(self, filename: str) -> List[str]:
        """Lee un archivo y retorna sus líneas."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.readlines()
        except UnicodeDecodeError:
            try:
                with open(filename, 'r', encoding='latin-1') as f:
                    return f.readlines()
            except Exception as e:
                print(f"Error al leer el archivo {filename}: {str(e)}")
                sys.exit(1)
        except Exception as e:
            print(f"Error al leer el archivo {filename}: {str(e)}")
            sys.exit(1)

    def analyze_differences(self):
        """Analiza las diferencias entre los archivos."""
        origin_lines = self.read_file(self.origin_file)
        target_lines = self.read_file(self.target_file)

        # Usar SequenceMatcher para mejor detección de cambios
        matcher = difflib.SequenceMatcher(None, target_lines, origin_lines)
        
        result_lines = target_lines.copy()
        offset = 0  # Para ajustar las posiciones después de cada cambio

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # Cambio: se reemplazó contenido
                old_content = ''.join(target_lines[i1:i2])
                new_content = ''.join(origin_lines[j1:j2])
                self.changes.append(('change', f'Línea {i1+1}: {old_content.strip()} -> {new_content.strip()}', i1))
                result_lines[i1+offset:i2+offset] = origin_lines[j1:j2]
                offset += (j2 - j1) - (i2 - i1)
            elif tag == 'delete':
                # Eliminación: se quitó contenido
                self.changes.append(('delete', f'Línea {i1+1}: Se eliminó: {target_lines[i1].strip()}', i1))
                del result_lines[i1+offset:i2+offset]
                offset -= (i2 - i1)
            elif tag == 'insert':
                # Inserción: se agregó contenido nuevo
                new_content = ''.join(origin_lines[j1:j2])
                self.changes.append(('insert', f'Línea {i1+1}: Se insertó: {new_content.strip()}', i1))
                result_lines[i1+offset:i1+offset] = origin_lines[j1:j2]
                offset += (j2 - j1)

        return result_lines

    def show_differences(self):
        """Muestra las diferencias encontradas."""
        if not self.changes:
            print("\nNo se encontraron diferencias entre los archivos.")
            return False

        print("\nCambios detectados:")
        for tipo, desc, linea in sorted(self.changes, key=lambda x: x[2]):
            if tipo == 'change':
                print(f"\033[93m{desc}\033[0m")  # Amarillo para cambios
            elif tipo == 'delete':
                print(f"\033[91m{desc}\033[0m")  # Rojo para eliminaciones
            elif tipo == 'insert':
                print(f"\033[92m{desc}\033[0m")  # Verde para inserciones

        return True

    def save_result(self, result_lines: List[str]):
        """Guarda el resultado en el archivo especificado."""
        try:
            with open(self.result_file, 'w', encoding='utf-8') as f:
                f.writelines(result_lines)
            print(f"\nArchivo resultado guardado exitosamente en '{self.result_file}'")
        except Exception as e:
            print(f"Error al guardar el archivo resultado: {str(e)}")
            sys.exit(1)

    def merge(self):
        """Ejecuta el proceso completo de merge."""
        print("=== Script de Merge de Archivos ===")
        print("Este script combinará los cambios del archivo origen en el archivo destino.")
        
        # Solicitar nombres de archivo
        self.request_filenames()
        
        # Analizar diferencias
        result_lines = self.analyze_differences()
        
        # Mostrar diferencias y pedir confirmación
        if self.show_differences():
            confirm = input("\n¿Desea aplicar estos cambios? (s/n): ").lower()
            if confirm != 's':
                print("Operación cancelada.")
                return
        
        # Guardar resultado
        self.save_result(result_lines)
        
        # Mostrar estadísticas
        print("\nEstadísticas del merge:")
        print(f"Cambios realizados: {len(self.changes)}")
        changes_by_type = {
            'change': sum(1 for c in self.changes if c[0] == 'change'),
            'delete': sum(1 for c in self.changes if c[0] == 'delete'),
            'insert': sum(1 for c in self.changes if c[0] == 'insert')
        }
        print(f"  - Modificaciones: {changes_by_type['change']}")
        print(f"  - Eliminaciones: {changes_by_type['delete']}")
        print(f"  - Inserciones: {changes_by_type['insert']}")

if __name__ == "__main__":
    merger = FileMerger()
    merger.merge()
