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

## Archivos Generados

El optimizador genera los siguientes archivos en la carpeta `out/`:

- `ast_optimized.json`: AST optimizado
- `diagnostics_optimized.txt`: Diagnósticos del AST optimizado

## Limitaciones

- Solo optimiza expresiones y comandos seguros
- No optimiza cuando hay posibles efectos secundarios
- Preserva la semántica original del programa
- Algunos patrones complejos pueden no ser detectados

## Testing

Para probar el optimizador se pueden cargar los archivos de prueba que se encuentran en examples/optimizer_test/.
