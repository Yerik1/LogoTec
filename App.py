import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, sys, subprocess
from pathlib import Path

from Executable.drawing import start_embed_server
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

    # Configuración
    self.hbox.columnconfigure(0, weight=3)
    self.hbox.columnconfigure(1, weight=2)
    self.hbox.rowconfigure(0, weight=1)

    self.paned_window.add(self.hbox, weight=4)

  def _create_output_area(self: "App") -> None:
    """
    Crea el área para la salida de la consola.
    """
    self.outputArea = tk.Text(self.paned_window, bg="black", fg="white", state=tk.DISABLED, height=8)
    self.paned_window.add(self.outputArea, weight=1)

  def _compile_code(self):
      try:
          # 1. Obtener el código del editor
          source_code = self.codeArea.get("1.0", tk.END).strip()
          if not source_code:
              self._clear_output()
              self._log_output("El área de código está vacía.")
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