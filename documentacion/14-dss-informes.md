# 14 — DSS e informes

## Sistema de Soporte a Decisiones (DSS)

El DSS analiza la **anamnesis inicial** (`formularioClinico`) y genera alertas y recomendaciones clínicas automáticas en:

- **Informe DSS** (`/informe/?rut=`)
- **Ficha clínica profesional** (`/ficha-clinica/?rut=`)
- **Resumen en panel** (`/panel/fichaPacientes/?rut=`)

La lógica vive principalmente en `PanelDeControl/views.py` y `PanelDeControl/views_informe.py`.

---

## Validación robusta

El DSS **no analiza campos vacíos**. Cada evaluación:

1. Verifica que el valor exista y no sea string vacío.
2. Incrementa contador `campos_evaluados` solo con datos válidos.
3. Retorna estado `info` si no hay datos suficientes.

Esto evita falsos positivos cuando el paciente dejó preguntas en blanco.

---

## Módulos de interpretación

### Semáforo integrado (`EscalaSemaforo`)

Analiza respuestas del semáforo de banderas rojas en anamnesis. Clasifica riesgo y sugiere derivación.

### Creencias sobre el dolor (`CreenciaDolor`)

Si el paciente cree tener un problema no diagnosticado → alerta de posible catastrofización. Recomienda PCS (Pain Catastrophizing Scale).

### Dolor neuropático (`Neuropaticas`)

A partir de `caracteristicasDeDolor` JSON detecta patrones neuropáticos y recomienda evaluación específica.

### Condiciones de salud (`condicionesSalud`)

Cruza `TiposDeEnfermedades` con tabla de recomendaciones (fibromialgia, diabetes, etc.).

### Conducta EVPER (`Respuesta_evitativo_persistente`)

Clasifica patrón **evitativo** (kinesiofobia) vs **persistente** (boom-bust) vs equilibrado. Incluye recomendaciones de manejo (exposición gradual, pacing, etc.).

### Necesidad de apoyo (`evaluar_necesidad_apoyo`)

Evalúa red de apoyo social declarada en anamnesis.

### Sustancias

Interpretación de preocupación por nicotina, alcohol, drogas, marihuana cuando están declaradas.

---

## Informe DSS

**Vista:** `RenderInforme`  
**Plantilla:** `PanelDeControl/templates/informe.html`

Contenido:
- Datos del paciente y clínica (logo).
- Secciones de anamnesis estructurada.
- Bloques DSS con colores: success / warning / danger / info.
- Recomendaciones de cuestionarios complementarios.

---

## Ficha clínica profesional

**Vista:** `RenderFichaClinica`  
**Plantilla:** `PanelDeControl/templates/ficha_clinica.html`

Documento más completo que el informe:
- Toda la anamnesis.
- Resultados de cuestionarios si existen.
- Sesiones kinésicas resumidas.
- Receta y notas.
- Usado para exportación ARCO HTML.

---

## Estadísticas derivadas del DSS

`estadisticas` (centro) agrega de todos los formularios del centro:

- Distribución género.
- Top ubicaciones de dolor.
- Intensidad promedio.
- Patrones de sueño, conducta, etc.

`estadisticas_paciente` muestra evolución longitudinal de PSFS, GROC, ENA, Screening.

---

## Extender el DSS

Para añadir una nueva regla:

1. Crear función interpretadora en `views.py` o `views_informe.py` que retorne dict con `status`, `title`, `message`, opcionalmente `bullets` / `recommendations`.
2. Llamarla desde `RenderInforme` y `RenderFichaClinica` con datos del `formularioClinico`.
3. Añadir bloque correspondiente en plantillas `informe.html` / `ficha_clinica.html`.

Mantener siempre validación de campos vacíos antes de interpretar.
