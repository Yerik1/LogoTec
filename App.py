import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, sys, subprocess
from pathlib import Path

from Executable.drawing import start_embed_server
from Executable.pi_executor import PiExecutor, translate_runtime_to_pi
from frontend.parser import parse_text
from frontend.semantics import analyze
from frontend.exporter import save_ast_json, save_diags_txt
from frontend.ast_viewer_tk import AstViewer
from optimizer.ASTOptimizer import ASTOptimizer
from IR.IntermediateCodeGen import IntermediateCodeGen
from IR_to_ASM.AssemblyGen import AssemblyGen
from Executable.build_native import build_and_link

class App(tk.Tk):
  def __init__(self: "App") -> None:
    """
    Constructor de la aplicación principal.
    """
    super().__init__()

    self.title("LogoTec IDE")
    self.minsize(1000, 600)
    
    # Almacenar AST y AST optimizado para comparación
    self.original_ast = None
    self.optimized_ast = None
    # Pi connection state
    self.pi_executor = None
    self.pi_ip = "192.168.1.100"
    self.pi_port = 9000
    
    self._create_widgets()

  def _create_widgets(self: "App") -> None:
    """
    Crea los widgets principales de la aplicación.
    """
    self._create_toolbar()
    self._create_paned_window()
    self._create_main_area()
    self._create_output_area()

  def _create_toolbar(self: "App") -> None:
    """
    Crea la barra de herramientas.
    """
    self.button_bar = ttk.Frame(self, borderwidth=2, relief="groove")
    self.button_bar.pack(fill=tk.X, pady=10, padx=10)

    for text, cmd in [
        ("Compilar", self._compile_code),
        ("Mostrar AST", self._show_ast),
        ("Ejecutar", self._run_code),
        ("Cargar Archivo", self._load_file),
    ]:
      button = ttk.Button(self.button_bar, text=text, command=cmd)
      button.pack(side=tk.LEFT, padx=5)

  def _create_paned_window(self: "App") -> None:
    """
    Crea la ventana dividida principal.
    """
    self.paned_window = ttk.Panedwindow(self, orient=tk.VERTICAL)
    self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

  def _create_main_area(self: "App") -> None:
    """
    Crea el área principal de la aplicación.
    """
    self.hbox = ttk.Frame(self.paned_window)

    # Editor de Código
    self.codeArea = tk.Text(self.hbox)
    self.codeArea.insert(tk.END, "// Escribe tu programa LogoTec aquí...")
    self.codeArea.grid(row=0, column=0, sticky="nsew")

    # Canvas
    self.canvas = tk.Canvas(self.hbox, bg="white")
    self.canvas.grid(row=0, column=1, sticky="nsew")

    # Panel de control para Raspberry Pi (botones)
    self.pi_panel = ttk.Frame(self.hbox, borderwidth=1, relief="ridge")
    self.pi_panel.grid(row=0, column=2, sticky="nsew", padx=(8,0))

    # Conexión Pi
    ttk.Label(self.pi_panel, text="Raspberry Pi (IP:Puerto)").pack(padx=6, pady=(6,2))
    conn_frame = ttk.Frame(self.pi_panel)
    conn_frame.pack(padx=6, pady=2)
    self.pi_ip_var = tk.StringVar(value=self.pi_ip)
    self.pi_port_var = tk.StringVar(value=str(self.pi_port))
    ttk.Entry(conn_frame, textvariable=self.pi_ip_var, width=14).pack(side=tk.LEFT)
    ttk.Entry(conn_frame, textvariable=self.pi_port_var, width=6).pack(side=tk.LEFT, padx=(6,0))
    self.pi_connect_btn = ttk.Button(self.pi_panel, text="Conectar", command=self._connect_pi)
    self.pi_connect_btn.pack(padx=6, pady=6)
    # Estado de conexión
    self.pi_status_label = ttk.Label(self.pi_panel, text="Desconectado", foreground="red")
    self.pi_status_label.pack(padx=6, pady=(0,6))

    # Botones de instrucciones
    btns = [
      ("ADELANTE", "ADELANTE"), ("ATRAS", "ATRAS"), ("IZQUIERDA", "IZQUIERDA"), ("DERECHA", "DERECHA"),
      ("DETENER", "DETENER"), ("BAJAR LAPIZ", "BAJAR_LAPIZ"), ("LEVANTAR LAPIZ", "LEVANTAR_LAPIZ"),
      ("VERDE", "VERDE"), ("MORADO", "MORADO"), ("CELESTE", "CELESTE"),
    ]
    # Lista para controlar estado de botones Pi
    self.pi_buttons = []
    for (label, cmd) in btns:
      b = ttk.Button(self.pi_panel, text=label, command=lambda c=cmd: self._send_pi_command(c), state=tk.DISABLED)
      b.pack(fill=tk.X, padx=6, pady=2)
      self.pi_buttons.append(b)

    # Botón: Ejecutar en maquina (envía el programa compilado a la Pi)
    self.exec_on_pi_btn = ttk.Button(self.pi_panel, text="Ejecutar en maquina", command=self._exec_on_pi, state=tk.DISABLED)
    self.exec_on_pi_btn.pack(fill=tk.X, padx=6, pady=(12,2))

    # Configuración
    self.hbox.columnconfigure(0, weight=3)
    self.hbox.columnconfigure(1, weight=2)
    self.hbox.columnconfigure(2, weight=1)
    self.hbox.rowconfigure(0, weight=1)

    self.paned_window.add(self.hbox, weight=4)

  def _create_output_area(self: "App") -> None:
    """
    Crea el área para la salida de la consola.
    """
    self.outputArea = tk.Text(self.paned_window, bg="black", fg="white", state=tk.DISABLED, height=8)
    self.paned_window.add(self.outputArea, weight=1)

  def _connect_pi(self):
    """Conectar/Desconectar a la Raspberry Pi usando PiExecutor."""
    ip = self.pi_ip_var.get().strip()
    try:
      port = int(self.pi_port_var.get().strip())
    except Exception:
      messagebox.showerror("Error", "Puerto inválido")
      return

    if self.pi_executor and self.pi_executor.connected:
      self.pi_executor.disconnect()
      self.pi_executor = None
      self.pi_connect_btn.config(text="Conectar")
      self._set_pi_buttons_enabled(False)
      self._log_output("Desconectado de la Pi")
      return

    # crear y conectar
    self.pi_executor = PiExecutor(ip, port, on_message=self._log_output, on_error=self._log_output)
    if self.pi_executor.connect():
      self.pi_connect_btn.config(text="Desconectar")
      self._set_pi_buttons_enabled(True)
      self._log_output(f"Conectado a Pi {ip}:{port}")
    else:
      self.pi_executor = None

  def _send_pi_command(self, cmd: str):
    """Enviar comando simple a la Pi (no bloqueante)."""
    if not hasattr(self, 'pi_executor') or not self.pi_executor:
      messagebox.showwarning("Aviso", "No conectado a la Pi. Presiona 'Conectar'.")
      return
    # enviar en hilo para evitar bloquear UI
    def worker():
      try:
        self.pi_executor.send_command(cmd)
      except Exception as e:
        self._log_output(f"Error enviando comando: {e}")
    import threading
    threading.Thread(target=worker, daemon=True).start()

  def _set_pi_buttons_enabled(self, enabled: bool):
    """Habilita o deshabilita los botones del panel Pi y actualiza la etiqueta de estado."""
    state = tk.NORMAL if enabled else tk.DISABLED
    for b in getattr(self, 'pi_buttons', []):
      try:
        b.config(state=state)
      except Exception:
        pass
    # actualizar etiqueta de estado
    if enabled:
      try:
        self.pi_status_label.config(text="Conectado", foreground="green")
      except Exception:
        pass
    else:
      try:
        self.pi_status_label.config(text="Desconectado", foreground="red")
      except Exception:
        pass

  def _compile_code(self):

      try:
          # 1. Obtener el código del editor
          source_code = self.codeArea.get("1.0", tk.END).strip()
          if not source_code:
              self._clear_output()
              self._log_output("El área de código está vacía.")
              return

          # Obtener la primera línea
          first_line = source_code.splitlines()[0].strip()

          # Verificar si empieza con comentario (por ejemplo: '#', '//', o ';' según tu lenguaje)
          # Puedes ajustar los prefijos aceptados aquí
          if not (first_line.startswith("#") or first_line.startswith("//") or first_line.startswith(";")):
              self._clear_output()
              self._log_output("Error: El programa debe iniciar con un comentario en la primera línea.")
              return

          # 2. Parsear el texto → AST
          self.original_ast = parse_text(source_code)

          # 3. Analizar semánticamente (AST original)
          diags = analyze(self.original_ast)
          if diags.has_errors():
              self._clear_output()
              self._log_output("Errores semánticos encontrados en el AST original:")
              self._log_output(diags.pretty())
              return

          # 4. Optimizar el AST
          optimizer = ASTOptimizer()
          self.optimized_ast = optimizer.optimize(self.original_ast)
          optimization_stats = optimizer.get_optimization_stats()

          # 5. Generar IR
          try:
              ir_generator = IntermediateCodeGen()
              llvm_ir = ir_generator.generate(self.optimized_ast)

              # Guardar IR en carpeta out/
              os.makedirs("out", exist_ok=True)
              ir_output_path = os.path.join("out", "output.ll")
              ir_generator.save_ir_to_file(llvm_ir, ir_output_path)

              # Insertar encabezado target triple si no existe
              with open(ir_output_path, "r+", encoding="utf-8") as f:
                  content = f.read()
                  if "target triple" not in content:
                      f.seek(0, 0)
                      f.write('target triple = "x86_64-pc-windows-msvc"\n' + content)

              self._log_output(f"IR generado correctamente: {ir_output_path}")

          except Exception as ir_error:
              self._log_output("Error al generar IR intermedio:")
              self._log_output(str(ir_error))
              raise

          # 6. Generar ASM
          asm_generator = AssemblyGen("out/output.ll", "out/output.s")
          asm_path = asm_generator.generate()

          exe_path = build_and_link(asm_path, out_dir="out", exe_name="turtle")
          exe_path = Path(exe_path).resolve()

          # 7. Guardar resultados en carpeta out/
          os.makedirs("out", exist_ok=True)

          save_ast_json(self.original_ast, "out/ast.json")
          save_ast_json(self.optimized_ast, "out/ast_optimized.json")
          save_diags_txt(diags, "out/diagnostics.txt")

          # 8. Mostrar feedback en consola GUI
          self._clear_output()
          self._log_output("=== Compilación completada ===")
          self._log_output("\n-- Diagnósticos --")
          self._log_output(diags.pretty())
          # Marcar compilación exitosa y generar comandos runtime para envío a Pi
          try:
            self.compiled = True
            if self.optimized_ast is not None:
              self._last_runtime_commands = self._ast_to_runtime_commands(self.optimized_ast)
            else:
              self._last_runtime_commands = self._ast_to_runtime_commands(self.original_ast)
            self._log_output(f"Comandos runtime generados: {len(self._last_runtime_commands)} comandos")
            self._set_exec_button_enabled(True)
          except Exception as _e:
            self.compiled = False
            self._last_runtime_commands = []
            self._set_exec_button_enabled(False)

      except Exception as e:
          messagebox.showerror("Error de compilación", str(e))
          self._clear_output()
          self._log_output(f"Error en compilación: {e}")


  def _show_ast(self):
    """
    Muestra el AST permitiendo elegir entre original y optimizado.
    """
    if not os.path.exists("out/ast.json"):
        messagebox.showwarning("Advertencia", "No hay AST para mostrar. Compile primero el código.")
        return
    
    # Si hay AST optimizado, mostrar opciones
    if self.optimized_ast is not None and os.path.exists("out/ast_optimized.json"):
        # Crear ventana de selección personalizada
        selection_window = tk.Toplevel(self)
        selection_window.title("Seleccionar AST")
        selection_window.geometry("600x200")
        selection_window.resizable(False, False)
        selection_window.transient(self)
        selection_window.grab_set()
        
        # Centrar la ventana
        selection_window.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        
        # Título
        title_label = ttk.Label(selection_window, text="Seleccione el AST a visualizar:", font=("Arial", 12, "bold"))
        title_label.pack(pady=20)
        
        # Frame para botones
        button_frame = ttk.Frame(selection_window)
        button_frame.pack(pady=10)
        
        # Variable para almacenar la elección
        choice = tk.StringVar()
        
        def make_choice(value):
            choice.set(value)
            selection_window.destroy()
        
        # Botones de selección
        original_btn = ttk.Button(button_frame, text="AST Original", 
                                command=lambda: make_choice("original"), width=18)
        original_btn.pack(side=tk.LEFT, padx=15)
        
        optimized_btn = ttk.Button(button_frame, text="AST Optimizado", 
                                 command=lambda: make_choice("optimized"), width=18)
        optimized_btn.pack(side=tk.LEFT, padx=15)
        
        # Esperar a que se haga la elección
        selection_window.wait_window()
        
        # Procesar la elección
        if choice.get() == "original":
            viewer = AstViewer(self, json_path="out/ast.json", title="AST Original")
        elif choice.get() == "optimized":
            viewer = AstViewer(self, json_path="out/ast_optimized.json", title="AST Optimizado")

    else:
        # Solo hay AST original
        viewer = AstViewer(self, json_path="out/ast.json")
        viewer.title("AST Original")

  def _set_exec_button_enabled(self, enabled: bool):
    try:
      state = tk.NORMAL if enabled else tk.DISABLED
      self.exec_on_pi_btn.config(state=state)
    except Exception:
      pass

  def _ast_to_runtime_commands(self, node) -> list:
    """Convierte (recursivamente) un AST en una lista de comandos runtime (strings).

    Implementación simple: soporta movimientos con literales, lápiz, color y espera.
    No resuelve variables o llamadas a funciones complejas; para esos casos intenta
    recorrer el árbol e incluir comandos de los hijos.
    """
    cmds = []
    if node is None:
      return cmds
    kind = getattr(node, 'kind', '').upper()
    if kind in ("PROGRAM", "STMTS"):
      for c in node.children:
        cmds.extend(self._ast_to_runtime_commands(c))
      return cmds

    if kind in ("AV", "RE", "GD", "GI"):
      val = 0
      if node.children:
        ch = node.children[0]
        if getattr(ch, 'kind', '').upper() == 'NUM':
          try:
            val = int(ch.value)
          except Exception:
            val = 0
      if kind == 'AV':
        cmds.append(f"FORWARD {val}")
      elif kind == 'RE':
        cmds.append(f"BACK {val}")
      elif kind == 'GD':
        cmds.append(f"RIGHT {val}")
      elif kind == 'GI':
        cmds.append(f"LEFT {val}")
      return cmds

    if kind == 'BL':
      cmds.append('PENUP')
      return cmds
    if kind == 'SB':
      cmds.append('PENDOWN')
      return cmds

    if kind == 'ESPERA':
      v = 100
      if node.children and getattr(node.children[0], 'kind', '').upper() == 'NUM':
        try:
          v = int(node.children[0].value)
        except Exception:
          v = 100
      cmds.append(f"DELAY {v}")
      return cmds

    if kind == 'PONCL' and node.children:
      ch = node.children[0]
      if getattr(ch, 'kind', '').upper() == 'NUM':
        try:
          cid = int(ch.value)
          cmds.append(f"COLOR {cid}")
        except Exception:
          pass
      elif getattr(ch, 'kind', '').upper() == 'STR':
        cmds.append(f"COLORNAME {ch.value}")
      return cmds

    if kind == 'PONPOS' and len(node.children) >= 2:
      a, b = node.children[0], node.children[1]
      if getattr(a, 'kind', '').upper() == 'NUM' and getattr(b, 'kind', '').upper() == 'NUM':
        cmds.append(f"POS {int(a.value)} {int(b.value)}")
      return cmds

    if kind == 'PONX' and node.children and getattr(node.children[0], 'kind', '').upper() == 'NUM':
      cmds.append(f"POSX {int(node.children[0].value)}")
      return cmds

    if kind == 'PONY' and node.children and getattr(node.children[0], 'kind', '').upper() == 'NUM':
      cmds.append(f"POSY {int(node.children[0].value)}")
      return cmds

    if kind == 'CENTRO':
      cmds.append('CENTER')
      return cmds

    if kind == 'REPITE' and len(node.children) >= 2:
      count_node = node.children[0]
      body_node = node.children[1]
      try:
        if getattr(count_node, 'kind', '').upper() == 'NUM':
          times = int(count_node.value)
          for _ in range(times):
            cmds.extend(self._ast_to_runtime_commands(body_node))
      except Exception:
        pass
      return cmds

    # Fallback: recorrer hijos
    for c in getattr(node, 'children', []) or []:
      cmds.extend(self._ast_to_runtime_commands(c))
    return cmds

  def _exec_on_pi(self):
    """Envía los comandos runtime generados a la Raspberry Pi usando PiExecutor.

    Requiere que el programa haya sido compilado (botón habilitado tras compilar).
    """
    if not getattr(self, 'compiled', False):
      messagebox.showwarning("Aviso", "Compila el código antes de ejecutar en la máquina.")
      return
    if not getattr(self, 'pi_executor', None) or not self.pi_executor.connected:
      messagebox.showwarning("Aviso", "No conectado a la Pi. Por favor presiona 'Conectar' antes de enviar.")
      return

    pi_cmds = []
    for rc in getattr(self, '_last_runtime_commands', []) or []:
      try:
        pi_cmd = translate_runtime_to_pi(rc)
        if pi_cmd:
          pi_cmds.append(pi_cmd)
      except Exception:
        pass

    if not pi_cmds:
      messagebox.showinfo("Info", "No se generaron comandos para enviar a la Pi.")
      return

    def done():
      self._log_output("Ejecución en Pi completada")

    self._log_output(f"Enviando {len(pi_cmds)} comandos a la Pi...")
    try:
      self.pi_executor.execute_commands_async(pi_cmds, done_callback=done)
    except Exception as e:
      self._log_output(f"Error enviando a Pi: {e}")

  def _run_code(self):
      import os, sys, subprocess, shutil, threading, traceback
      self._clear_output()
      self._log_output("Ejecutando...\n")

      def worker():
          try:
              out_dir = Path("out");
              out_dir.mkdir(exist_ok=True)
              exe_path = (out_dir / ("turtle.exe" if os.name == "nt" else "turtle")).resolve()
              if not exe_path.exists():
                  self._log_output(f"❌ No existe el ejecutable: {exe_path}\n")
                  return

              # copiar drawing.py a out si hace falta
              server_src = Path(__file__).parent / "drawing.py"
              server_dst = out_dir / "drawing.py"
              if server_src.exists():
                  if not server_dst.exists() or server_src.read_bytes() != server_dst.read_bytes():
                      shutil.copy2(server_src, server_dst)

              from Executable.drawing import start_embed_server

              # 1) inicia el bridge sobre tu Canvas existente (ej. self.canvas)
              addr, port = start_embed_server(self.canvas)

              env = os.environ.copy()
              env["TURTLE_TCP_ADDR"] = f"{addr}:{port}"

              proc = subprocess.Popen(
                  [str(exe_path)],
                  cwd=str(exe_path.parent),
                  env=env,
                  stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,
                  text=True,
                  bufsize=1
              )
              for line in proc.stderr:
                  self._log_output(line)
              rc = proc.wait()
              self._log_output(f"\n[proceso terminado] código de salida: {rc}\n")
          except Exception as e:
              import traceback
              self._log_output("❌ Error al ejecutar:\n" + traceback.format_exc())

      threading.Thread(target=worker, daemon=True).start()

  def _load_file(self):
    """
    Carga un archivo de texto/código en el codeArea.
    """
    try:
      file_path = filedialog.askopenfilename(
          title="Seleccionar archivo de código",
          filetypes=[("Archivos de texto", "*.txt *.logo *.py *.json"), ("Todos los archivos", "*.*")]
      )
      if not file_path:
        return  # Usuario canceló

      with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

      # Limpiar el área de código y cargar el archivo
      self.codeArea.delete("1.0", tk.END)
      self.codeArea.insert(tk.END, content)

      self._log_output(f"Archivo cargado en editor: {file_path}")

    except Exception as e:
      messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

  def _log_output(self: "App", message: str) -> None:
    """
    Agrega un mensaje al área de la consola.

    Args:
      message (str): Mensaje a agregar.
    """
    self.outputArea.config(state=tk.NORMAL)
    self.outputArea.insert(tk.END, message + "\n")
    self.outputArea.config(state=tk.DISABLED)
    self.outputArea.see(tk.END)

  def _clear_output(self: "App") -> None:
      self.outputArea.config(state=tk.NORMAL)
      self.outputArea.delete("1.0", tk.END)
      self.outputArea.config(state=tk.DISABLED)