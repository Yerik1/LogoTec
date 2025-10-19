#!/usr/bin/env python3
"""
Script de prueba para el optimizador de AST
"""

from frontend.parser import parse_text
from ASTOptimizer import ASTOptimizer

def test_optimizer():
    """Pruebas del optimizador con diferentes casos"""
    
    test_cases = [
        # Caso 1: Optimizaciones aritméticas
        {
            "name": "Aritmética básica",
            "code": """
            INIC x = 2 + 3
            INIC y = x * 1
            INIC z = y + 0
            AV 5 * 0
            """
        },
        # Caso 2: Control de flujo
        {
            "name": "Control de flujo",
            "code": """
            SI 1 IGUALES 1 HAZ
                AV 10
            FIN
            REPITE 0 [
                AV 5
            ]
            """
        },
        # Caso 3: Expresiones booleanas
        {
            "name": "Expresiones booleanas",
            "code": """
            SI 5 MAYORQ 3 Y 1 IGUALES 1 HAZ
                GD 90
            FIN
            """
        },
        # Caso 4: Comandos de movimiento
        {
            "name": "Comandos de movimiento",
            "code": """
            AV 0
            RE 10
            GD 0
            GI 45
            """
        }
    ]
    
    optimizer = ASTOptimizer()
    
    for test_case in test_cases:
        print(f"\n{'='*50}")
        print(f"PRUEBA: {test_case['name']}")
        print(f"{'='*50}")
        
        try:
            # Parsear el código
            print("Código original:")
            print(test_case['code'])
            
            ast = parse_text(test_case['code'])
            print(f"\nAST original:")
            print(ast.pretty())
            
            # Optimizar
            optimizer.optimizations_applied = 0  # Reset contador
            optimized_ast = optimizer.optimize(ast)
            
            print(f"\nAST optimizado:")
            print(optimized_ast.pretty())
            
            stats = optimizer.get_optimization_stats()
            print(f"\nOptimizaciones aplicadas: {stats['optimizations_applied']}")
            
        except Exception as e:
            print(f"Error en la prueba: {e}")

def test_specific_optimizations():
    """Pruebas específicas de optimizaciones individuales"""
    
    print("\n" + "="*60)
    print("PRUEBAS ESPECÍFICAS DE OPTIMIZACIONES")
    print("="*60)
    
    optimizer = ASTOptimizer()
    
    # Test constant folding
    test_expressions = [
        "INIC result = 2 + 3 * 4",
        "INIC result = (10 - 5) / 2",
        "INIC result = 2 POTENCIA 3",
        "INIC result = -(-5)",
        "SI 5 IGUALES 5 HAZ AV 10 FIN",
        "SI 3 MAYORQ 5 HAZ AV 10 FIN",
        "REPITE 1 [ AV 10 ]",
        "REPITE 0 [ AV 10 ]"
    ]
    
    for expr in test_expressions:
        try:
            print(f"\nExpresión: {expr}")
            ast = parse_text(expr)
            
            optimizer.optimizations_applied = 0
            optimized = optimizer.optimize(ast)
            
            print(f"Optimizaciones: {optimizer.optimizations_applied}")
            if optimizer.optimizations_applied > 0:
                print("AST optimizado:")
                print(optimized.pretty())
            else:
                print("Sin optimizaciones aplicadas")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_optimizer()
    test_specific_optimizations()