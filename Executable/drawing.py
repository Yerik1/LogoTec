# drawing.py — modo standalone o embebido (canvas externo)
import sys, math, tkinter as tk, queue, threading, time
from pathlib import Path

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

_EMBED_SERVER = None
_EMBED_ADDR = None
_EMBED_PORT = None
_EMBED_TURTLE = None

W, H = 800, 600
SPEED_PX_PER_SEC = 75.0
TURN_DEG_PER_SEC = 180.0
FRAME_MS = 16

def reader_thread(target_queue: "queue.Queue[str]"):
    for line in sys.stdin:
        s = line.strip()
        if s:
            target_queue.put(s)

def find_sprite():
    base = Path(__file__).resolve().parent
    for p in [
        base / "turtle.png",
        base / "Images" / "turtle.png",
        base.parent / "Images" / "turtle.png",
        Path.cwd() / "turtle.png",
        Path.cwd() / "Images" / "turtle.png",
    ]:
        if p.exists():
            return p
    return None

SPRITE_PATH = find_sprite()

class Turtle:
    def __init__(self, canvas: tk.Canvas | None = None):
        # embebido: canvas externo; standalone: crea ventana nueva
        if canvas is None:
            self.r = tk.Tk()
            self.r.title("Tortuga (standalone)")
            self.c = tk.Canvas(self.r, width=W, height=H, bg="white")
            self.c.pack(fill="both", expand=True)
            self.own_window = True
        else:
            self.c = canvas
            self.r = self.c.winfo_toplevel()
            self.own_window = False

        try:
            self.W, self.H = int(self.c["width"]), int(self.c["height"])
        except Exception:
            self.W, self.H = W, H

        self.x, self.y, self.h = self.W / 2, self.H / 2, 0.0
        self.pen = True
        self.color = "black"

        self._sprite_visible = True
        self._sprite_id = None
        self.base_img = None
        self.turtle_img = None
        self._sprite_mode = "triangle"
        self.cmd_q = queue.Queue()

        # cargar sprite
        if HAS_PIL and SPRITE_PATH:
            try:
                img = Image.open(str(SPRITE_PATH)).convert("RGBA")
                img = img.resize((20, 20), Image.LANCZOS)
                img = img.rotate(-90, expand=True)
                self.base_img = img
                self.turtle_img = ImageTk.PhotoImage(self.base_img)
                self._sprite_id = self.c.create_image(self.x, self.y, image=self.turtle_img)
                self._sprite_mode = "image"
            except Exception:
                self._sprite_id = self.c.create_polygon(
                    self._triangle_points(), fill="#2b6cb0", outline="#1a365d", width=1
                )
        else:
            self._sprite_id = self.c.create_polygon(
                self._triangle_points(), fill="#2b6cb0", outline="#1a365d", width=1
            )

        # overlay rumbo
        self.heading_text = self.c.create_text(
            70, 20, text="", fill="gray15", font=("Consolas", 10, "bold"), state="hidden"
        )
        self._ensure_sprite()

    def _triangle_points(self, size=12.0):
        a = size
        local = [(a, 0.0), (-0.8*a, -0.6*a), (-0.8*a, 0.6*a)]
        rad = math.radians(self.h)
        ch, sh = math.cos(rad), math.sin(rad)
        pts = []
        for px, py in local:
            wx = self.x + (px*ch - py*sh)
            wy = self.y - (px*sh + py*ch)
            pts.extend([wx, wy])
        return pts

    def _ensure_sprite(self):
        if self._sprite_mode == "image" and self.base_img is not None:
            rotated = self.base_img.rotate(self.h, resample=Image.BICUBIC, expand=True)
            self.turtle_img = ImageTk.PhotoImage(rotated)
            self.c.itemconfigure(self._sprite_id, image=self.turtle_img)
            self.c.coords(self._sprite_id, self.x, self.y)
        else:
            self.c.coords(self._sprite_id, *self._triangle_points())
        self.c.itemconfigure(self._sprite_id, state="normal" if self._sprite_visible else "hidden")

    def _draw_to(self, nx, ny):
        if self.pen:
            self.c.create_line(self.x, self.y, nx, ny, width=2, fill=self.color)
        self.x, self.y = nx, ny
        self._ensure_sprite()

    def move_step(self, d):
        nx = self.x + d * math.cos(math.radians(self.h))
        ny = self.y - d * math.sin(math.radians(self.h))
        self._draw_to(nx, ny)

    def turn_step(self, deg):
        self.h = (self.h + deg) % 360.0
        self._ensure_sprite()

    def reset(self):
        # 1) borrar sprite y canvas
        if getattr(self, "_sprite_id", None) is not None:
            try:
                self.c.delete(self._sprite_id)
            except Exception:
                pass
            self._sprite_id = None

        self.c.delete("all")
        self.c.update_idletasks()

        # 2) soltar referencias a imagen para evitar "fantasma"
        self.turtle_img = None

        # 3) estado base
        self.x, self.y, self.h = self.W / 2, self.H / 2, 0.0
        self.pen = False
        self.color = "black"
        self._sprite_visible = True

        # 4) overlays
        self.heading_text = self.c.create_text(
            70, 20, text="", fill="gray15", font=("Consolas", 10, "bold"), state="hidden"
        )

        # 5) recrear sprite (imagen si hay base, si no triángulo)
        try:
            from PIL import ImageTk, Image  # por si el archivo también corre sin PIL
            if getattr(self, "base_img", None) is not None:
                rotated = self.base_img.rotate(self.h, resample=Image.BICUBIC, expand=True)
                self.turtle_img = ImageTk.PhotoImage(rotated)
                self._sprite_id = self.c.create_image(self.x, self.y, image=self.turtle_img)
                self._sprite_mode = "image"
            else:
                self._sprite_id = self.c.create_polygon(
                    self._triangle_points(), fill="#2b6cb0", outline="#1a365d", width=1
                )
                self._sprite_mode = "triangle"
        except Exception:
            self._sprite_id = self.c.create_polygon(
                self._triangle_points(), fill="#2b6cb0", outline="#1a365d", width=1
            )
            self._sprite_mode = "triangle"

        self._ensure_sprite()

    # instantáneos
    def set_heading(self, deg): self.h = deg % 360.0; self._ensure_sprite()
    def set_pos(self, x, y):    self.x, self.y = float(x), float(y); self._ensure_sprite()
    def set_x(self, x):         self.x = float(x); self._ensure_sprite()
    def set_y(self, y):         self.y = float(y); self._ensure_sprite()
    def penup(self):            self.pen = True
    def pendown(self):          self.pen = False
    def hide(self):             self._sprite_visible = False; self._ensure_sprite()
    def show(self):             self._sprite_visible = True;  self._ensure_sprite()
    def set_color(self, c):
        palette = {0:"black",1:"red",2:"blue",3:"green",4:"orange",5:"purple"}
        self.color = palette.get(int(c), "black")
    def set_color_name(self, name):
        m = {"negro":"black","black":"black","rojo":"red","red":"red",
             "verde":"green","green":"green","azul":"blue","blue":"blue",
             "naranja":"orange","orange":"orange","morado":"purple","purple":"purple"}
        self.color = m.get(name.lower(), "black")
    def center(self): self.x, self.y = self.W/2, self.H/2; self._ensure_sprite()

def start_embed_server(canvas, host="127.0.0.1", port=0):
    """Inicia (o reutiliza) un servidor TCP que llena la cola de la tortuga embebida."""
    import socketserver, threading

    global _EMBED_SERVER, _EMBED_ADDR, _EMBED_PORT, _EMBED_TURTLE

    # Si ya está corriendo, no crees otra instancia: resetea y devuelve el mismo puerto
    if _EMBED_SERVER is not None and _EMBED_TURTLE is not None:
        # asegurar que seguimos dibujando en el canvas actual
        if _EMBED_TURTLE.c is not canvas:
            # si cambiaron el canvas, reasigna y resetea
            _EMBED_TURTLE.c = canvas
            _EMBED_TURTLE.r = canvas.winfo_toplevel()
        # limpia y listo para la siguiente ejecución
        _EMBED_TURTLE.reset()
        return _EMBED_ADDR, _EMBED_PORT

    # Crear tortuga y server por primera vez
    t = Turtle(canvas)

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            buf = b""
            while True:
                data = self.request.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    s = line.decode("utf-8", "ignore").strip()
                    # Encolar en la cola de ESTA tortuga, en el hilo de Tk
                    t.c.after_idle(lambda x=s: t.cmd_q.put(x))

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True

    server = Server((host, port), Handler)
    addr, p = server.server_address

    # Guardar singleton
    _EMBED_SERVER = server
    _EMBED_ADDR, _EMBED_PORT = addr, p
    _EMBED_TURTLE = t

    # Server y loop de animación
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # NO crees otro main/tick aquí si ya lo arrancaste en otro lado;
    # si lo necesitas, aquí lanzas el tick una única vez:
    threading.Thread(target=main, args=(t,), daemon=True).start()

    return addr, p

def main(t=None):
    # si no se pasa tortuga (standalone)
    if t is None:
        t = Turtle(None)
        threading.Thread(target=reader_thread, args=(t.cmd_q,), daemon=True).start()

    state = {"action": None, "last_ts": None}
    running = True  # flag para cortar el loop solo en standalone

    def start_move(d):
        s = 1.0 if d >= 0 else -1.0
        state["action"] = ("move", abs(float(d)), s)
        state["last_ts"] = time.time()

    def start_turn(d):
        s = 1.0 if d >= 0 else -1.0
        state["action"] = ("turn", abs(float(d)), s)
        state["last_ts"] = time.time()

    def start_wait(ms):
        state["action"] = ("wait", float(ms))
        state["last_ts"] = time.time()

    def drain_queue(q):
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass

    def tick():
        nonlocal running
        global SPRITE_PATH, SPEED_PX_PER_SEC, TURN_DEG_PER_SEC
        try:
            a = state["action"]

            if a is not None:
                now = time.time()
                dt = now - (state["last_ts"] or now)
                state["last_ts"] = now

                kind = a[0]
                if kind == "move":
                    rem, s = a[1], a[2]
                    step = SPEED_PX_PER_SEC * dt
                    d = min(rem, step)
                    if d > 0:
                        t.move_step(s * d)
                        rem -= d
                    state["action"] = None if rem <= 1e-6 else ("move", rem, s)

                elif kind == "turn":
                    rem, s = a[1], a[2]
                    step = TURN_DEG_PER_SEC * dt
                    d = min(rem, step)
                    if d > 0:
                        t.turn_step(s * d)
                        rem -= d
                    state["action"] = None if rem <= 1e-6 else ("turn", rem, s)

                elif kind == "wait":
                    rem = a[1] - dt * 1000.0
                    state["action"] = None if rem <= 0 else ("wait", rem)

            else:
                # sin acción en curso → despachar un comando si hay
                try:
                    s = t.cmd_q.get_nowait()
                except queue.Empty:
                    s = None

                if s:
                    parts = s.split()
                    cmd = parts[0].upper()

                    if cmd == "QUIT":
                        if getattr(t, "own_window", False):
                            # Standalone: termina
                            t.r.quit()
                            return
                        else:
                            # Embebido: reset limpio SIN return
                            state["action"] = None
                            state["last_ts"] = None
                            drain_queue(t.cmd_q)
                            t.reset()

                    elif cmd == "FORWARD":
                        start_move(float(parts[1]))
                    elif cmd == "BACK":
                        start_move(-float(parts[1]))
                    elif cmd == "LEFT":
                        start_turn(float(parts[1]))
                    elif cmd == "RIGHT":
                        start_turn(-float(parts[1]))
                    elif cmd == "PENUP":
                        t.penup()
                    elif cmd == "PENDOWN":
                        t.pendown()
                    elif cmd == "POS":
                        t.set_pos(int(parts[1]), int(parts[2]))
                    elif cmd == "POSX":
                        t.set_x(int(parts[1]))
                    elif cmd == "POSY":
                        t.set_y(int(parts[1]))
                    elif cmd == "HEADING":
                        t.set_heading(int(parts[1]))
                    elif cmd == "COLOR":
                        t.set_color(int(parts[1]))
                    elif cmd == "COLORNAME":
                        t.set_color_name(parts[1])
                    elif cmd == "CENTER":
                        t.center()
                    elif cmd == "SHOW":
                        t.show()
                    elif cmd == "HIDE":
                        t.hide()
                    elif cmd == "SPEED":
                        SPEED_PX_PER_SEC = max(1.0, float(parts[1]))
                    elif cmd == "TURNSPEED":
                        TURN_DEG_PER_SEC = max(1.0, float(parts[1]))
                    elif cmd == "DELAY":
                        start_wait(float(parts[1]))

        except Exception:
            # opcional: print("tick error:", e)
            pass
        finally:
            t.r.after(FRAME_MS, tick)

    # arrancar el loop
    t.r.after(FRAME_MS, tick)
    if t.own_window:
        t.r.mainloop()


if __name__ == "__main__":
    main()
