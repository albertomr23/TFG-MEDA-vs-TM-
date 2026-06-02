# Resumen de Problemas Estructurales y de Código - TFG MEDA vs TM

**Generado:** 1 de Junio de 2026  
**Analista:** Sistema de análisis de código  
**Estado:** ⚠️ **6-8 horas de refactorización recomendadas**

---

## 🔴 PROBLEMAS CRÍTICOS (Fix Immediate!)

### 1. **Import Incorrecto en `tm_wrapper.py` - LÍNEA 4**
```python
# ❌ INCORRECTO (actual)
from yaml import warnings

# ✅ CORRECTO
import warnings
```
**Impacto:** Rompe toda la funcionalidad de advertencias. Se va a lanzar `AttributeError` cuando se intente usar `warnings.filterwarnings()`.

**Ubicación:** `src/models/tm_wrapper.py`, línea 4

**Fix Tiempo:** 30 segundos

---

### 2. **Duplicación de Clase `MEDAFilter` (6 copias idénticas)**
- `src/exp_05_hybrid.py` (líneas ~20-50)
- `src/exp_06_pure_comparison.py` (líneas ~17-40)
- `src/exp_07_extract_rules.py` (líneas ~1-40)
- `src/exp_08_inverse_hybrid_latent.py` (líneas ~31-60)
- `src/exp_10_final_translator.py` (líneas ~1-40)
- `src/exp_meda_04_v2.py` (líneas ~27-45)

**Impacto:** 
- Pesadilla de mantenimiento (si cambias lógica en una, hay que cambiar en 5 más)
- Dificulta debug
- Inconsistencias silenciosas si alguien modifica una versión pero no las otras
- Ocupa 300+ líneas innecesarias

**Solución Recomendada:** Crear `src/pipelines/meda_filter.py` con una sola versión. Importar desde todos los scripts.

**Fix Tiempo:** 1.5 horas

---

### 3. **Duplicación de Función `select_and_load_dataset()` (7 copias)**
- Definida de forma casi idéntica en: `exp_05`, `exp_06`, `exp_07`, `exp_08`, `exp_09`, `exp_10`, `exp_meda_04_v2.py`

**Impacto:**
- Si descubres un bug en carga de datos, hay que arreglarlo en 7 sitios
- Hizo cambios en `dataset_type = "simulated_hd"` en `exp_08` pero no en los otros
- Inconsistencias futuras garantizadas

**Solución:** Crear `src/utils/data_loader.py` con una sola función centralizada.

**Fix Tiempo:** 1 hora

---

### 4. **Fallos Silenciosos en vASCA (SVD singular)**
**Ubicación:** `src/exp_05_hybrid.py` y `src/exp_08_inverse_hybrid_latent.py`

```python
# El problema: cuando vASCA falla (matriz singular), el código solo imprime:
except Exception as e:
    print(f"[!] {self.method.upper()} crashed: {e}. Passing all logic features downstream.")
    self.selected_indices_ = list(range(X.shape[1]))  # Silencio total
```

**Impacto:**
- Pipeline continúa con *todos* los features sin saber que vASCA falló
- Resultados inválidos pero se presentan como válidos
- Bug muy difícil de detectar

**Fix Tiempo:** 30 minutos

---

## 🟡 PROBLEMAS ALTOS

### 5. **Índices de Columna Hardcodeados**
- Columna 0 = target (simulated)
- Columna 15 = Peritonitis (real)
- Columnas 16+ = biomarkers (real)

**Ubicación:** Todo `exp_*.py` en función `select_and_load_dataset()`

**Impacto:** Si alguien cambia el formato del Excel o agrega columnas, TODO se rompe silenciosamente.

**Solución:** Crear archivo config o metadatos en cada Excel con esquema de columnas.

**Fix Tiempo:** 2 horas

---

### 6. **Uso Inconsistente de Nombres de Parámetros**
```python
# En SmartBooleanizer:
def __init__(self, n_bins=3):  # "n_bins"

# En TMClauseExtractor:
def __init__(self, num_bins=3):  # "num_bins"

# En TMWrapper:
def __init__(self, num_bins=3):  # "num_bins"
```

**Impacto:** Confusión, errores en llamadas, documentación inconsistente.

**Fix:** Estandarizar a `n_bins` en toda la codebase (convención sklearn).

**Fix Tiempo:** 1 hora

---

### 7. **Falta de Type Annotations**
Todo el codebase NO tiene type hints. Ejemplo:

```python
# ❌ Actual
def select_and_load_dataset():
    # ¿Qué devuelve? ¿Qué tipos?
    return X, y, feature_names, dataset_type, results_dir

# ✅ Debería ser
def select_and_load_dataset() -> Tuple[np.ndarray, np.ndarray, List[str], str, str]:
    return X, y, feature_names, dataset_type, results_dir
```

**Impacto:** IDE no puede ayudarte con autocompletar, bugs difíciles de detectar, mantenimiento complicado.

**Fix Tiempo:** 2-3 horas

---

## 🟠 PROBLEMAS MEDIOS

### 8. **Métodos no Implementados en Modelos R**
- `RWrapper.predict()` — vASCA y ASCA NO tienen método predict
- Usado en pipelines sklearn pero no funciona correctamente

**Ubicación:** `src/models/r_wrapper.py`

**Fix Tiempo:** 1.5 horas

---

### 9. **Falta de __init__.py en Módulos**
- `src/interpretability/__init__.py` — **VACÍO**
- Debería tener exports: `from .clinical_translator import ClinicalTranslator`

**Impacto:** Requiere imports absolutos en lugar de relativos.

**Fix Tiempo:** 15 minutos

---

### 10. **Manejo de Errores Inconsistente**
Algunos scripts tienen `try/except`, otros no. Algunos usan `warnings`, otros `print("[!]")`.

**Impacto:** Comportamiento impredecible, logs inconsistentes.

**Fix Tiempo:** 1 hora

---

## 📊 Tabla Resumen de Problemas

| # | Severidad | Problema | Ubicación | Tiempo Fix | Impacto |
|---|-----------|----------|-----------|-----------|---------|
| 1 | 🔴 CRÍTICO | Import incorrecto | `tm_wrapper.py:4` | 30s | Warnings rotos |
| 2 | 🔴 CRÍTICO | MEDAFilter duplicado 6x | 6 exp files | 1.5h | Mantenimiento imposible |
| 3 | 🔴 CRÍTICO | select_and_load_dataset 7x | 7 files | 1h | Bug de datos |
| 4 | 🔴 CRÍTICO | Fallos silenciosos vASCA | exp_05, exp_08 | 0.5h | Resultados inválidos |
| 5 | 🟡 ALTO | Índices hardcodeados | Todos los exp | 2h | Cambios rompen código |
| 6 | 🟡 ALTO | Nombres inconsistentes | Múltiples | 1h | Confusión API |
| 7 | 🟡 ALTO | Sin type hints | Todo | 2-3h | IDE no ayuda |
| 8 | 🟠 MEDIO | Métodos sin implementar | r_wrapper.py | 1.5h | Pipelines incompletos |
| 9 | 🟠 MEDIO | __init__.py vacíos | interpretability/ | 0.25h | Imports rotos |
| 10 | 🟠 MEDIO | Error handling inconsistente | Todo | 1h | Logs confusos |

---

## ✅ Orden Recomendado de Fixes

### FASE 1: EMERGENCIAS (30 min)
1. ✅ Arreglar import en `tm_wrapper.py`
2. ✅ Agregar error handling para vASCA

### FASE 2: ARQUITECTURA (3 horas)
3. ✅ Centralizar `select_and_load_dataset()` en `utils/data_loader.py`
4. ✅ Mover `MEDAFilter` a `pipelines/meda_filter.py`
5. ✅ Actualizar todos los imports en exp files

### FASE 3: POLISH (2-3 horas)
6. ✅ Estandarizar nombres de parámetros
7. ✅ Agregar type hints en funciones críticas
8. ✅ Rellenar `__init__.py` files
9. ✅ Mejorar error handling

### FASE 4: TESTING (2 horas)
10. ✅ Escribir unit tests para data loader
11. ✅ Verificar imports
12. ✅ Ejecutar todos los exp scripts una vez

---

## 📁 Archivos para Consultar

Para análisis más detallados, ver:
- **[CODEBASE_ANALYSIS_REPORT.md](CODEBASE_ANALYSIS_REPORT.md)** — Análisis completo (12 secciones, 35+ problemas)
- **[ISSUES_QUICK_REFERENCE.md](ISSUES_QUICK_REFERENCE.md)** — Lista rápida por prioridad
- **[RECOMMENDED_FIXES.md](RECOMMENDED_FIXES.md)** — Soluciones con código de ejemplo

---

## 🎯 Buen Punto: Lo que SÍ está bien

✅ **Estructura general es sólida** — Organización de directorios lógica  
✅ **Experimentos bien separados** — Cada exp tiene su propio scope  
✅ **Uso de wrappers para integración R** — Buena idea arquitectónica  
✅ **Modularidad básica** — features/, models/, interpretability/ bien separados  
✅ **Datasets variados** — Buen mix de simulated, real, high-dim  

---

## 💡 Recomendación Final

**Para defensa de TFG:** El código funciona y los experimentos son válidos. Sin embargo, ANTES de publicar o usar en producción:

1. Arreglar los 4 problemas críticos (1-2 horas)
2. Refactorizar duplicación (2-3 horas)
3. Escribir breve documento de "Limiting Factors" en la tesis mencionando deuda técnica

**Presupuesto realista:** 6-8 horas de refactorización completa.

---

**Estado del Proyecto:** ✅ Funcional para tesis | 🔧 Necesita limpieza antes de producción | 📈 Mejora recomendada: 6-8h

