# frontend/semantics.py
from __future__ import annotations
from typing import Dict, Literal, Optional
from .ast import Node
from .diagnostics import Diagnostics

Type = Literal["int","bool", "unknown"]  # por ahora solo numéricos (entrega 1)

class Symtab:
    def __init__(self) -> None:
        self.vars: list[dict[str, str]] = [{}]  # nombre -> tipo
        self.procs: dict[str, int] = {}

    def push(self):
        self.vars.append({})

    def pop(self):
        if len(self.vars) > 1:
            self.vars.pop()

    def set_var(self, name: str, ty: str):
        self.vars[-1][name] = ty

    def get_var(self, name: str) -> str | None:
        for scope in reversed(self.vars):
            if name in scope:
                return scope[name]
        return None

    def set_proc(self, name: str, arity: int):
        self.procs[name] = arity

    def get_proc_arity(self, name: str) -> int | None:
        return self.procs.get(name)

def type_of_bexpr(n: Node, st: Symtab, di: Diagnostics) -> Type:
    if n.kind == "RELOP":
        if len(n.children) != 2:
            di.error(n.line, f"{n.value} requiere 2 operandos")
            return "unknown"
        lt = type_of_expr(n.children[0], st, di)
        rt = type_of_expr(n.children[1], st, di)
        if lt != "int" or rt != "int":
            di.error(n.line, f"{n.value} requiere operandos numéricos")
            return "unknown"
        return "bool"
    if n.kind == "BOOLBIN":
        if len(n.children) != 2:
            di.error(n.line, f"Operador lógico '{n.value}' requiere 2 operandos")
            return "unknown"
        lt = type_of_bexpr(n.children[0], st, di)
        rt = type_of_bexpr(n.children[1], st, di)
        if lt != "bool" or rt != "bool":
            di.error(n.line, f"Operador lógico '{n.value}' requiere booleanos")
            return "unknown"
        return "bool"
    # Paréntesis u otros
    if n.kind not in ("PROGRAM","STMTS"):
        di.warn(n.line, f"Expresión booleana desconocida de tipo '{n.kind}'")
    return "unknown"

def type_of_expr(n: Node, st: Symtab, di: Diagnostics) -> Type:
    if n.kind == "NUM":
        return "int"
    if n.kind == "STR":
        return "unknown"
    if n.kind == "ID":
        ty = st.get_var(str(n.value))
        return ty or "unknown"
    if n.kind == "NEG":
        if not n.children:
            di.error(n.line, "Operador unario sin operando")
            return "unknown"
        return type_of_expr(n.children[0], st, di)
    if n.kind == "BINOP":
        if len(n.children) != 2:
            di.error(n.line, f"Operación '{n.value}' requiere 2 operandos")
            return "unknown"
        lt = type_of_expr(n.children[0], st, di)
        rt = type_of_expr(n.children[1], st, di)
        if lt != "int" or rt != "int":
            di.error(n.line, f"Operación '{n.value}' requiere operandos numéricos")
            return "unknown"
        return "int"
    if n.kind == "POW":
        if len(n.children) != 2:
            di.error(n.line, "POTENCIA requiere 2 operandos")
            return "unknown"
        lt = type_of_expr(n.children[0], st, di)
        rt = type_of_expr(n.children[1], st, di)
        if lt != "int" or rt != "int":
            di.error(n.line, "POTENCIA requiere operandos numéricos")
            return "unknown"
        return "int"
    if n.kind == "CALL":
        op = n.value
        if op == "AZAR":
            if len(n.children) != 1:
                di.error(n.line, "AZAR requiere 1 argumento numérico")
                return "unknown"
            t = type_of_expr(n.children[0], st, di)
            return "int" if t == "int" else "unknown"
        if op in ("PRODUCTO", "POTENCIA", "DIVISION", "SUMA", "DIFERENCIA"):
            if len(n.children) != 2:
                di.error(n.line, f"{op} requiere 2 operandos")
                return "unknown"
            lt = type_of_expr(n.children[0], st, di)
            rt = type_of_expr(n.children[1], st, di)
            if lt != "int" or rt != "int":
                di.error(n.line, f"{op} requiere operandos numéricos")
                return "unknown"
            return "int"
        # Si es una llamada a procedimiento (stmt : ID), aquí no debería entrar
        # (solo aparece como stmt). Devolvemos unknown por si aparece en expr.
        return "unknown"

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
        tb = type_of_bexpr(n.children[0], st, di)
        if tb != "bool":
            di.error(n.line, "La condición de 'SI' debe ser booleana")
        check_stmt(n.children[1], st, di)

    # Bucles
    elif k == "PARA":
        if len(n.children) < 3 or n.children[1].kind != "PARAMS" or n.children[2].kind != "STMTS":
            di.error(n.line, "Definición de procedimiento inválida")
        else:
            name_node = n.children[0]  # ID(nombre)
            params = n.children[1].children  # lista de IDs
            body = n.children[2]

            # Registrar procedimiento y su aridad
            proc_name = str(name_node.value)
            arity = sum(1 for p in params if p.kind == "ID")
            st.set_proc(proc_name, arity)

            # Scope para params (tipo int en esta entrega)
            st.push()
            for pid in params:
                if pid.kind == "ID":
                    st.set_var(str(pid.value), "int")

            check_stmt(body, st, di)
            st.pop()


    elif k == "MIENTRAS":
        tb = type_of_bexpr(n.children[0], st, di)
        if tb != "bool":
            di.error(n.line, "La condición de MIENTRAS debe ser booleana")
        check_stmt(n.children[1], st, di)

    elif k == "HAZ":
        ident = n.children[0]  # Node("ID", nombre)
        expr = n.children[1]
        t = type_of_expr(expr, st, di)
        if t == "unknown":
            di.warn(expr.line, f"No se puede inferir tipo de la expresión para '{ident.value}'")
        st.set_var(str(ident.value), "int" if t == "int" else "unknown")

    elif k == "HAZ_HASTA":
        check_stmt(n.children[0], st, di)  # bloque
        tb = type_of_bexpr(n.children[1], st, di)
        if tb != "bool":
            di.error(n.line, "La condición de HASTA debe ser booleana")


    elif k == "HAZ_MIENTRAS":
        check_stmt(n.children[0], st, di)
        tb = type_of_bexpr(n.children[1], st, di)
        if tb != "bool":
            di.error(n.line, "La condición de MIENTRAS debe ser booleana")


    elif k == "REPITE":
        t = type_of_expr(n.children[0], st, di)
        if t != "int":
            di.error(n.line, "REPITE requiere una expresión numérica para el conteo")
        check_stmt(n.children[1], st, di)

    # Temporización / procedimientos
    elif k == "ESPERA":
        t = type_of_expr(n.children[0], st, di)
        if t != "int":
            di.error(n.line, "ESPERA requiere un valor numérico")


    elif k == "EJECUTA":
        if not n.children:
            di.error(n.line, "EJECUTA requiere un bloque o un identificador")
        else:
            ident = n.children[0]
            if ident.kind == "ID":
                # Llamada a procedimiento por nombre → aceptada
                pass
            elif ident.kind == "STMTS":
                # Bloque de sentencias → validar su contenido
                check_stmt(ident, st, di)
            else:
                di.error(ident.line or n.line, "EJECUTA requiere un bloque [...] o un identificador de procedimiento")


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


    elif k == "CALL":
        # hijos: [ ID(nombre) ] o [ ID(nombre), ARGS(...) ]
        if not n.children:
            di.error(n.line, "Llamada inválida")
        else:
            name_node = n.children[0]
            if name_node.kind != "ID":
                di.error(n.line, "Llamada inválida: falta nombre de procedimiento")
            else:
                pname = str(name_node.value)
                declared_arity = st.get_proc_arity(pname)
                # si no está declarado, en esta entrega no rechazamos, solo avisamos (opcional)
                if declared_arity is None:
                    # di.warn(n.line, f"Procedimiento '{pname}' no declarado")
                    pass
                else:
                    # contar args reales (si hay ARGS)
                    passed_arity = 0
                    if len(n.children) >= 2 and n.children[1].kind == "ARGS":
                        passed_arity = len(n.children[1].children)
                        # tipar cada arg como expr numérica (esta entrega)
                        for arg in n.children[1].children:
                            if type_of_expr(arg, st, di) != "int":
                                di.error(arg.line, f"Argumento no numérico en llamada a '{pname}'")
                    if passed_arity != declared_arity:
                        di.error(n.line,
                                 f"Llamada a '{pname}' con {passed_arity} argumento(s); se esperaban {declared_arity}")
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
