"""Fix mojibake en elite.py.

Reemplaza secuencias de caracteres cirilicos (resultado de doble-codificacion
UTF-8 -> CP1251 -> UTF-8) por sus equivalentes correctos.
"""
import sys
import ast

# Mapeo basado en codepoints exactos detectados en el archivo
# Secuencias largas PRIMERO para evitar conflictos
MAPEO = {
    # Acentos latinos (Г + X, vienen de chars como n, a, e, i, o, u, N)
    '\u0413\u201C': '\u00D3',     # Г + comilla izquierda -> O
    '\u0413\u04B1': '\u00F1',     # Г + ұ -> n
    '\u0413\u04D9': '\u00FA',     # Г + ә -> u
    '\u0413\u0492': '\u00C1',     # Г + Ғ -> A
    '\u0413\u0454': '\u00FA',     # Г + є -> u
    '\u0413\u00AD': '\u00ED',     # Г + soft hyphen -> i
    '\u0413\u040E': '\u00E1',     # Г + Ў -> a
    '\u0413\u049A': '\u00CD',     # Г + Қ -> I
    '\u0413\u04A1': '\u00DA',     # Г + ҡ -> U
    '\u0413\u00B1': '\u00F1',     # Г + ± -> n
    '\u0413\u0027': '\u00D1',     # Г + apostrofe ASCII -> N

    # Emojis y simbolos (в + X, vienen de emojis UTF-8 de 3+ bytes)
    '\u0432\u2022\u0497': '\u2550',       # borde horizontal
    '\u0432\u04B3\u2026': '\u2605',       # estrella (вҳ…)
    '\u0432\u04B3\u2022': '\u2615',       # cafe (вҳ•)
    '\u0432\u04B3\u201D': '\u2614',       # lluvia (вҳ")
    '\u0432\u04A1\u04AA': '\u26BD',       # balon (вҡҪ)
    '\u0432\u04EF\u0497': '\u2B50',       # estrella alternativa (вӯҗ)
    '\u0432\u04B8\u0456': '\u23F3',       # reloj de arena (вҸі)
    '\u0432\u04B8\u04B1\u043F\u0451': '\u23F1\uFE0F',  # cronometro (вҸ±пёҸ)
    '\u0432\u04A3\u04B2\u043F\u0451': '\u2708\uFE0F',  # avion (вңҲпёҸ)
    '\u0432\u0493': '\u20E3',             # keycap combinador (вғЈ)
    '\u0432\u0083\u0423': '\u0023\uFE0F\u20E3',  # keycap #
    '\u0432\u2020\u2019': '\u2192',       # flecha
    '\u0432\u00A6': '\u2026',             # elipsis

    # Signos de puntuacion (В + X)
    '\u0412\u049D': '\u00BF',             # Вҝ -> interrogacion inicial
    '\u0412\u040E': '\u00A1',             # ВЎ -> exclamacion inicial

    # Emojis con doble-encoding latin-1 (ð + chars)
    '\u00F0\u0178\u201C\u040A': '\U0001F4CC',  # ðŸ"Њ -> 📌 (pushpin)
    '\u00F0\u0178\u201D\u0455': '\U0001F643',  # ðŸ™ -> 🙃 (upside-down)

    # Residuales sueltos
    '\u043F\u0451\u04B8': '\uFE0F',      # variation selector FE0F (residual)
    '\u0497\u0020': '\u0020',            # җ space -> space (residual tras ↩️)
    '\u049D\u0020': '\u0020',             # қ space -> space (residual)
}


def fix_content(text):
    """Aplica el mapeo a todo el texto, secuencias largas primero."""
    result = text
    for bad, good in sorted(MAPEO.items(), key=lambda x: -len(x[0])):
        result = result.replace(bad, good)
    return result


def count_mojibake(text):
    """Cuenta caracteres cirilicos restantes para verificar."""
    count = 0
    for ch in text:
        cp = ord(ch)
        if 0x0400 <= cp <= 0x04FF:
            count += 1
    return count


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'elite.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    before = count_mojibake(original)
    fixed = fix_content(original)
    after = count_mojibake(fixed)

    cambios = before - after
    print(f"Archivo: {filepath}")
    print(f"Caracteres cirilicos antes: {before}")
    print(f"Caracteres cirilicos despues: {after}")
    print(f"Caracteres corregidos: {cambios}")

    if cambios > 0:
        try:
            ast.parse(fixed)
            print("OK: sintaxis Python valida")
        except SyntaxError as e:
            print(f"ERROR de sintaxis: {e}")
            print("NO se guardaran los cambios")
            sys.exit(1)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed)
        print(f"Guardado: {filepath}")
    else:
        print("No habia mojibake que corregir")


if __name__ == '__main__':
    main()
