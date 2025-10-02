# frontend/parser.py
from __future__ import annotations
import sys
import ply.yacc as yacc
from ply.yacc import PlyLogger

from .lexer import build_lexer, tokens
from .ast import Node

# Precedencias
precedence = (
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', 'UMINUS'),
)

# --------- Gramática ----------
def p_program(p):
    "program : stmt_list"
    p[0] = Node("PROGRAM").add(p[1])

def p_stmt_list_single(p):
    "stmt_list : stmt"
    p[0] = Node("STMTS").add(p[1])

def p_stmt_list_more(p):
    "stmt_list : stmt_list stmt"
    p[1].add(p[2])
    p[0] = p[1]

def p_stmt_move_turn(p):
    """stmt : AV expr
            | RE expr
            | GD expr
            | GI expr"""
    cmd = p.slice[1].type
    p[0] = Node(cmd, line=p.lineno(1)).add(p[2])

def p_stmt_inic(p):
    "stmt : INIC ID '=' expr"
    p[0] = Node("INIC", line=p.lineno(1)).add(Node("ID", p[2], line=p.lineno(2)), p[4])

def p_stmt_inc1(p):
    "stmt : INC '[' ID ']'"
    p[0] = Node("INC", line=p.lineno(1)).add(Node("ID", p[3], line=p.lineno(3)))

def p_stmt_inc2(p):
    "stmt : INC '[' ID expr ']'"
    p[0] = Node("INC", line=p.lineno(1)).add(Node("ID", p[3], line=p.lineno(3)), p[4])

# --- Posición ---
def p_stmt_pos_brackets(p):
    "stmt : PONPOS '[' expr expr ']'"
    p[0] = Node("PONPOS", line=p.lineno(1)).add(p[3], p[4])

def p_stmt_pos_xy(p):
    "stmt : PONXY expr expr"
    p[0] = Node("PONXY", line=p.lineno(1)).add(p[2], p[3])

def p_stmt_pos_x(p):
    "stmt : PONX expr"
    p[0] = Node("PONX", line=p.lineno(1)).add(p[2])

def p_stmt_pos_y(p):
    "stmt : PONY expr"
    p[0] = Node("PONY", line=p.lineno(1)).add(p[2])

# --- Rumbo / dirección ---
def p_stmt_ponrumbo(p):
    "stmt : PONRUMBO expr"
    p[0] = Node("PONRUMBO", line=p.lineno(1)).add(p[2])

def p_stmt_rumbo(p):
    "stmt : RUMBO"
    p[0] = Node("RUMBO", line=p.lineno(1))

# --- Lápiz ---
def p_stmt_bl(p):
    "stmt : BL"
    p[0] = Node("BL", line=p.lineno(1))

def p_stmt_sb(p):
    "stmt : SB"
    p[0] = Node("SB", line=p.lineno(1))

# --- Oculta tortuga ---
def p_stmt_ot(p):
    "stmt : OT"
    p[0] = Node("OT", line=p.lineno(1))

# --- Color del lápiz ---
def p_stmt_poncl_id(p):
    "stmt : PONCL ID"
    p[0] = Node("PONCL", line=p.lineno(1)).add(Node("ID", p[2], line=p.lineno(2)))

def p_stmt_poncl_str(p):
    "stmt : PONCL STRING"
    p[0] = Node("PONCL", line=p.lineno(1)).add(Node("STR", p[2], line=p.lineno(2)))

def p_stmt_poncl_str(p):
    "stmt : PONCL STRING"
    p[0] = Node("PONCL", line=p.lineno(1)).add(Node("STR", p[2], line=p.lineno(2)))

# Expresiones
def p_expr_binop(p):
    """expr : expr '+' expr
            | expr '-' expr
            | expr '*' expr
            | expr '/' expr"""
    p[0] = Node("BINOP", p[2], line=p.lineno(2)).add(p[1], p[3])

def p_expr_uminus(p):
    "expr : '-' expr %prec UMINUS"
    p[0] = Node("NEG").add(p[2])

def p_expr_group(p):
    "expr : '(' expr ')'"
    p[0] = p[2]

def p_expr_num(p):
    "expr : NUM"
    p[0] = Node("NUM", p[1], line=p.lineno(1))

def p_expr_str(p):
    "expr : STRING"
    p[0] = Node("STR", p[1], line=p.lineno(1))

def p_expr_id(p):
    "expr : ID"
    p[0] = Node("ID", p[1], line=p.lineno(1))

# Errores
def p_error(t):
    if t:
        raise SyntaxError(f"Error de sintaxis cerca de '{t.value}' (token {t.type}) en línea {t.lineno}")
    else:
        raise SyntaxError("Error de sintaxis: fin de entrada inesperado")

# Runner
def build_parser():
    lex = build_lexer()
    logger = PlyLogger(sys.stdout)
    parser = yacc.yacc(debug=False, write_tables=False, errorlog=logger)
    return parser, lex

def parse_text(text: str):
    parser, lex = build_parser()
    return parser.parse(text, lexer=lex)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m frontend.parser <archivo.logo>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()
    ast = parse_text(text)
    print(ast.pretty())
