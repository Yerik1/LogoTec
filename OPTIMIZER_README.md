# Optimizador de AST para LogoTec

## Descripción

El optimizador de AST es una herramienta que mejora automáticamente el código Logo aplicando varias técnicas de optimización sin cambiar la funcionalidad del programa.

## Características del Optimizador

### 1. **Constant Folding (Plegado de Constantes)**
Evalúa expresiones constantes en tiempo de compilación:
```logo
INIC x = 2 + 3 * 4    →    INIC x = 14
INIC y = (10 - 5) / 2  →    INIC y = 2.5
```

### 2. **Algebraic Simplification (Simplificación Algebraica)**
Aplica identidades matemáticas para simplificar expresiones:
```logo
x + 0    →    x
x * 1    →    x
x * 0    →    0
x / 1    →    x
x - x    →    0  (para variables simples)
```

### 3. **Dead Code Elimination (Eliminación de Código Muerto)**
Elimina código que no tiene efecto:
```logo
AV 0     →    (eliminado)
GD 0     →    (eliminado)
RE 0     →    (eliminado)
```

### 4. **Control Flow Optimization (Optimización de Flujo de Control)**
Optimiza estructuras de control:
```logo
REPITE 0 [ ... ]    →    (eliminado)
REPITE 1 [ AV 10 ]  →    AV 10
```

### 5. **Command Normalization (Normalización de Comandos)**
Convierte comandos a formas más eficientes:
```logo
RE 10    →    AV -10
GI 45    →    GD -45
```

### 6. **Boolean Logic Optimization (Optimización de Lógica Booleana)**
Simplifica expresiones booleanas:
```logo
true Y x     →    x
false O x    →    x
x IGUALES x  →    true  (para variables simples)
```

## Cómo Usar el Optimizador

### En la Aplicación GUI:

1. **Escribir código**: Escribe tu programa Logo en el editor
2. **Compilar**: Haz clic en "Compilar" para generar el AST
3. **Optimizar**: Haz clic en "Optimizar" para aplicar optimizaciones
4. **Ver resultados**: El optimizador mostrará:
   - Número de optimizaciones aplicadas
   - AST original vs. AST optimizado
   - Análisis semántico del código optimizado

### Desde Código Python:

```python
from frontend.parser import parse_text
from ASTOptimizer import ASTOptimizer

# Parsear código
ast = parse_text("INIC x = 2 + 3")

# Crear optimizador
optimizer = ASTOptimizer()

# Optimizar
optimized_ast = optimizer.optimize(ast)

# Ver estadísticas
stats = optimizer.get_optimization_stats()
print(f"Optimizaciones aplicadas: {stats['optimizations_applied']}")
```

## Ejemplo Completo

**Código Original:**
```logo
INIC x = 2 + 3
INIC y = x * 1
INIC z = y + 0
AV 10 + 5
RE 0
GD 90 * 1
REPITE 1 [
    AV 20
    GD 90
]
REPITE 0 [
    AV 100
]
```

**Código Optimizado:**
```logo
INIC x = 5
INIC y = x
INIC z = y
AV 15
GD 90
AV 20
GD 90
```

## Archivos Generados

El optimizador genera los siguientes archivos en la carpeta `out/`:

- `ast.json`: AST original
- `ast_optimized.json`: AST optimizado
- `diagnostics.txt`: Diagnósticos del AST original
- `diagnostics_optimized.txt`: Diagnósticos del AST optimizado

## Beneficios

1. **Código más eficiente**: Menos operaciones en tiempo de ejecución
2. **Mejor rendimiento**: Evaluaciones constantes pre-calculadas
3. **Código más limpio**: Eliminación de operaciones redundantes
4. **Detección de errores**: El análisis puede revelar código problemático
5. **Facilita debugging**: Código simplificado es más fácil de entender

## Limitaciones

- Solo optimiza expresiones y comandos seguros
- No optimiza cuando hay posibles efectos secundarios
- Preserva la semántica original del programa
- Algunos patrones complejos pueden no ser detectados

## Testing

Para probar el optimizador:

```bash
python test_optimizer.py
```

Este script ejecuta una suite de pruebas que verifican las diferentes optimizaciones implementadas.