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
