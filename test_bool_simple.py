#!/usr/bin/env python3
"""
Test simple para optimizaciones booleanas usando sintaxis correcta
"""

from frontend.parser import parse_text
from ASTOptimizer import ASTOptimizer
from frontend.semantics import analyze

def test_boolean_simple():
    """Test simple de optimizaciones booleanas"""
    
    print("="*60)
    print("TEST SIMPLE DE OPTIMIZACIÓN BOOLEANA")
    print("="*60)
    
    # Casos simples que funcionan con la gramática
    test_cases = [
        {
            "name": "Constant folding: 5 iguales? 5 (true)",
            "code": "SI 5 iguales? 5 [ AV 10 ]",
            "expected": "Debería ejecutar siempre AV 10"
        },
        {
            "name": "Constant folding: 3 mayorque? 7 (false)",  
            "code": "SI 3 mayorque? 7 [ GD 45 ]",
            "expected": "Debería eliminar el bloque completo"
        },
        {
            "name": "Constant folding: 10 menorque? 20 (true)",
            "code": "SI 10 menorque? 20 [ RE 5 ]", 
            "expected": "Debería ejecutar siempre RE 5"
        }
    ]
    
    optimizer = ASTOptimizer()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 50)
        print(f"Código: {test['code']}")
        print(f"Esperado: {test['expected']}")
        
        try:
            # Parsear AST original
            original_ast = parse_text(test['code'])
            print("✓ AST parseado correctamente")
            
            # Mostrar AST original
            print(f"\nAST Original:")
            print(original_ast.pretty())
            
            # Optimizar
            optimizer.optimizations_applied = 0
            optimized_ast = optimizer.optimize(original_ast)
            stats = optimizer.get_optimization_stats()
            
            print(f"\nOptimizaciones aplicadas: {stats['optimizations_applied']}")
            
            if stats['optimizations_applied'] > 0:
                print(f"\nAST Optimizado:")
                print(optimized_ast.pretty())
            else:
                print("Sin optimizaciones aplicadas")
            
            # Verificar análisis semántico
            opt_diags = analyze(optimized_ast)
            if opt_diags.items:
                print(f"\n⚠ Errores semánticos:")
                for item in opt_diags.items:
                    print(f"   [{item.level}] Línea {item.line}: {item.msg}")
            else:
                print("\n✓ AST optimizado sin errores semánticos")
                
        except Exception as e:
            print(f"\n💥 Error: {e}")

def test_arithmetic_vs_boolean():
    """Comparar optimizaciones aritméticas vs booleanas"""
    
    print(f"\n{'='*60}")
    print("COMPARACIÓN: ARITMÉTICA vs BOOLEANA")
    print(f"{'='*60}")
    
    tests = [
        {
            "name": "Aritmética: constant folding",
            "code": "INIC x = 2 + 3\nAV x"
        },
        {
            "name": "Booleana: constant folding",
            "code": "SI 5 iguales? 5 [ AV 15 ]"
        }
    ]
    
    optimizer = ASTOptimizer()
    
    for test in tests:
        print(f"\n{test['name']}:")
        print(f"Código: {test['code']}")
        
        try:
            ast = parse_text(test['code'])
            optimizer.optimizations_applied = 0
            optimized = optimizer.optimize(ast)
            stats = optimizer.get_optimization_stats()
            
            print(f"Optimizaciones: {stats['optimizations_applied']}")
            if stats['optimizations_applied'] > 0:
                print("AST optimizado:")
                print(optimized.pretty())
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_boolean_simple() 
    test_arithmetic_vs_boolean()