# frontend/parser.py
from __future__ import annotations
import sys
import ply.yacc as yacc
from ply.yacc import PlyLogger

from .lexer import build_lexer, tokens
from .ast import Node

# Precedencias
precedence = (
    ('left', 'O'),
    ('left', 'Y'),
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', 'UMINUS'),
    ('nonassoc', 'IGUALES', 'MAYORQ', 'MENORQ'),
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

# --- Lista de parámetros ---
def p_param_list_one(p):
    "param_list : ID"
    p[0] = Node("PARAMS").add(Node("ID", p[1], line=p.lineno(1)))

def p_param_list_more(p):
    "param_list : param_list ID"
    p[1].add(Node("ID", p[2], line=p.lineno(2)))
    p[0] = p[1]

def p_param_list_empty(p):
    "param_list : "
    # ¡OJO!: no uses p.lineno(1) aquí porque la producción está vacía.
    p[0] = Node("PARAMS")


# --- Bloques con corchetes ---
def p_block(p):
    "block : '[' stmt_list ']'"
    p[0] = p[2]

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

def p_stmt_espera(p):
    "stmt : ESPERA expr"
    p[0] = Node("ESPERA", line=p.lineno(1)).add(p[2])

# --- Procedimiento con parámetros ---
def p_stmt_para_def_args(p):
    "stmt : PARA ID '[' param_list ']' stmt_list FIN"
    # índices: 1:PARA 2:ID 3:'[' 4:param_list 5:']' 6:stmt_list 7:FIN
    name = Node("ID", p[2], line=p.lineno(2))
    p[0] = Node("PARA", line=p.lineno(1)).add(name, p[4], p[6])

# --- Llamada a procedimiento ---
def p_stmt_proc_call_noargs(p):
    "stmt : ID"
    # llamada sin args (compatibilidad)
    p[0] = Node("CALL", line=p.lineno(1)).add(Node("ID", p[1], line=p.lineno(1)))

def p_stmt_proc_call_args(p):
    "stmt : ID '[' arg_values ']'"
    name = Node("ID", p[1], line=p.lineno(1))
    p[0] = Node("CALL", line=p.lineno(1)).add(name, p[3])

# Lista de argumentos de llamada
def p_arg_values_one(p):
    "arg_values : expr"
    p[0] = Node("ARGS").add(p[1])

def p_arg_values_more(p):
    "arg_values : arg_values expr"
    p[1].add(p[2]); p[0] = p[1]

def p_arg_values_empty(p):
    "arg_values : "
    p[0] = Node("ARGS")

def p_stmt_centro(p):
    "stmt : CENTRO"
    p[0] = Node("CENTRO", line=p.lineno(1))

# --- Control de flujo con corchetes ---
def p_stmt_ejecuta_block(p):
    "stmt : EJECUTA block"
    p[0] = Node("EJECUTA", line=p.lineno(1)).add(p[2])

def p_stmt_repite_block(p):
    "stmt : REPITE expr block"
    p[0] = Node("REPITE", line=p.lineno(1)).add(p[2], p[3])

def p_stmt_si_block(p):
    "stmt : SI bexpr block"
    p[0] = Node("SI", line=p.lineno(1)).add(p[2], p[3])

def p_stmt_mientras_block(p):
    "stmt : MIENTRAS bexpr block"
    p[0] = Node("MIENTRAS", line=p.lineno(1)).add(p[2], p[3])

def p_stmt_haz_hasta_block(p):
    "stmt : HAZ_HASTA block HASTA bexpr"
    p[0] = Node("HAZ_HASTA", line=p.lineno(1)).add(p[2], p[4])

def p_stmt_haz_mientras_block(p):
    "stmt : HAZ_MIENTRAS block MIENTRAS bexpr"
    p[0] = Node("HAZ_MIENTRAS", line=p.lineno(1)).add(p[2], p[4])

def p_stmt_si(p):
    "stmt : SI expr HAZ stmt_list FIN"
    # Nodo SI con dos hijos: condición y bloque de sentencias
    p[0] = Node("SI", line=p.lineno(1)).add(p[2], p[4])


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

"""
def p_expr_logic(p):
    """"""expr : expr Y expr
            | expr O expr""""""
    p[0] = Node("LOGIC", p[2], line=p.lineno(2)).add(p[1], p[3])
"""
def p_expr_producto(p):
    "expr : PRODUCTO expr expr"
    p[0] = Node("BINOP", '*', line=p.lineno(1)).add(p[2], p[3])

def p_expr_suma(p):
    "expr : SUMA expr expr"
    p[0] = Node("BINOP", '+', line=p.lineno(1)).add(p[2], p[3])

def p_expr_diferencia(p):
    "expr : DIFERENCIA expr expr"
    p[0] = Node("BINOP", '-', line=p.lineno(1)).add(p[2], p[3])

def p_expr_division_word(p):
    "expr : DIVISION expr expr"
    p[0] = Node("BINOP", '/', line=p.lineno(1)).add(p[2], p[3])

def p_expr_potencia(p):
    "expr : POTENCIA expr expr"
    p[0] = Node("POW", line=p.lineno(1)).add(p[2], p[3])


def p_expr_azar_uno(p):
    "expr : AZAR expr"
    p[0] = Node("CALL", "AZAR", line=p.lineno(1)).add(p[2])



# ========================
# Booleanas (bexpr)
# ========================

# Paréntesis en booleanas
def p_bexpr_paren(p):
    "bexpr : '(' bexpr ')'"
    p[0] = p[2]

# Conectores lógicos (entre booleanas)
def p_bexpr_boolbin(p):
    """bexpr : bexpr Y bexpr
             | bexpr O bexpr"""
    p[0] = Node("BOOLBIN", p[2], line=p.lineno(2)).add(p[1], p[3])

# Predicados relacionales INFJOS: a IGUALES? b, a MENORQ? b, a MAYORQ? b
def p_bexpr_rel_infix(p):
    """bexpr : expr IGUALES expr
             | expr MENORQ expr
             | expr MAYORQ expr"""
    p[0] = Node("RELOP", p[2], line=p.lineno(2)).add(p[1], p[3])

# Predicados relacionales PREFIJO: IGUALES? a b, MENORQ? a b, MAYORQ? a b
def p_bexpr_rel_prefix_eq(p):
    "bexpr : IGUALES expr expr"
    p[0] = Node("RELOP", 'IGUALES', line=p.lineno(1)).add(p[2], p[3])

def p_bexpr_rel_prefix_lt(p):
    "bexpr : MENORQ expr expr"
    p[0] = Node("RELOP", 'MENORQ', line=p.lineno(1)).add(p[2], p[3])

def p_bexpr_rel_prefix_gt(p):
    "bexpr : MAYORQ expr expr"
    p[0] = Node("RELOP", 'MAYORQ', line=p.lineno(1)).add(p[2], p[3])




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
