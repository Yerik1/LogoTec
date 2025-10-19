import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

from frontend.parser import parse_text
from frontend.semantics import analyze
from frontend.exporter import save_ast_json, save_diags_txt
from frontend.ast_viewer_tk import AstViewer
from ASTOptimizer import ASTOptimizer

class App(tk.Tk):
  def __init__(self: "App") -> None:
    """
    Constructor de la aplicación principal.
    """
    super().__init__()

    self.title("LogoTec IDE")
    self.minsize(1000, 600)
    
    # Almacenar AST y AST optimizado para comparación
    self.current_ast = None
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
        ("Optimizar", self._optimize_code),
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
          ast = parse_text(source_code)
          self.current_ast = ast  # Guardar para optimización
          
          # Salidas para la GUI

          # 3. Analizar semánticamente
          diags = analyze(ast)

          # 4. Guardar resultados en carpeta out/
          os.makedirs("out", exist_ok=True)

          save_ast_json(ast, "out/ast.json")
          save_diags_txt(diags, "out/diagnostics.txt")

          # 5. Mostrar feedback en consola GUI
          self._clear_output()
          self._log_output("=== Compilación completada ===")
          self._log_output("\n-- Diagnósticos --")
          self._log_output(diags.pretty())
          self._log_output("\n-- AST generado --")
          self._log_output("AST guardado en: out/ast.json")
          self._log_output("Use 'Mostrar AST' para visualizar")
          self._log_output("\n-- Optimización --")
          self._log_output("Use 'Optimizar' para optimizar el AST generado")



      except Exception as e:
          messagebox.showerror("Error de compilación", str(e))
          self._clear_output()
          self._log_output(f"Error en compilación: {e}")

  def _optimize_code(self):
      """
      Optimiza el AST actual usando el optimizador.
      """
      try:
          if self.current_ast is None:
              self._clear_output()
              self._log_output("No hay AST para optimizar. Compile primero el código.")
              return

          # Crear el optimizador
          optimizer = ASTOptimizer()
          
          # Obtener estadísticas antes de optimizar
          self._clear_output()
          self._log_output("=== Iniciando Optimización ===")
          self._log_output("\n-- AST Original --")
          self._log_output("Estructura original:")
          self._log_output(self.current_ast.pretty())
          
          # Optimizar el AST
          self.optimized_ast = optimizer.optimize(self.current_ast)
          
          # Obtener estadísticas
          stats = optimizer.get_optimization_stats()
          
          # Mostrar resultados
          self._log_output(f"\n-- Resultados de Optimización --")
          self._log_output(f"Optimizaciones aplicadas: {stats['optimizations_applied']}")
          
          if stats['optimizations_applied'] > 0:
              self._log_output("\n-- AST Optimizado --")
              self._log_output("Estructura optimizada:")
              self._log_output(self.optimized_ast.pretty())
              
              # Guardar AST optimizado
              os.makedirs("out", exist_ok=True)
              save_ast_json(self.optimized_ast, "out/ast_optimized.json")
              self._log_output("\nAST optimizado guardado en: out/ast_optimized.json")
              
              # Analizar semánticamente el AST optimizado
              try:
                  optimized_diags = analyze(self.optimized_ast)
                  save_diags_txt(optimized_diags, "out/diagnostics_optimized.txt")
                  self._log_output("Diagnósticos del AST optimizado guardados en: out/diagnostics_optimized.txt")
                  
                  # Mostrar diagnósticos si hay errores
                  if optimized_diags.errors or optimized_diags.warnings:
                      self._log_output("\n-- Diagnósticos del AST Optimizado --")
                      self._log_output(optimized_diags.pretty())
                  else:
                      self._log_output("✓ AST optimizado sin errores semánticos")
                      
              except Exception as analysis_error:
                  self._log_output(f"⚠ Error en análisis semántico del AST optimizado: {analysis_error}")
          else:
              self._log_output("No se aplicaron optimizaciones - el código ya está optimizado")
          
          self._log_output("\n=== Optimización Completada ===")

      except Exception as e:
          messagebox.showerror("Error de optimización", str(e))
          self._clear_output()
          self._log_output(f"Error en optimización: {e}")

  def _show_ast(self):
    """
    Muestra el AST. Si hay AST optimizado, permite elegir cuál mostrar.
    """
    if not os.path.exists("out/ast.json"):
        messagebox.showwarning("Advertencia", "No hay AST para mostrar. Compile primero el código.")
        return
    
    # Si hay AST optimizado, preguntar cuál mostrar
    if self.optimized_ast is not None and os.path.exists("out/ast_optimized.json"):
        choice = messagebox.askyesnocancel(
            "Seleccionar AST", 
            "¿Qué AST desea mostrar?\n\nSí = AST Original\nNo = AST Optimizado\nCancelar = Ambos (comparar)"
        )
        
        if choice is True:
            # Mostrar AST original
            AstViewer(self, json_path="out/ast.json", title="AST Original")
        elif choice is False:
            # Mostrar AST optimizado
            AstViewer(self, json_path="out/ast_optimized.json", title="AST Optimizado")
        elif choice is None:
            # Mostrar ambos para comparar
            AstViewer(self, json_path="out/ast.json", title="AST Original")
            AstViewer(self, json_path="out/ast_optimized.json", title="AST Optimizado")
    else:
        # Solo hay AST original
        AstViewer(self, json_path="out/ast.json", title="AST Original")

  def _run_code(self):
    self._clear_output()
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

  def _clear_output(self: "App") -> None:
      self.outputArea.config(state=tk.NORMAL)
      self.outputArea.delete("1.0", tk.END)
      self.outputArea.config(state=tk.DISABLED)