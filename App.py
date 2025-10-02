import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

from frontend.parser import parse_text
from frontend.semantics import analyze
from frontend.exporter import save_ast_json, save_diags_txt

class App(tk.Tk):
  def __init__(self: "App") -> None:
    """
    Constructor de la aplicación principal.
    """
    super().__init__()

    self.title("LogoTec IDE")
    self.minsize(1000, 600)
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
              self._log_output("El área de código está vacía.")
              return

          # 2. Parsear el texto → AST
          ast = parse_text(source_code)

          # 3. Analizar semánticamente
          diags = analyze(ast)

          # 4. Guardar resultados en carpeta out/
          os.makedirs("out", exist_ok=True)

          save_diags_txt(diags, "out/diagnostics.txt")

          # 5. Mostrar feedback en consola GUI
          self._log_output("=== Compilación completada ===")
          self._log_output("\n-- Diagnósticos --")
          self._log_output(diags.pretty())

      except Exception as e:
          messagebox.showerror("Error de compilación", str(e))
          self._log_output(f"Error en compilación: {e}")

  def _show_ast(self):
    """
    Carga directamente el archivo out/ast.json y muestra un ejemplo
    del contenido en forma de árbol simplificado.
    """
    try:
      file_path = os.path.join(os.path.dirname(__file__), "out", "ast.json")

      '''if not os.path.exists(file_path):
        self._log_output("No se encontró el archivo: out/ast.json")
        return'''
      source_code = self.codeArea.get("1.0", tk.END).strip()

        # 2. Parsear el texto → AST
      ast = parse_text(source_code)
      save_ast_json(ast, "out/ast.json")
      self._log_output(ast.pretty())

    except json.JSONDecodeError as e:
      messagebox.showerror("Error de JSON", f"El archivo no es un JSON válido:\n{e}")
    except Exception as e:
      messagebox.showerror("Error", f"Ocurrió un error al cargar el AST:\n{e}")

  '''def _show_ast(self):
    """
    Carga un archivo JSON y lo muestra en el outputArea.
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), "out", "ast.json")

        if not os.path.exists(file_path):
            self._log_output("No se encontró el archivo: out/ast.json")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Formatear JSON con indentación bonita
        pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
        self._log_output("=== AST (desde out/ast.json) ===")
        self._log_output(pretty_json)

    except json.JSONDecodeError as e:
        messagebox.showerror("Error de JSON", f"El archivo no es un JSON válido:\n{e}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al cargar el AST:\n{e}")

    except json.JSONDecodeError as e:
      messagebox.showerror("Error de JSON", f"El archivo no es un JSON válido:\n{e}")
    except Exception as e:
      messagebox.showerror("Error", f"Ocurrió un error al cargar el archivo:\n{e}")
'''
  def _run_code(self):
    self._log_output("Ejecutando...\n(Sin lógica conectada aún)")

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

