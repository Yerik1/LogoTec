#!/usr/bin/env python3
"""
Test específico para optimizaciones de lógica booleana
"""

from frontend.parser import parse_text
from ASTOptimizer import ASTOptimizer
from frontend.semantics import analyze

def test_boolean_optimization():
    """Prueba las optimizaciones de lógica booleana"""
    
    print("="*60)
    print("TEST DE OPTIMIZACIÓN DE LÓGICA BOOLEANA")
    print("="*60)
    
    # Casos de prueba específicos para lógica booleana
    test_cases = [
        {
            "name": "Cortocircuito AND - true Y x = x",
            "code": "SI 1 iguales? 1 y 5 mayorque? 3 HAZ AV 10 FIN",
            "expected": "Debe simplificar a: SI 5 mayorque? 3"
        },
        {
            "name": "Cortocircuito AND - false Y x = false",
            "code": "SI 3 mayorque? 5 y 1 iguales? 1 HAZ AV 20 FIN", 
            "expected": "Debe simplificar a condición falsa"
        },
        {
            "name": "Cortocircuito OR - true O x = true",
            "code": "SI 1 iguales? 1 o 5 menorque? 3 HAZ AV 30 FIN",
            "expected": "Debe simplificar a condición verdadera"
        },
        {
            "name": "Cortocircuito OR - false O x = x", 
            "code": "SI 3 mayorque? 5 o 7 mayorque? 4 HAZ RE 15 FIN",
            "expected": "Debe simplificar a: SI 7 mayorque? 4"
        },
        {
            "name": "Constant folding - comparación verdadera",
            "code": "SI 5 iguales? 5 HAZ AV 40 FIN",
            "expected": "Debe ejecutar siempre el bloque AV 40"
        },
        {
            "name": "Constant folding - comparación falsa",
            "code": "SI 3 mayorque? 7 HAZ GI 30 FIN",
            "expected": "Debe eliminar el bloque completamente"
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
            
            # Optimizar
            optimizer.optimizations_applied = 0
            optimized_ast = optimizer.optimize(original_ast)
            stats = optimizer.get_optimization_stats()
            
            print(f"\nOptimizaciones aplicadas: {stats['optimizations_applied']}")
            
            if stats['optimizations_applied'] > 0:
                print("\nAST Original:")
                print(original_ast.pretty())
                print("\nAST Optimizado:")
                print(optimized_ast.pretty())
                
                # Verificar que no hay errores semánticos
                opt_diags = analyze(optimized_ast)
                if opt_diags.items:
                    print(f"\n⚠ ADVERTENCIA: Errores semánticos detectados:")
                    print(opt_diags.pretty())
                else:
                    print("\n✓ AST optimizado sin errores semánticos")
            else:
                print("Sin optimizaciones aplicadas")
                
        except Exception as e:
            print(f"💥 Error: {e}")
            import traceback
            traceback.print_exc()

def test_bool_op_file():
    """Prueba el archivo bool_op.logo completo"""
    
    print("\n" + "="*60)
    print("TEST DEL ARCHIVO bool_op.logo COMPLETO")
    print("="*60)
    
    try:
        # Leer el archivo de prueba
        with open('frontend/examples/bool_op.logo', 'r', encoding='utf-8') as f:
            code = f.read()
        
        print("Código de bool_op.logo:")
        print(code[:200] + "..." if len(code) > 200 else code)
        
        # Parsear y optimizar
        original_ast = parse_text(code)
        print(f"\n✓ AST original parseado ({len(original_ast.children)} nodos principales)")
        
        optimizer = ASTOptimizer()
        optimized_ast = optimizer.optimize(original_ast)
        stats = optimizer.get_optimization_stats()
        
        print(f"\n📊 RESULTADOS GENERALES:")
        print(f"   Optimizaciones aplicadas: {stats['optimizations_applied']}")
        
        # Análisis semántico de ambos ASTs
        orig_diags = analyze(original_ast)
        opt_diags = analyze(optimized_ast)
        
        print(f"   AST original - errores: {len(orig_diags.items)}")
        print(f"   AST optimizado - errores: {len(opt_diags.items)}")
        
        if opt_diags.items:
            print(f"\n⚠ ERRORES EN AST OPTIMIZADO:")
            for item in opt_diags.items:
                print(f"   [{item.level}] Línea {item.line}: {item.msg}")
        else:
            print(f"\n✅ ÉXITO: AST optimizado sin errores semánticos")
            
        # Mostrar estructura simplificada del AST optimizado
        print(f"\n🌳 ESTRUCTURA AST OPTIMIZADO (simplificada):")
        show_simplified_ast(optimized_ast, max_depth=3)
        
    except Exception as e:
        print(f"💥 Error procesando bool_op.logo: {e}")
        import traceback
        traceback.print_exc()

def show_simplified_ast(node, indent=0, max_depth=3):
    """Muestra una versión simplificada del AST"""
    if indent > max_depth:
        return
    
    pad = "  " * indent
    if node.value is not None:
        print(f"{pad}{node.kind}({node.value})")
    else:
        print(f"{pad}{node.kind}")
    
    # Solo mostrar algunos hijos para no sobrecargar
    children_to_show = node.children[:3] if len(node.children) > 3 else node.children
    
    for child in children_to_show:
        show_simplified_ast(child, indent + 1, max_depth)
    
    if len(node.children) > 3:
        print(f"{pad}  ... (+{len(node.children) - 3} más)")

if __name__ == "__main__":
    test_boolean_optimization()
    test_bool_op_file()