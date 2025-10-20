#!/usr/bin/env python3
"""
Prueba rápida del AstViewer corregido
"""

from frontend.parser import parse_text
from ASTOptimizer import ASTOptimizer
from frontend.exporter import save_ast_json
import os

def test_ast_viewer():
    # Código simple para probar
    code = '''INIC x = 2 + 3
AV 15'''
    
    print("Generando ASTs para probar el viewer...")
    
    try:
        # Parsear y optimizar
        ast = parse_text(code)
        optimizer = ASTOptimizer()
        optimized_ast = optimizer.optimize(ast)
        
        # Crear directorio out
        os.makedirs("out", exist_ok=True)
        
        # Guardar ASTs
        save_ast_json(ast, "out/ast.json")
        save_ast_json(optimized_ast, "out/ast_optimized.json")
        
        print("✓ ASTs guardados en out/ast.json y out/ast_optimized.json")
        print("✓ Ahora puedes usar 'Mostrar AST' en la aplicación")
        print(f"✓ Optimizaciones aplicadas: {optimizer.get_optimization_stats()['optimizations_applied']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ast_viewer()