# ADR 001 — Ciclos clínicos

**Estado:** Aceptado  
**Fecha:** 2026  
**Contexto:** KenkoMed necesitaba soportar múltiples episodios de tratamiento por paciente (reingresos) sin perder el historial del episodio anterior.

---

## Contexto

El sistema original modelaba la anamnesis (`formularioClinico`), cuestionarios legacy y sesiones kinésicas con relación directa al `Paciente` (1:1 o 1:N global). Un segundo episodio sobrescribía o mezclaba datos del primero.

Se requería:

- Separar episodios de tratamiento por paciente y centro.
- Permitir consulta histórica de episodios cerrados (solo lectura).
- Minimizar ruptura con datos existentes en producción.

---

## Decisión 1 — App separada `ciclos_clinicos`

**Decisión:** Crear la app Django `ciclos_clinicos` con el modelo `CicloClinico`, capa `services`/`selectors` y endpoints propios. Los modelos existentes en `Login`, `SesionesKinesicas` y `TiposDeFormularios` reciben FK/OneToOne a `CicloClinico`.

**Motivos:**

- La lógica de ciclo de vida (iniciar, cerrar, resolver desde request) es un dominio acotado y reutilizable.
- Evita inflar aún más `Login/views.py` o `PanelDeControl`.
- Facilita tests unitarios de reglas de negocio (`test_services.py`).

**Alternativa descartada:** Agregar solo un campo `episodio` numérico en cada modelo sin entidad central — difícil de garantizar consistencia y un solo activo.

---

## Decisión 2 — Un solo ciclo activo por paciente y clínica

**Decisión:** Restricción parcial en BD (`UniqueConstraint` con `condition=estado='activo'`) más validación en `iniciar_nuevo_ciclo()`.

**Motivos:**

- Refleja la práctica clínica: un paciente tiene un tratamiento en curso a la vez en un centro.
- Simplifica la resolución por defecto (`obtener_ciclo_activo`) cuando no hay `ciclo_id` en la URL.
- Evita ambigüedad al guardar anamnesis o sesiones.

**Estados:**

| Estado | Editable | Transiciones desde activo |
|--------|----------|---------------------------|
| `activo` | Sí | → `finalizado`, `abandonado` |
| `finalizado` | No (solo lectura) | — |
| `abandonado` | No (solo lectura) | — |

---

## Decisión 3 — `Notas` y `RecetaMedica` permanecen globales al paciente

**Decisión:** No agregar FK a `CicloClinico` en `Notas` ni `RecetaMedica`. Siguen siendo OneToOne con `Paciente`.

**Motivos:**

- **Notas:** campo libre de apuntes del profesional, no vinculado a un episodio específico; el clínico espera un único bloc de notas transversal.
- **Receta médica:** representa la prescripción vigente del paciente; duplicarla por ciclo generaría confusión sobre cuál receta imprimir.
- Menor impacto en vistas y plantillas ya existentes (`/RecetaMedica/`, edición de notas en historial).

**Consecuencia:** al consultar un ciclo histórico, las notas y la receta mostradas son las **actuales** del paciente, no una snapshot del episodio. Si en el futuro se requiere historial de recetas por episodio, sería un cambio de modelo aparte.

**Alternativa descartada:** OneToOne receta/ciclo — obligaría a migrar recetas existentes y re-pensar la UI de receta única.

---

## Decisión 4 — Resolución de ciclo vía `ciclo_id` + sesión

**Decisión:** Parámetro de query `ciclo_id` con fallback a `session['ciclo_activo_id']` y luego ciclo activo del centro.

**Motivos:**

- URLs compartibles y marcables (`?rut=&ciclo_id=`).
- El selector de historial persiste la elección en sesión para navegación subsiguiente.
- Compatible con formularios POST (`ciclo_id` oculto).

---

## Consecuencias

### Positivas

- Reingresos con historial intacto por episodio.
- Informes DSS y exportación ARCO pueden acotarse a un ciclo.
- Migración `0002_backfill` preservó datos legacy en ciclo #1.

### Negativas / deuda

- Modelos legacy mantienen `paciente` además de `ciclo` (transición); conviene filtrar siempre por ciclo en código nuevo.
- `Notas`/`RecetaMedica` globales pueden confundir al revisar ciclos antiguos.
- Estadísticas de centro agregadas sobre anamnesis pueden requerir revisión para no contar múltiples formularios por paciente.

---

## Referencias

- Documentación funcional: [16 — Ciclos clínicos](../16-ciclos-clinicos.md)
- Migración backfill: `ciclos_clinicos/migrations/0002_backfill_ciclos_existentes.py`
- Tests: `ciclos_clinicos/tests/test_services.py`
