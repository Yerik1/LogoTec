# frontend/semantics.py
from __future__ import annotations
from typing import Dict, Literal, Optional
from .ast import Node
from .diagnostics import Diagnostics

Type = Literal["int", "unknown"]  # por ahora solo numéricos (entrega 1)

class Symtab:
    def __init__(self) -> None:
        self.vars: Dict[str, Type] = {}  # nombre -> tipo

    def set_var(self, name: str, ty: Type):
        self.vars[name] = ty

    def get_var(self, name: str) -> Optional[Type]:
        return self.vars.get(name, None)

def type_of_expr(n: Node, st: Symtab, di: Diagnostics) -> Type:
    """Inferencia simple de tipos para expresiones."""
    if n.kind == "NUM":
        return "int"
    if n.kind == "STR":
        return "unknown"
    if n.kind == "ID":
        ty = st.get_var(str(n.value))
        return ty or "unknown"
    if n.kind == "NEG":
        return type_of_expr(n.children[0], st, di)
    if n.kind == "BINOP":
        lt = type_of_expr(n.children[0], st, di)
        rt = type_of_expr(n.children[1], st, di)
        # Por ahora, exigimos numéricos; si no, marcamos unknown.
        if lt != "int" or rt != "int":
            di.error(n.line, f"Operación '{n.value}' requiere operandos numéricos")
            return "unknown"
        return "int"
    # fallback
    return "unknown"

def check_stmt(n, st, di):
    k = n.kind

    # Bloques de sentencias
    if k in ("STMTS", "PROGRAM"):
        for c in n.children:
            check_stmt(c, st, di)

    # Declaración con inicialización
    elif k == "INIC":
        ident = n.children[0]  # Node("ID", nombre)
        expr = n.children[1]
        t = type_of_expr(expr, st, di)
        if t == "unknown":
            di.warn(expr.line, f"No se puede inferir tipo de la expresión para '{ident.value}'")
        st.set_var(str(ident.value), "int" if t == "int" else "unknown")

    # Incremento
    elif k == "INC":
        ident = n.children[0]
        name = str(ident.value)
        ty = st.get_var(name)
        if ty is None:
            di.error(ident.line, f"Variable '{name}' no declarada antes de INC")
        elif ty != "int":
            di.error(ident.line, f"INC requiere variable numérica: '{name}'")
        if len(n.children) == 2:
            t = type_of_expr(n.children[1], st, di)
            if t != "int":
                di.error(n.children[1].line, "El incremento de INC debe ser numérico")

    # Posiciones
    elif k in ("PONPOS", "PONXY"):
        tx = type_of_expr(n.children[0], st, di)
        ty = type_of_expr(n.children[1], st, di)
        if tx != "int" or ty != "int":
            di.error(n.line, "Las coordenadas deben ser numéricas")

    elif k in ("PONX", "PONY", "PONRUMBO"):
        t = type_of_expr(n.children[0], st, di)
        if t != "int":
            di.error(n.line, f"{k} requiere un valor numérico")

    # Movimiento / rotaciones
    elif k in ("AV", "RE", "GD", "GI"):
        t = type_of_expr(n.children[0], st, di)
        if t != "int":
            di.error(n.line, f"{k} requiere una expresión numérica")

    # Lápiz y pantalla
    elif k in ("BL", "SB", "OT", "RUMBO", "CENTRO"):
        pass  # no requieren validación adicional

    elif k == "PONCL":
        if n.children:
            c = n.children[0]
            if c.kind not in ("ID", "STR"):
                di.warn(n.line, "PONCL espera un nombre de color o cadena")

    # Condicional simple
    elif k == "SI":
        cond = n.children[0]
        body = n.children[1]
        t = type_of_expr(cond, st, di)
        if t != "int":
            di.error(cond.line, "La condición de 'SI' debe ser una expresión numérica")
        check_stmt(body, st, di)

    # Bucles
    elif k == "PARA":
        ident = n.children[0]
        ini = n.children[1]
        fin = n.children[2]
        body = n.children[3]
        ti = type_of_expr(ini, st, di)
        tf = type_of_expr(fin, st, di)
        if ti != "int" or tf != "int":
            di.error(n.line, "El rango de PARA debe ser numérico")
        st.set_var(str(ident.value), "int")
        check_stmt(body, st, di)

    elif k == "MIENTRAS":
        cond = n.children[0]
        body = n.children[1]
        t = type_of_expr(cond, st, di)
        if t != "int":
            di.error(cond.line, "La condición de MIENTRAS debe ser numérica")
        check_stmt(body, st, di)

    elif k == "HAZ_HASTA":
        body = n.children[0]
        cond = n.children[1]
        t = type_of_expr(cond, st, di)
        if t != "int":
            di.error(cond.line, "La condición de HAZ HASTA debe ser numérica")
        check_stmt(body, st, di)

    elif k == "HAZ_MIENTRAS":
        body = n.children[0]
        cond = n.children[1]
        t = type_of_expr(cond, st, di)
        if t != "int":
            di.error(cond.line, "La condición de HAZ MIENTRAS debe ser numérica")
        check_stmt(body, st, di)

    elif k == "REPITE":
        count = n.children[0]
        body = n.children[1]
        t = type_of_expr(count, st, di)
        if t != "int":
            di.error(count.line, "REPITE requiere un número de repeticiones")
        check_stmt(body, st, di)

    # Temporización / procedimientos
    elif k == "ESPERA":
        t = type_of_expr(n.children[0], st, di)
        if t != "int":
            di.error(n.line, "ESPERA requiere un valor numérico")

    elif k == "EJECUTA":
        ident = n.children[0]
        if ident.kind != "ID":
            di.error(ident.line, "EJECUTA requiere un identificador de procedimiento")

    # Operadores aritméticos como palabras clave
    elif k in ("PRODUCTO", "POTENCIA", "DIVISION", "SUMA", "DIFERENCIA", "AZAR"):
        for c in n.children:
            t = type_of_expr(c, st, di)
            if t != "int":
                di.error(c.line, f"{k} requiere operandos numéricos")

    # Operadores lógicos / comparaciones
    elif k in ("IGUALES", "MAYORQ", "MENORQ", "Y", "O"):
        lt = type_of_expr(n.children[0], st, di)
        rt = type_of_expr(n.children[1], st, di)
        if lt != "int" or rt != "int":
            di.error(n.line, f"{k} requiere operandos numéricos")

    else:
        di.error(n.line, f"Instrucción no reconocida: {k}")


def analyze(root: Node) -> Diagnostics:
    di = Diagnostics()
    st = Symtab()
    check_stmt(root, st, di)
    return di

# Runner opcional: python -m frontend.semantics <archivo.logo>
if __name__ == "__main__":
    import sys
    from .parser import parse_text
    from .exporter import save_ast_json, save_diags_txt

    if len(sys.argv) != 2:
        print("Uso: python -m frontend.semantics <archivo.logo>")
        sys.exit(1)

    src_path = sys.argv[1]
    with open(src_path, "r", encoding="utf-8") as f:
        text = f.read()

    ast = parse_text(text)
    diags = analyze(ast)

    # Salida en consola (como antes)
    print(ast.pretty())
    print("\n-- Diagnósticos --")
    print(diags.pretty())

    # Salidas para la GUI
    save_ast_json(ast, "out/ast.json")
    save_diags_txt(diags, "out/diagnostics.txt")
