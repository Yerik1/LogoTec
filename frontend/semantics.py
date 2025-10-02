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

def check_stmt(n: Node, st: Symtab, di: Diagnostics):
    k = n.kind
    if k in ("AV", "RE", "GD", "GI"):
        t = type_of_expr(n.children[0], st, di)
        if t != "int":
            di.error(n.line, f"{k} requiere una expresión numérica")
    elif k == "INIC":
        ident = n.children[0]  # Node("ID", name)
        expr = n.children[1]
        t = type_of_expr(expr, st, di)
        # Para entrega 1, permitimos tipado por primera asignación (int/unknown)
        if t == "unknown":
            di.warn(expr.line, f"No se puede inferir tipo de la expresión para '{ident.value}'")
        st.set_var(str(ident.value), "int" if t == "int" else "unknown")
    elif k == "INC":
        ident = n.children[0]
        name = str(ident.value)
        ty = st.get_var(name)
        if ty is None:
            di.error(ident.line, f"Variable '{name}' no declarada antes de INC")
        elif ty != "int":
            di.error(ident.line, f"INC requiere variable numérica: '{name}'")
        # si tiene delta, que sea numérico
        if len(n.children) == 2:
            t = type_of_expr(n.children[1], st, di)
            if t != "int":
                di.error(n.children[1].line, "El incremento de INC debe ser numérico")
    elif k in ("STMTS", "PROGRAM"):
        for c in n.children:
            check_stmt(c, st, di)

    elif k in ("PONPOS", "PONXY"):
        # dos expr numéricas
        x_t = type_of_expr(n.children[0], st, di)
        y_t = type_of_expr(n.children[1], st, di)
        if x_t != "int" or y_t != "int":
            di.error(n.line, f"{k} requiere coordenadas numéricas (X,Y)")

    elif k in ("PONX", "PONY", "PONRUMBO"):
        t = type_of_expr(n.children[0], st, di)
        if t != "int":
            di.error(n.line, f"{k} requiere un valor numérico")

    elif k in ("BL", "SB", "OT", "RUMBO"):
        # No requieren expresiones; no hacemos nada semántico aquí.
        pass

    elif k == "PONCL":
        # Aceptamos ID o STR como nombre de color (no tipamos en entrega 1)
        # Si quisieras restringir: podrías advertir cuando no sea STR ni ID.
        if n.children:
            c = n.children[0]
            if c.kind not in ("ID", "STR"):
                di.warn(n.line, "PONCL espera un nombre de color o cadena")

    elif k == "SI":
        cond = n.children[0]
        body = n.children[1]

        # Revisar que la condición sea numérica
        t = type_of_expr(cond, st, di)
        if t != "int":
            di.error(cond.line, "La condición de 'si' debe ser una expresión numérica")

        # Revisar el bloque de sentencias
        check_stmt(body, st, di)

    # Los demás nodos (`ID`, `NUM`, `BINOP`, etc.) se validan cuando aparecen en contexto.

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
