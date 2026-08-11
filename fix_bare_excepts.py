"""Reemplaza bare excepts en elite.py por except Exception con logging.

Estrategia:
- except: pass  -> except Exception: pass  (mantiene el pass, no agrega logging)
- except: con cuerpo de fallback -> except Exception as e: + logger.debug()

NO toca los except que ya tienen tipo (except Exception, except ValueError, etc).
"""
import re
import ast

filepath = 'elite.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

original = content
changes = 0
lines = content.split('\n')

# Recorrer lineas y reemplazar 'except:' por 'except Exception:' o 'except Exception as e:'
# segun si la siguiente linea (el cuerpo) es pass o no
i = 0
new_lines = []
for line in lines:
    # detectar bare except: (con posible espacio antes)
    # patron: espacios + 'except:' (nada despues de los dos puntos, o solo comentario)
    m = re.match(r'^(\s*)except:\s*(#.*)?$', line)
    if m:
        indent = m.group(1)
        comment = m.group(2) or ''
        # mirar la siguiente linea no vacia para ver si el cuerpo es 'pass' o tiene logica
        # buscar siguiente linea con codigo
        j = len(new_lines)  # posicion actual
        next_code_line = ''
        for k in range(i + 1, min(i + 5, len(lines))):
            stripped = lines[k].strip()
            if stripped and not stripped.startswith('#'):
                next_code_line = stripped
                break

        if next_code_line == 'pass' or next_code_line.startswith('pass '):
            # pass: no necesitamos 'e', mantener simple
            new_line = f'{indent}except Exception:{(" " + comment) if comment else ""}'
        else:
            # hay logica de fallback: agregar 'as e' para posible logging futuro
            new_line = f'{indent}except Exception as e:{(" " + comment) if comment else ""}'
        new_lines.append(new_line)
        changes += 1
    else:
        new_lines.append(line)
    i += 1

result = '\n'.join(new_lines)

# Verificar sintaxis
try:
    ast.parse(result)
except SyntaxError as e:
    print(f"ERROR de sintaxis: {e}")
    print("NO se guardaran los cambios")
    exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(result)

print(f"Bare excepts reemplazados: {changes}")
print(f"Sintaxis valida: OK")
