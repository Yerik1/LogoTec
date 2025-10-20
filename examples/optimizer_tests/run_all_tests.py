#!/usr/bin/env python3
"""
Script para ejecutar y validar todos los tests del optimizador AST.
"""

import os
import sys
import time
from pathlib import Path

# Agregar el directorio raíz al path  
root_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, root_path)

try:
    from ASTOptimizer import ASTOptimizer
    from frontend.lexer import build_lexer
    from frontend.parser import build_parser
    from frontend.semantics import analyze
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print(f"💡 Asegúrate de ejecutar desde el directorio correcto")
    print(f"📂 Directorio raíz esperado: {root_path}")
    sys.exit(1)

def test_optimization(filepath):
    """
    Ejecuta un test de optimización en el archivo especificado.
    
    Returns:
        tuple: (success, optimizations_count, errors_count, execution_time)
    """
    print(f"\n🔍 Probando: {os.path.basename(filepath)}")
    print("=" * 50)
    
    try:
        start_time = time.time()
        
        # Leer archivo de test
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"📝 Código leído ({len(code)} caracteres)")
        
        # Parsear código original
        parser, lexer = build_parser()
        
        original_ast = parser.parse(code, lexer=lexer)
        if not original_ast:
            print("❌ Error: No se pudo parsear el código original")
            return False, 0, 1, 0
        
        print("✅ AST original parseado correctamente")
        
        # Aplicar optimizaciones
        optimizer = ASTOptimizer()
        optimized_ast = optimizer.optimize(original_ast)
        optimizations_count = optimizer.optimizations_applied
        
        print(f"🔧 Optimizaciones aplicadas: {optimizations_count}")
        
        # Analizar semánticamente el resultado
        if optimized_ast:
            diagnostics = analyze(optimized_ast)
            errors_count = len(diagnostics.items) if diagnostics and diagnostics.items else 0
            
            if errors_count == 0:
                print("✅ AST optimizado sin errores semánticos")
            else:
                print(f"⚠️  AST optimizado - diagnósticos: {errors_count}")
                if diagnostics:
                    for diag in diagnostics.items:
                        print(f"   • [{diag.level}] (línea {diag.line}) {diag.msg}")
        else:
            errors_count = 0
            print("ℹ️  AST optimizado está vacío (código completamente eliminado)")
        
        execution_time = time.time() - start_time
        print(f"⏱️  Tiempo de ejecución: {execution_time:.3f}s")
        
        success = errors_count == 0
        return success, optimizations_count, errors_count, execution_time
        
    except Exception as e:
        print(f"❌ Error durante el test: {str(e)}")
        return False, 0, 1, 0

def main():
    """Ejecuta todos los tests del directorio optimizer_tests."""
    
    print("🚀 Ejecutando Tests del Optimizador AST - LogoTec")
    print("=" * 60)
    
    # Directorio de tests
    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("*.logo"))
    
    if not test_files:
        print("❌ No se encontraron archivos .logo en el directorio de tests")
        return
    
    print(f"📁 Directorio de tests: {tests_dir}")
    print(f"📋 Archivos encontrados: {len(test_files)}")
    
    # Resultados globales
    total_tests = 0
    successful_tests = 0
    total_optimizations = 0
    total_errors = 0
    total_time = 0
    
    results = []
    
    # Ejecutar cada test
    for test_file in sorted(test_files):
        success, opt_count, err_count, exec_time = test_optimization(test_file)
        
        total_tests += 1
        if success:
            successful_tests += 1
        
        total_optimizations += opt_count
        total_errors += err_count
        total_time += exec_time
        
        results.append({
            'file': os.path.basename(test_file),
            'success': success,
            'optimizations': opt_count,
            'errors': err_count,
            'time': exec_time
        })
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    
    print(f"Tests ejecutados: {total_tests}")
    print(f"Tests exitosos: {successful_tests}")
    print(f"Tests fallidos: {total_tests - successful_tests}")
    print(f"Tasa de éxito: {successful_tests/total_tests*100:.1f}%")
    print(f"Total optimizaciones aplicadas: {total_optimizations}")
    print(f"Total errores encontrados: {total_errors}")
    print(f"Tiempo total de ejecución: {total_time:.3f}s")
    
    # Tabla de resultados detallados
    print(f"\n📋 RESULTADOS DETALLADOS")
    print("-" * 60)
    print(f"{'Archivo':<20} {'Estado':<8} {'Opts':<6} {'Errs':<6} {'Tiempo':<8}")
    print("-" * 60)
    
    for result in results:
        status = "✅ OK" if result['success'] else "❌ FAIL"
        print(f"{result['file']:<20} {status:<8} {result['optimizations']:<6} "
              f"{result['errors']:<6} {result['time']:<8.3f}s")
    
    print("-" * 60)
    
    # Código de salida
    if successful_tests == total_tests:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        exit_code = 0
    else:
        print("⚠️  Algunos tests fallaron. Revisar los errores arriba.")
        exit_code = 1
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()