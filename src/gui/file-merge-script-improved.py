import difflib
import os

def merge_files():
    # Solicitar nombres de archivos
    print("\nNota: Los archivos deben estar en el mismo directorio que este script")
    origin_file = input("\nIngrese el nombre del archivo origen (con los cambios): ").strip()
    target_file = input("Ingrese el nombre del archivo destino (donde aplicar los cambios): ").strip()
    result_file = input("Ingrese el nombre del archivo resultante: ").strip()
    
    # Verificar que los archivos origen y destino existen
    if not os.path.exists(origin_file):
        print(f"\nError: El archivo origen '{origin_file}' no existe.")
        return
    
    if not os.path.exists(target_file):
        print(f"\nError: El archivo destino '{target_file}' no existe.")
        return
    
    try:
        # Leer contenido de los archivos
        with open(origin_file, 'r', encoding='utf-8') as f:
            origin_content = f.read()
        
        with open(target_file, 'r', encoding='utf-8') as f:
            target_content = f.read()
        
        # Convertir el contenido a listas de líneas
        origin_lines = origin_content.splitlines(keepends=True)
        target_lines = target_content.splitlines(keepends=True)
        
        # Crear el unificado diff
        diff = difflib.unified_diff(
            target_lines,
            origin_lines,
            fromfile=target_file,
            tofile=origin_file,
            n=3  # Contexto de 3 líneas
        )
        
        # Aplicar los cambios usando SequenceMatcher
        matcher = difflib.SequenceMatcher(None, target_content, origin_content)
        merged_content = ""
        
        for opcode in matcher.get_opcodes():
            tag, i1, i2, j1, j2 = opcode
            
            if tag == 'equal':
                # Mantener el contenido sin cambios
                merged_content += target_content[i1:i2]
            elif tag == 'replace' or tag == 'insert':
                # Usar el contenido del archivo origen
                merged_content += origin_content[j1:j2]
            # Para 'delete', no agregamos nada
        
        # Guardar el resultado
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        
        # Mostrar estadísticas y resumen
        print(f"\nMerge completado. Resultado guardado en '{result_file}'")
        print("\nResumen de cambios:")
        
        # Contar líneas
        origin_line_count = len(origin_lines)
        target_line_count = len(target_lines)
        result_line_count = len(merged_content.splitlines())
        
        print(f"- Líneas en archivo origen: {origin_line_count}")
        print(f"- Líneas en archivo destino: {target_line_count}")
        print(f"- Líneas en archivo resultado: {result_line_count}")
        
        # Mostrar diferencias encontradas
        changes = list(matcher.get_opcodes())
        change_count = sum(1 for tag, _, _, _, _ in changes if tag != 'equal')
        print(f"- Número de bloques modificados: {change_count}")
        
        # Preguntar si se desea ver los cambios detallados
        if input("\n¿Desea ver el detalle de los cambios? (s/n): ").lower().strip() == 's':
            print("\nDetalle de cambios:")
            for tag, i1, i2, j1, j2 in changes:
                if tag != 'equal':
                    print(f"\n{tag.upper()}:")
                    if tag in ('replace', 'delete'):
                        print(f"- Contenido original:")
                        print(target_content[i1:i2].rstrip())
                    if tag in ('replace', 'insert'):
                        print(f"+ Nuevo contenido:")
                        print(origin_content[j1:j2].rstrip())
        
    except Exception as e:
        print(f"\nError durante el proceso de merge: {str(e)}")

if __name__ == "__main__":
    print("=== Script de Merge de Archivos ===")
    print("Este script combinará los cambios del archivo origen en el archivo destino.")
    merge_files()
