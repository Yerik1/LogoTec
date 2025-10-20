# Tests del Optimizador AST - LogoTec

Este directorio contiene archivos de test específicos para validar cada tipo de optimización implementada en el ASTOptimizer.

## Estructura de Tests

### 1. `const_fold.logo` - Constant Folding (Doblado de Constantes)

**Objetivo**: Verificar que las expresiones aritméticas con valores constantes se evalúen en tiempo de compilación.

**Optimizaciones esperadas**:

- `2 + 3 * 4` → `14`
- `(10 - 5) / 2` → `2.5`

### 2. `alg_simpl.logo` - Algebraic Simplification (Simplificación Algebraica)

**Objetivo**: Verificar que las operaciones algebraicas se simplifiquen usando identidades matemáticas.

**Optimizaciones esperadas**:

- `x + 0` → `x` (identidad aditiva)
- `x * 1` → `x` (identidad multiplicativa)
- `x * 0` → `0` (elemento absorbente)
- `x / 1` → `x` (división por uno)
- `x - x` → `0` (auto-sustracción)

### 3. `dead_code.logo` - Dead Code Elimination (Eliminación de Código Muerto)

**Objetivo**: Verificar que se eliminen instrucciones sin efecto visible.

**Optimizaciones esperadas**:

- `AV 0` → [eliminado]
- `GD 0` → [eliminado]
- `RE 0` → [eliminado]

### 4. `cont_flow.logo` - Control Flow Optimization (Optimización de Flujo de Control)

**Objetivo**: Verificar que se eliminen estructuras de control que nunca se ejecutan.

**Optimizaciones esperadas**:

- `REPITE 0 [...]` → [eliminado completamente]

### 5. `comm_norm.logo` - Command Normalization (Normalización de Comandos)

**Objetivo**: Verificar que los comandos se conviertan a formas más eficientes.

**Optimizaciones esperadas**:

- `RE 10` → `AV -10`
- `GI 45` → `GD -45`

### 6. `bool_op.logo` - Boolean Logic Optimization (Optimización de Lógica Booleana)

**Objetivo**: Verificar que las condiciones booleanas constantes se evalúen y simplifiquen.

**Optimizaciones esperadas**:

- `SI 5 iguales? 5 [...]` → ejecutar directamente el bloque
- `SI 3 mayorque? 7 [...]` → eliminar bloque completo
- Combinación de optimizaciones: boolean + arithmetic + command normalization

## Cómo Ejecutar los Tests

### Método 1: Usando el GUI de LogoTec

1. Abrir LogoTec (`python App.py`)
2. Cargar cualquier archivo de test
3. Compilar (el optimizador se ejecuta automáticamente)
4. Ver el AST optimizado usando el botón "Ver AST"

### Método 2: Usando scripts de prueba

```bash
# Test individual
python test_optimizer.py examples/optimizer_tests/const_fold.logo

# Test de todos los archivos
python test_all_optimizations.py
```

### Método 3: Debugging detallado

```bash
python debug_optimizer.py examples/optimizer_tests/bool_op.logo
```

## Interpretación de Resultados

### Métricas Importantes

- **Optimizaciones aplicadas**: Número total de transformaciones realizadas
- **Errores semánticos**: Debe ser 0 después de la optimización
- **Reducción de nodos AST**: Comparar tamaño antes y después
- **Tiempo de compilación**: Verificar que no se degrade significativamente

### Validación Exitosa

Un test es exitoso cuando:

1. ✅ El AST original se parsea correctamente
2. ✅ Se aplican las optimizaciones esperadas
3. ✅ El AST optimizado pasa el análisis semántico (0 errores)
4. ✅ El comportamiento del programa se mantiene equivalente

## Casos de Prueba Avanzados

### Optimizaciones Combinadas

Varios archivos de test demuestran cómo múltiples optimizaciones pueden aplicarse simultáneamente:

```logo
// Ejemplo de bool_op.logo
SI 6 iguales? 6 [        // Boolean: true → eliminar condicional
    AV 10 + 5           // Arithmetic: → AV 15
    RE 0                // Dead code: → eliminado
    GD 45 * 2           // Arithmetic: → GD 90
]
```

### Futuras Extensiones

Los archivos incluyen casos comentados para:

- Operadores booleanos compuestos (`Y`, `O`)
- Expresiones más complejas
- Anidamiento de optimizaciones

## Troubleshooting

### Errores Comunes

1. **Errores semánticos después de optimización**: Verificar que los nodos AST mantengan la estructura correcta
2. **Optimizaciones no aplicadas**: Revisar que los patrones coincidan exactamente
3. **Falsos positivos**: Asegurar que las optimizaciones no cambien la semántica del programa

### Debug Tips

- Usar `debug_optimizer.py` para ver el AST paso a paso
- Verificar los tokens generados por el lexer
- Comparar ASTs antes y después visualmente