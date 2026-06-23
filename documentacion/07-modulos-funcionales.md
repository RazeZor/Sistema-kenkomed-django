# 07 — Módulos funcionales

## Panel de control (`PanelDeControl`)

### Dashboard — `panel`

**Archivo:** `views.py`  
**Métricas:** `metricas_panel.py`

Muestra:
- Nombre y profesión del clínico.
- Próximas citas (8 siguientes).
- KPIs: pacientes totales, citas hoy/semana, anamnesis del mes, sesiones kinésicas.

Las métricas respetan el alcance: admin centro ve todo el centro; miembro ve su actividad.

### Historial clínico — `HistorialClinico`

Hub central del paciente (`?rut=`):

- Datos demográficos y accesos rápidos.
- Enlaces a todos los cuestionarios.
- Informe DSS, ficha profesional, exportación ARCO (JSON/HTML).
- Notas clínicas editables (POST).
- Selector de sesiones kinésicas.
- Generar formulario remoto.

**Auditoría:** consulta historial, edición notas.

### Resumen paciente — `VerInformePacientes`

Vista `/panel/fichaPacientes/?rut=` con flags DSS derivados de la anamnesis (semáforo, neuropático, etc.).

### Estadísticas

- **`estadisticas`** — Agregados del centro: género, ubicación dolor, intensidad, patrones. Solo admin centro.
- **`estadisticas_paciente_view`** — Gráficos evolutivos PSFS, GROC, ENA, Screening por paciente.

---

## Gestión de pacientes (`views_pacientes.py`)

| Vista | Método | Descripción |
|-------|--------|-------------|
| `MostrarPacientes` | GET | Lista paginada (10 por página) |
| `AgregarPacienteBasico` | GET/POST | Alta con validación RUT chileno |
| `EditarPaciente` | GET/POST | Edición campos básicos |
| `EliminarPaciente` | POST | Borrado con verificación de centro |

Tras alta manual, redirige a historial con `temp_rut_historial` en sesión.

---

## Informes (`views_informe.py`)

### `RenderInforme`

Informe DSS imprimible desde anamnesis. Incluye interpretaciones automáticas (creencias, dolor neuropático, condiciones de salud, EVPER, etc.).

### `RenderFichaClinica`

Ficha clínica profesional consolidada: demografía, anamnesis, cuestionarios, sesiones, receta, notas.

Usada también para exportación ARCO HTML (`auditoria_suprimida` evita doble registro).

---

## Reservas y calendario (`views_reservas.py`)

### Vistas HTML

- `calendario_personal_view` — citas del clínico en sesión.
- `calendario_clinica_view` — todas las citas del centro (permiso requerido).

Plantilla: `calendario.html` con FullCalendar.

### API JSON

| Endpoint | Acción |
|----------|--------|
| `api_obtener_reservas` | Lista eventos (`start`, `end`, `alcance`) |
| `api_crear_reserva` | Crea cita; puede actualizar email paciente |
| `api_mover_reserva` | Reagenda |
| `api_eliminar_reserva` | Cancela |

Validaciones:
- Horario 07:00–21:00.
- Sin solapamiento por clínico.
- Paciente y clínico deben pertenecer al centro.

Correos en hilo background al crear/reagendar/cancelar.

---

## Formulario inicial (`FormularioInicial/views.py`)

### `FormularioInicial`

Anamnesis DSS completa desde el panel:

- GET con `?rut=` precarga paciente existente.
- POST crea paciente nuevo o actualiza existente + guarda `formularioClinico`.

### Flujo QR

1. `generar_token_formulario` — lista pacientes sin anamnesis, crea token.
2. `descargar_qr` — muestra QR y URL copiable.
3. `formulario_publico` — flujo paciente con verificación RUT y consentimiento.
4. `desactivar_token` — invalida enlace.
5. `generar_token_desde_historial` — atajo POST desde historial.

Helpers: `validar_rut`, `validar_campos_obligatorios`, `construir_formulario_desde_post`, `crear_o_actualizar_paciente`.

---

## Sesiones kinésicas (`SesionesKinesicas/views.py`)

| Vista | Descripción |
|-------|-------------|
| `listar_sesiones_paciente` | Índice de sesiones |
| `crear_primera_sesion` | Evaluación inicial extensa (JSON) |
| `crear_sesion_seguimiento` | Notas + evolución |
| `crear_sesion_final` | Alta: diagnóstico, resumen, recomendaciones; dispara email |
| `ver_sesion_kinesica` | Lectura |
| `editar_sesion_kinesica` | Edición |
| `api_sesiones_paciente` | JSON para UI |

---

## Recetas (`RecetasMedicas/views.py`)

Arquitectura en capas:

- `AuthService` — sesión y permisos.
- `PacienteService` — búsqueda por RUT.
- `RecetaService` — CRUD transaccional.
- `RequestProcessor` — orquesta GET/POST.

Una receta por paciente (OneToOne). Notifica por email al crear/actualizar.

---

## Perfil clínico (`clinicos/views.py`)

Vista de solo lectura del profesional logueado en `/clinicos/perfil/`.

---

## Privacidad (`views_privacidad.py`)

Ver `documentacion/09-privacidad-cumplimiento.md`.
