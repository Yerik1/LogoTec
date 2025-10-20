#!/usr/bin/env python3
"""
Prueba rápida del optimizador corregido
"""

from frontend.parser import parse_text
from ASTOptimizer import ASTOptimizer
from frontend.semantics import analyze

def test_fixed_optimizer():
    # Código simple para probar
    code = '''INIC x = 2 + 3
AV 10 + 5
RE 0
GD 90 * 1'''
    
    print("Código de prueba:")
    print(code)
    print("\n" + "="*40)
    
    try:
        # Parsear
        ast = parse_text(code)
        print("✓ AST parseado correctamente")
        
        # Optimizar
        optimizer = ASTOptimizer()
        optimized_ast = optimizer.optimize(ast)
        stats = optimizer.get_optimization_stats()
        print(f"✓ Optimizaciones aplicadas: {stats['optimizations_applied']}")
        
        # Analizar semánticamente ambos
        original_diags = analyze(ast)
        optimized_diags = analyze(optimized_ast)
        
        print("\n-- Diagnósticos AST Original --")
        if original_diags.items:
            print(original_diags.pretty())
            print("Tiene errores:", original_diags.has_errors())
        else:
            print("✓ Sin diagnósticos")
            
        print("\n-- Diagnósticos AST Optimizado --")
        if optimized_diags.items:
            print(optimized_diags.pretty())
            print("Tiene errores:", optimized_diags.has_errors())
        else:
            print("✓ Sin diagnósticos")
            
        print("\n✓ Todo funcionando correctamente!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_optimizer()