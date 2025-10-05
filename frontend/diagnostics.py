# frontend/diagnostics.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class Diag:
    level: str   # "ERROR" | "WARN" | "INFO"
    line: int
    msg: str

class Diagnostics:
    def __init__(self) -> None:
        self.items: List[Diag] = []

    def error(self, line: int, msg: str):
        self.items.append(Diag("ERROR", line, msg))

    def warn(self, line: int, msg: str):
        self.items.append(Diag("WARN", line, msg))

    def info(self, line: int, msg: str):
        self.items.append(Diag("INFO", line, msg))

    def has_errors(self) -> bool:
        return any(d.level == "ERROR" for d in self.items)

    def pretty(self) -> str:
        if not self.items:
            return "Sin diagnósticos."
        return "\n".join(f"[{d.level}] (línea {d.line}) {d.msg}" for d in self.items)
