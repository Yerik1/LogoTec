# frontend/lexer.py
from __future__ import annotations
import sys
import os
import re
import ply.lex as lex

# --- Palabras reservadas (en minúscula) ---
# Subconjunto inicial: movimiento, giros, init y aumento.

_reserved = {
    # movimientos
    'avanza': 'AV', 'av': 'AV',
    'retrocede': 'RE', 're': 'RE',
    'giraderecha': 'GD', 'gd': 'GD',
    'giraizquierda': 'GI', 'gi': 'GI',

    # variable init & increment
    'inic': 'INIC',
    'inc': 'INC',

    # --- dibujo ---
    'ponpos': 'PONPOS',
    'ponxy': 'PONXY',
    'ponx': 'PONX',
    'pony': 'PONY',
    'ponrumbo': 'PONRUMBO',
    'rumbo': 'RUMBO',
    'bajalapiz': 'BL', 'bl': 'BL',
    'subelapiz': 'SB', 'sb': 'SB',
    'ocultatortuga': 'OT', 'ot': 'OT',
    'poncolorlapiz': 'PONCL', 'poncl': 'PONCL',

    # --- logicas ---
    'si': 'SI', 'mientras': 'MIENTRAS',
    'y': 'Y', 'o': 'O',

    # --- bloques ---
    'haz': 'HAZ',
    'espera': 'ESPERA',
    'para': 'PARA', 'fin': 'FIN',
    'haz.hasta': 'HAZ_HASTA', 'hasta': 'HASTA',
    'haz.mientras': 'HAZ_MIENTRAS',
    'centro': 'CENTRO',
    'ejecuta': 'EJECUTA',
    'repite': 'REPITE',



    # --- matematicas ---
    'iguales?': 'IGUALES',
    'mayorque?': 'MAYORQ',
    'menorque?': 'MENORQ',
    'producto': 'PRODUCTO',
    'potencia': 'POTENCIA',
    'division': 'DIVISION', 'división': 'DIVISION',
    'suma': 'SUMA',
    'diferencia': 'DIFERENCIA',
    'azar': 'AZAR',
}

# --- Lista de tokens que PLY exporta ---
tokens = [
    # numéricos e identificadores
    'NUM', 'ID',"STRING",
] + sorted(set(_reserved.values()))

# --- Caracteres literales sueltos (no generan token con nombre) ---
# Paréntesis, corchetes, coma, igual y operadores aritméticos básicos
literals = ['(', ')', '[', ']', ',', '=', '+', '-', '*', '/']

# --- Ignorar espacios y tabs ---
t_ignore = ' \t'

# --- Comentarios estilo // ---
def t_COMMENT(t):
    r'//[^\n]*'
    pass  # ignorar

# --- Saltos de línea (llevar el conteo correcto de la línea) ---
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# --- Números (enteros y decimales) ---
def t_NUM(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_STRING(t):
    r'"([^"\n]|\\.)*"'    # admite \" y otros escapes simples
    # quita las comillas y desescapa lo básico
    raw = t.value[1:-1]
    t.value = bytes(raw, "utf-8").decode("unicode_escape")
    return t

# --- Identificadores y palabras clave (case-insensitive) ---
# Permitimos típicos IDs de lenguajes: letra/underscore inicial, luego alfanum/underscore.
def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_]+)?\??'
    lexeme = t.value
    lexeme_lower = t.value.lower()
    # normalizamos las claves con y sin acento para 'división'
    if lexeme_lower == 'división':
        lexeme_lower = 'division'
    # Palabras con punto y signo de pregunta (p.ej. "haz.hasta", "iguales?")
    # Las dejamos como están y comparamos en minúscula:
    if lexeme_lower in _reserved:
        t.type = _reserved[lexeme_lower]
    else:
        if '.' in lexeme or '?' in lexeme:
            raise SyntaxError(
                f"Identificador inválido '{lexeme}': "
                "las variables no pueden contener '.' ni '?'."
            )

            # 2.2 Debe iniciar en minúscula
        if not lexeme[0].islower():
            raise SyntaxError(
                f"Identificador inválido '{lexeme}': "
                "debe iniciar con una letra minúscula."
            )

            # 2.3 Longitud máxima 10
        if len(lexeme) > 10:
            raise SyntaxError(
                f"Identificador inválido '{lexeme}': "
                "longitud máxima permitida es 10 caracteres."
            )

            # 2.4 Solo letras, dígitos, '_', '&', '@'
        if not re.fullmatch(r'[a-z][A-Za-z0-9_&@]{0,9}', lexeme):
            raise SyntaxError(
                f"Identificador inválido '{lexeme}': "
                "solo se permiten letras, dígitos, y '_', '&', '@' (después del primero)."
            )
        t.type = 'ID'
        setattr(t.lexer, 'seen_variable', True)
    return t

# --- Errores léxicos ---
def t_error(t):
    col = _column(t)
    msg = f"Carácter inesperado '{t.value[0]}' en línea {t.lexer.lineno}, col {col}"
    raise SyntaxError(msg)

# Utilidad: columna aproximada (para mensajes)
def _column(t):
    last_nl = t.lexer.lexdata.rfind('\n', 0, t.lexpos)
    return t.lexpos - (last_nl + 1)

# --- Builder del lexer ---
def build_lexer(**kwargs):
    return lex.lex(**kwargs)

# --- Modo script para probar rápido ---
def _run_cli(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    lexer = build_lexer()
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(f"{tok.type:<10} {repr(tok.value):<12} (line {tok.lineno})")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python -m frontend.lexer <archivo.logo>")
        sys.exit(1)
    _run_cli(sys.argv[1])