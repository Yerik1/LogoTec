# frontend/exporter.py
from __future__ import annotations
import json
import os
from typing import Any, Dict
from .ast import Node
from .diagnostics import Diagnostics

def ast_to_dict(n: Node) -> Dict[str, Any]:
    return {
        "kind": n.kind,
        "value": n.value,
        "line": n.line,
        "children": [ast_to_dict(c) for c in n.children],
    }

def save_ast_json(root: Node, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ast_to_dict(root), f, ensure_ascii=False, indent=2)

def save_diags_txt(diags: Diagnostics, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if not diags.items:
            f.write("Sin diagnósticos.\n")
        else:
            for d in diags.items:
                f.write(f"[{d.level}] (línea {d.line}) {d.msg}\n")
