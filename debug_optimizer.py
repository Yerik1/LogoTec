#!/usr/bin/env python3
"""
Prueba para detectar errores en AST optimizado
"""

from frontend.parser import parse_text
from ASTOptimizer import ASTOptimizer
from frontend.semantics import analyze
from frontend.exporter import save_ast_json
import os

def test_semantic_errors():
    # Casos de prueba que pueden causar problemas
    test_cases = [
        {
            "name": "Expresiones aritméticas",
            "code": "INIC x = 2 + 3\nAV x * 1"
        },
        {
            "name": "Comandos con optimización",
            "code": "AV 10 + 5\nRE 0\nGD 90 * 1"
        },
        {
            "name": "Bucles optimizables",
            "code": "REPITE 1 [ AV 10 ]\nREPITE 0 [ GD 45 ]"
        },
        {
            "name": "Expresiones complejas",
            "code": "INIC y = 5 - 5\nINIC z = y + 10"
        }
    ]
    
    optimizer = ASTOptimizer()
    
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"PRUEBA: {test['name']}")
        print(f"{'='*50}")
        print(f"Código: {test['code']}")
        
        try:
            # Parsear AST original
            original_ast = parse_text(test['code'])
            print("\n✓ AST original parseado")
            
            # Analizar AST original
            original_diags = analyze(original_ast)
            print(f"Diagnósticos AST original: {len(original_diags.items)} items")
            if original_diags.items:
                print("  ", original_diags.pretty())
            if original_diags.has_errors():
                print("  ⚠ AST original tiene errores - saltando optimización")
                continue
            
            # Optimizar AST
            optimizer.optimizations_applied = 0
            optimized_ast = optimizer.optimize(original_ast)
            stats = optimizer.get_optimization_stats()
            print(f"✓ Optimizaciones aplicadas: {stats['optimizations_applied']}")
            
            # Mostrar AST optimizado
            print("\nAST optimizado:")
            print(optimized_ast.pretty())
            
            # Analizar AST optimizado
            optimized_diags = analyze(optimized_ast)
            print(f"\nDiagnósticos AST optimizado: {len(optimized_diags.items)} items")
            if optimized_diags.items:
                print("ERRORES EN AST OPTIMIZADO:")
                print(optimized_diags.pretty())
                if optimized_diags.has_errors():
                    print("🚨 AST optimizado genera errores semánticos!")
            else:
                print("✓ AST optimizado sin errores")
                
        except Exception as e:
            print(f"💥 Error durante la prueba: {e}")
            import traceback
            traceback.print_exc()

def test_specific_optimization():
    """Prueba una optimización específica que puede causar problemas"""
    print("\n" + "="*60)
    print("PRUEBA ESPECÍFICA: Optimización problemática")
    print("="*60)
    
    # Este caso puede ser problemático
    code = "INIC x = 2 + 3\nAV x + 0"
    
    try:
        ast = parse_text(code)
        print("AST original:")
        print(ast.pretty())
        
        # Analizar original
        orig_diags = analyze(ast)
        print(f"\nDiagnósticos originales: {len(orig_diags.items)}")
        
        # Optimizar paso a paso para ver dónde falla
        optimizer = ASTOptimizer()
        optimized = optimizer.optimize(ast)
        
        print(f"\nAST después de optimización:")
        print(optimized.pretty())
        
        # Analizar optimizado
        opt_diags = analyze(optimized)
        print(f"\nDiagnósticos optimizados: {len(opt_diags.items)}")
        if opt_diags.items:
            print("PROBLEMAS:")
            for item in opt_diags.items:
                print(f"  [{item.level}] Línea {item.line}: {item.msg}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_semantic_errors()
    test_specific_optimization()