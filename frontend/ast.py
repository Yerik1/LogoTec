# frontend/ast.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class Node:
    kind: str
    value: Any = None
    children: List["Node"] = field(default_factory=list)
    line: int = 0

    def add(self, *nodes: "Node"):
        for n in nodes:
            if n is not None:
                self.children.append(n)
        return self

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        head = f"{pad}{self.kind}"
        if self.value is not None:
            head += f"({self.value})"
        lines = [head]
        for c in self.children:
            lines.append(c.pretty(indent + 1))
        return "\n".join(lines)
