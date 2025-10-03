# frontend/ast_viewer_tk.py
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -----------------------------------------------------------
# Modelo y utilidades
# -----------------------------------------------------------
@dataclass
class JNode:
    kind: str
    value: Any
    line: int
    children: List["JNode"] = field(default_factory=list)
    collapsed: bool = False
    # layout
    x: float = 0
    y: float = 0
    # canvas item ids (para click/colapso)
    item_rect: Optional[int] = None
    item_text: Optional[int] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "JNode":
        ch = [JNode.from_dict(c) for c in (d.get("children") or [])]
        return JNode(kind=d.get("kind","?"),
                     value=d.get("value"),
                     line=int(d.get("line") or 0),
                     children=ch)

    def label(self) -> str:
        if self.value is None or self.value == "":
            return self.kind
        if self.kind == "STR":
            return f'{self.kind} · "{self.value}"'
        return f"{self.kind} · {self.value}"

# -----------------------------------------------------------
# Layout (postorden sencillo tipo “tidy”)
# -----------------------------------------------------------
class TreeLayout:
    def __init__(self, x_gap=90, y_gap=90, font_px=12, min_w=56, char_px=7):
        self.x_gap = x_gap
        self.y_gap = y_gap
        self.font_px = font_px
        self.min_w = min_w
        self.char_px = char_px
        self._cursor_x = 0  # posición x “hojas” en postorden

    def node_width(self, node: JNode) -> int:
        text = node.label()
        return max(self.min_w, 20 + len(text) * self.char_px)

    def layout(self, root: JNode) -> None:
        self._cursor_x = 0
        self._assign_xy(root, depth=0)

    def _assign_xy(self, n: JNode, depth: int) -> float:
        if n.collapsed or not n.children:
            # hoja (o colapsado): posición en cursor
            x = self._cursor_x * self.x_gap
            self._cursor_x += 1
        else:
            xs = [self._assign_xy(c, depth+1) for c in n.children]
            x = sum(xs) / len(xs)
        n.x = x
        n.y = depth * self.y_gap
        return x

# -----------------------------------------------------------
# Color por tipo
# -----------------------------------------------------------
def kind_color(kind: str) -> str:
    palette = {
        "PROGRAM":"#2563EB", "STMTS":"#0EA5E9",
        "INIC":"#16A34A", "INC":"#16A34A",
        "AV":"#7C3AED", "RE":"#7C3AED",
        "GD":"#EA580C", "GI":"#EA580C",
        "PONPOS":"#0891B2", "PONXY":"#0891B2", "PONX":"#0891B2", "PONY":"#0891B2",
        "PONRUMBO":"#F59E0B", "RUMBO":"#F59E0B",
        "BL":"#475569", "SB":"#475569", "OT":"#475569", "PONCL":"#E11D48",
        "ESPERA":"#06B6D4",
        "NUM":"#64748B", "ID":"#64748B", "STR":"#64748B",
        "BINOP":"#22C55E", "NEG":"#22C55E", "CALL":"#22C55E",
    }
    return palette.get(kind, "#334155")

# -----------------------------------------------------------
# Viewer Tkinter
# -----------------------------------------------------------
class AstViewer(tk.Toplevel):
    def __init__(self, master=None, json_path: Optional[str]=None):
        super().__init__(master)
        self.title("AST Viewer")
        self.geometry("980x680")
        self.configure(bg="#0B1220")

        # Top bar
        bar = ttk.Frame(self)
        bar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        self.btn_open = ttk.Button(bar, text="Abrir ast.json", command=self.open_json_dialog)
        self.btn_open.pack(side=tk.LEFT)

        self.btn_reset = ttk.Button(bar, text="Re-centrar", command=self.reset_view)
        self.btn_reset.pack(side=tk.LEFT, padx=6)

        ttk.Label(bar, text="Zoom: Ctrl + rueda | Pan: arrastrar").pack(side=tk.LEFT, padx=12)

        # Scrollable canvas
        wrap = ttk.Frame(self)
        wrap.pack(fill=tk.BOTH, expand=True)

        self.hbar = ttk.Scrollbar(wrap, orient=tk.HORIZONTAL)
        self.vbar = ttk.Scrollbar(wrap, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(
            wrap, bg="#0F172A",
            xscrollcommand=self.hbar.set,
            yscrollcommand=self.vbar.set,
            highlightthickness=0
        )
        self.hbar.config(command=self.canvas.xview)
        self.vbar.config(command=self.canvas.yview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        # eventos
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_move)
        self.canvas.bind("<MouseWheel>", self._on_zoom)          # Windows
        self.canvas.bind("<Button-4>", self._on_zoom)            # Linux up
        self.canvas.bind("<Button-5>", self._on_zoom)            # Linux down

        # datos
        self.root_node: Optional[JNode] = None
        self.layout_engine = TreeLayout()
        self.scale = 1.0
        self._pan_start: Optional[Tuple[int,int]] = None

        if json_path:
            self.load_json(json_path)

    # ---------- IO ----------
    def open_json_dialog(self):
        path = filedialog.askopenfilename(
            title="Abrir ast.json",
            filetypes=[("JSON","*.json"), ("Todos","*.*")]
        )
        if path:
            self.load_json(path)

    def load_json(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.root_node = JNode.from_dict(data)
            self.redraw()
            self.reset_view()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir JSON:\n{e}")

    # ---------- Dibujo ----------
    def redraw(self):
        self.canvas.delete("all")
        if not self.root_node:
            return
        # layout
        self.layout_engine.layout(self.root_node)

        # dibujar edges primero
        self._draw_edges(self.root_node)
        # dibujar nodos encima
        self._draw_nodes(self.root_node)

        # ajustar scrollregion
        bb = self.canvas.bbox("all")
        if bb:
            pad = 80
            self.canvas.config(scrollregion=(bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad))

    def _draw_edges(self, n: JNode):
        if n.collapsed:
            return
        for c in n.children:
            # línea “suave”: recta por simplicidad (Canvas no tiene bézier nativo)
            self.canvas.create_line(
                n.x, n.y, c.x, c.y,
                fill="#CBD5E1", width=1.2, tags=("edge",)
            )
            self._draw_edges(c)

    def _draw_nodes(self, n: JNode):
        # rect + texto
        label = n.label()
        w = self.layout_engine.node_width(n)
        h = 28
        x0, y0 = n.x - w/2, n.y - h/2
        x1, y1 = n.x + w/2, n.y + h/2

        fill = "#0B1220" if n.children else "#0F172A"
        border = kind_color(n.kind)
        text_color = border

        rect = self.canvas.create_rectangle(
            x0, y0, x1, y1,
            fill=fill, outline=border, width=2,
            tags=("node","rect")
        )
        text = self.canvas.create_text(
            n.x, n.y,
            text=label, fill=text_color, font=("Segoe UI", 10),
            tags=("node","label")
        )
        # guardar ids para hit-test
        n.item_rect = rect
        n.item_text = text

        # tooltip simple con línea
        self.canvas.tag_bind(rect, "<Enter>", lambda e, n=n: self._show_status(n))
        self.canvas.tag_bind(text, "<Enter>", lambda e, n=n: self._show_status(n))
        self.canvas.tag_bind(rect, "<Leave>", lambda e: self._show_status(None))
        self.canvas.tag_bind(text, "<Leave>", lambda e: self._show_status(None))

        # click para colapsar/expandir
        self.canvas.tag_bind(rect, "<Button-1>", lambda e, n=n: self._toggle(n))
        self.canvas.tag_bind(text, "<Button-1>", lambda e, n=n: self._toggle(n))

        if not n.collapsed:
            for c in n.children:
                self._draw_nodes(c)

    def _show_status(self, n: Optional[JNode]):
        if n is None:
            self.title("AST Viewer")
        else:
            self.title(f"AST Viewer — {n.kind}"
                       + (f" ({n.value})" if n.value not in (None,"") else "")
                       + (f"  ·  línea {n.line}" if n.line else ""))

    def _toggle(self, n: JNode):
        n.collapsed = not n.collapsed
        self.redraw()

    # ---------- Interacción ----------
    def reset_view(self):
        self.scale = 1.0
        self.canvas.scale("all", 0, 0, 1.0, 1.0)
        self.canvas.xview_moveto(0.0)
        self.canvas.yview_moveto(0.0)

    def _on_pan_start(self, ev):
        self._pan_start = (ev.x, ev.y)

    def _on_pan_move(self, ev):
        if not self._pan_start:
            return
        dx = ev.x - self._pan_start[0]
        dy = ev.y - self._pan_start[1]
        self._pan_start = (ev.x, ev.y)
        self.canvas.xview_scroll(int(-dx/2), "units")
        self.canvas.yview_scroll(int(-dy/2), "units")

    def _on_zoom(self, ev):
        # Ctrl + rueda para zoom (sin Ctrl, ignora)
        state = ev.state
        ctrl_down = (state & 0x0004) != 0  # mask de Ctrl en Tk
        if not ctrl_down:
            return
        factor = 1.1 if (getattr(ev, "delta", 0) > 0 or getattr(ev, "num", None) == 4) else 1/1.1
        self.scale *= factor
        self.canvas.scale("all", self.canvas.canvasx(ev.x), self.canvas.canvasy(ev.y), factor, factor)
        # actualizar scrollregion
        bb = self.canvas.bbox("all")
        if bb:
            self.canvas.config(scrollregion=bb)

# -----------------------------------------------------------
# Standalone runner
# -----------------------------------------------------------
def open_ast_window(json_path: Optional[str] = "out/ast.json"):
    root = tk.Tk()
    root.withdraw()  # solo mostramos la ventana del viewer
    AstViewer(root, json_path=json_path)
    root.mainloop()

if __name__ == "__main__":
    open_ast_window()
