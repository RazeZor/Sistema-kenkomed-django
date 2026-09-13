# 08 — Cuestionarios clínicos

Todos se acceden desde el **historial clínico** del paciente con `?rut=`.  
**Archivo principal:** `TiposDeFormularios/views.py`  
**Clase base:** `BaseEvaluacionHandler` — validación de sesión, obtención de paciente, helpers de auditoría.

---

## Resumen de instrumentos

| Cuestionario | URL | Modelo | Sesiones |
|--------------|-----|--------|----------|
| GROC | `/CuestionarioGROC/` | `Login.Groc` | Lista de puntajes |
| PSFS | `/CuestionarioPSFS/` | `Login.CuestionarioPSFS` | Múltiples (utils) |
| EQ-5D | `/CuestionarioEQ_5D/` | `Login.CuestionarioEQ_5D` | Listas por dimensión |
| Barthel | `/CuestionarioBarthel/` | `Login.CuestionarioBarthel` | JSON por ítem |
| Screening | `/CuestionarioScrenning/` | `Login.CuestionarioScrenning` | Una evaluación (actualizable) |
| ENA | `/CuestionarioENA/` | `Login.CuestionarioEvaluacionENA` | JSON `estado_por_sesion` |
| Oswestry (ODI) | `/CuestionarioOswestry/` | `TiposDeFormularios.EvaluacionOswestry` | N evaluaciones |
| LEFS | `/CuestionarioLEFS/` | `TiposDeFormularios.EvaluacionLEFS` | N evaluaciones |

---

## GROC (Global Rating of Change)

- Escala única de percepción de cambio.
- Acciones POST: `guardar`, `actualizar` (append puntaje), `GuardarNota`.
- Gráfico de evolución en historial/estadísticas.

---

## PSFS (Patient-Specific Functional Scale)

**Utilidades:** `TiposDeFormularios/psfs_utils.py`

- 3 actividades definidas por el clínico.
- Puntaje 0–10 por actividad; total = promedio (máx. 10).
- **Nueva sesión:** checkbox `nueva_sesion` → append.
- **Actualizar sin checkbox:** reemplaza última sesión (`replace_last_psfs_session`).
- `repair_psfs_stored_totals()` corrige totales corruptos al cargar.
- `build_psfs_sessions()` / `psfs_chart_series()` para UI y gráficos.

---

## EQ-5D

- 5 dimensiones + VAS.
- Primera vez: `action=guardar`.
- Seguimiento: `action=actualizar` — append a listas por campo.

---

## Índice de Barthel

- 10 actividades de vida diaria (0–3 o según ítem).
- Puntaje total y grado de dependencia (Total, Grave, Moderado, Leve, Independiente).
- Sesiones almacenadas como JSON en cada campo.

---

## Screening (Örebro)

- Intensidad dolor, 8 preguntas funcionales Sí/No, nivel de molestia.
- `calcular_puntaje()` — riesgo bajo/medio/alto.
- `generar_alerta()` — HTML de alerta clínica en plantilla.
- Una evaluación por paciente (OneToOne); se actualiza con `action=actualizar`.

---

## ENA (Escala de Necesidad de Atención)

- Registros en `estado_por_sesion` con `level`, `description`, `timestamp`, `session`.
- Acciones: `guardar`, `delete` (por índice), `clear` (limpiar historial).
- Datos inyectados como `evaluations_json` en plantilla.

---

## Oswestry Disability Index (ODI)

**Modelo:** `EvaluacionOswestry` — 10 secciones, 0–5 puntos.

- Múltiples evaluaciones por paciente ordenadas por `fecha_evaluacion`.
- `get_porcentaje_incapacidad()`, `get_interpretacion()` — nivel de discapacidad lumbar.
- Gráfico de evolución en plantilla (`evaluations_json`).

---

## LEFS (Lower Extremity Functional Scale)

**Modelo:** `EvaluacionLEFS` — 20 actividades, 0–4 puntos cada una.

- Total 0–80 puntos; porcentaje de funcionalidad.
- `get_interpretacion()` — nivel y recomendación clínica.
- Múltiples evaluaciones con gráfico temporal.

---

## Auditoría en cuestionarios

- **Consulta (GET):** `consulta_cuestionario` — detalle = nombre del instrumento.
- **Edición (POST exitoso):** `edicion_cuestionario` — detalle = instrumento + subacción (ej. "nueva sesión").

---

## Plantillas

Ubicación: `TiposDeFormularios/templates/`

- `GROC.html`, `CuestionarioPSFS.html`, `CuestionarioEQ-5D.html`, etc.
- Parciales en `partials/` para PSFS.

---

## Admin

`TiposDeFormularios/admin.py` registra `EvaluacionOswestry` y `EvaluacionLEFS` para soporte.

---

## Timed Up and Go Test (TUG)

### Descripción
Prueba funcional de movilidad y riesgo de caída. El paciente parte sentado, se levanta, camina 3 metros, gira y regresa a sentarse. Se mide el tiempo en segundos.

### Modelo: `EvaluacionTUG`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tiempo_segundos` | `FloatField` | Tiempo total del test (admite décimas) |
| `usa_ayuda_marcha` | `BooleanField` | Si usó bastón, andador, etc. |
| `observaciones` | `JSONField` | Lista de observaciones clínicas seleccionadas |
| `notas_clinicas` | `TextField` | Notas libres del clínico |
| `ciclo` | `ForeignKey` | Ciclo clínico asociado |
| `clinico` | `ForeignKey` | Clínico que aplicó el test |
| `paciente` | `ForeignKey` | Paciente evaluado |

### Baremos clínicos

| Tiempo | Riesgo | DSS status |
|--------|--------|------------|
| < 10 s | Sin riesgo de caída | `success` |
| 10–12 s | Riesgo leve | `warning` |
| 12–20 s | Riesgo moderado de caída | `danger` |
| > 20 s | Riesgo severo / dependencia funcional | `danger` |

Referencia: Podsiadlo & Richardson (1991). Punto de corte ≥12 s para riesgo de caída en adultos mayores.

### Método DSS: `get_interpretacion()`
Retorna un dict con: `nivel`, `riesgo`, `color`, `rango`, `descripcion`, `recomendacion`, `dss_status`, `dss_bullets`.

### URL
```
/CuestionarioTUG/?rut=<rut>   [GET + POST]
name='tug'
```

### Integración en sesiones kinésicas
- Código: `'tug'`
- Paquete: `extremidad_inferior` (junto a LEFS y WOMAC)
- Aparece en `RegistroEscalaSesion.TIPOS_ESCALA`

### Gráfico de evolución
Builder `_tug` en `escalas_graficos.py`. Produce serie de `tiempo_segundos` vs `fecha_evaluacion` en color naranja clínico (`#f97316`).

### Observaciones clínicas disponibles (checkboxes)
1. Paso tentativo lento
2. Apoyo en paredes
3. Pérdida de equilibrio
4. Arrastre de pies
5. Pasos cortos
6. Sin balanceo de brazos
7. Vuelta en bloque
8. No usa dispositivo de ayuda correctamente

---

## 6. Escala de Equilibrio de Berg (Berg Balance Scale - BBS)

### Modelo
`EvaluacionBerg` (`TiposDeFormularios.models`)

### Estructura
- 14 tareas de equilibrio funcional evaluadas de 0 a 4 puntos.
- Puntaje Total: 0 a 56 puntos. Mayor puntaje = mejor equilibrio postural.

### Baremos de Riesgo de Caídas
- **0 - 20 pts**: Alto riesgo de caída.
- **21 - 40 pts**: Moderado riesgo de caída (12 veces más probabilidad de caída).
- **41 - 56 pts**: Leve / Bajo riesgo de caída.

### Grupos de Capacidad Motora
- **55 - 56 pts**: Marcha funcional
- **50 - 54 pts**: Marcha independiente
- **45 - 49 pts**: Marcha con/sin ayudas técnicas
- **40 - 44 pts**: Grupo de inicio de marcha
- **33 - 39 pts**: Grupo de inicio de bipedestación
- **< 33 pts**: Control postural inicial / sedestación

### URL
```
/CuestionarioBerg/?rut=<rut>   [GET + POST]
name='berg'
```

### Integración en sesiones kinésicas
- Código: `'berg'`
- Paquete: `equilibrio_marcha` (junto a Tinetti y TUG)

---

## 7. Escala de Tinetti (Equilibrio y Marcha)

### Modelo
`EvaluacionTinetti` (`TiposDeFormularios.models`)

### Estructura
- **Subescala de Equilibrio**: 9 tareas (0 a 1 o 0 a 2 pts) — Puntuación Máx: 16 pts.
- **Subescala de Marcha**: 7 tareas (0 a 1 o 0 a 2 pts) — Puntuación Máx: 12 pts.
- **Puntuación Total**: 0 a 28 puntos.

### Baremos de Riesgo de Caídas
- **≤ 18 pts**: Alto riesgo de caída.
- **19 - 24 pts**: Moderado riesgo de caída.
- **25 - 28 pts**: Bajo / Sin riesgo de caída.

### URL
```
/CuestionarioTinetti/?rut=<rut>   [GET + POST]
name='tinetti'
```

### Integración en sesiones kinésicas
- Código: `'tinetti'`
- Paquete: `equilibrio_marcha` (junto a Berg y TUG)

