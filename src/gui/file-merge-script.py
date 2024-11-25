import difflib
import os

def merge_files():
    # Solicitar nombres de archivos
    origin_file = input("Ingrese el nombre del archivo origen (con los cambios): ")
    target_file = input("Ingrese el nombre del archivo destino (donde aplicar los cambios): ")
    result_file = input("Ingrese el nombre del archivo resultante: ")
    
    # Verificar que los archivos origen y destino existen
    if not os.path.exists(origin_file):
        print(f"Error: El archivo origen '{origin_file}' no existe.")
        return
    
    if not os.path.exists(target_file):
        print(f"Error: El archivo destino '{target_file}' no existe.")
        return
    
    try:
        # Leer contenido de los archivos
        with open(origin_file, 'r', encoding='utf-8') as f:
            origin_lines = f.readlines()
        
        with open(target_file, 'r', encoding='utf-8') as f:
            target_lines = f.readlines()
        
        # Crear objeto Differ para comparar archivos
        differ = difflib.Differ()
        
        # Obtener diferencias
        diff = list(differ.compare(target_lines, origin_lines))
        
        # Procesar diferencias y crear el contenido resultante
        merged_lines = []
        i = 0
        while i < len(diff):
            line = diff[i]
            if line.startswith('  '):  # Línea sin cambios
                merged_lines.append(line[2:])
            elif line.startswith('+ '):  # Línea agregada
                merged_lines.append(line[2:])
            elif line.startswith('- '):  # Línea eliminada
                # Verificar si la siguiente línea es un cambio
                if i + 1 < len(diff) and diff[i + 1].startswith('+ '):
                    # Es un cambio, tomamos la nueva versión
                    merged_lines.append(diff[i + 1][2:])
                    i += 1  # Saltar la siguiente línea ya que la procesamos
            i += 1
        
        # Guardar resultado en el nuevo archivo
        with open(result_file, 'w', encoding='utf-8') as f:
            f.writelines(merged_lines)
        
        print(f"\nMerge completado. Resultado guardado en '{result_file}'")
        
        # Mostrar estadísticas
        print("\nEstadísticas del merge:")
        print(f"Líneas en archivo origen: {len(origin_lines)}")
        print(f"Líneas en archivo destino: {len(target_lines)}")
        print(f"Líneas en archivo resultado: {len(merged_lines)}")
        
        # Contar cambios
        changes = sum(1 for line in diff if line.startswith(('+ ', '- ')))
        print(f"Número de cambios aplicados: {changes}")
        
    except Exception as e:
        print(f"Error durante el proceso de merge: {str(e)}")

if __name__ == "__main__":
    print("=== Script de Merge de Archivos ===")
    print("Este script combinará los cambios del archivo origen en el archivo destino.")
    print("Los archivos deben estar en el mismo directorio que este script.\n")
    
    merge_files()
