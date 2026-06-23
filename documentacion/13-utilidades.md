# 13 — Utilidades y servicios

Referencia de módulos auxiliares del código.

---

## Login/auditoria.py

| Función | Descripción |
|---------|-------------|
| `obtener_ip_cliente(request)` | IP real vía `X-Forwarded-For` |
| `registrar_auditoria(request, accion, paciente, detalle)` | Crea `AuditoriaAcceso` |
| `auditar_cuestionario_consulta` | Wrapper consulta cuestionario |
| `auditar_cuestionario_edicion` | Wrapper edición cuestionario |

---

## clinicas/utils.py

Filtrado multiclínica — ver `documentacion/06-multiclinica.md`.

---

## clinicas/services.py

| Función | Descripción |
|---------|-------------|
| `crear_clinica_individual(clinico)` | Centro solo al primer login |
| `unir_clinico_a_centro(...)` | Migra pacientes entre centros |
| `convertir_a_centro(clinica)` | Individual → compartido |

---

## clinicas/branding.py

`url_logo_clinica(clinica)` — URL del logo para templates y emails.

---

## clinicas/context_processors.py

`clinica_sesion` — flags de permisos para menú.

---

## PanelDeControl/metricas_panel.py

`obtener_metricas_panel(request)` — KPIs del dashboard:

- Total pacientes del centro
- Citas hoy / semana
- Anamnesis nuevas del mes (vía `formularioClinico.fechaCreacion`)
- Sesiones kinésicas registradas

---

## PanelDeControl/exportacion.py

`exportar_paciente_json_bytes(paciente)` — JSON ARCO versión `kenkomed-arco-v1`.

Agrega: demografía, anamnesis, cuestionarios, sesiones, reservas, receta, notas.

---

## PanelDeControl/auditoria_pdf.py

`generar_auditoria_pdf(clinica, registros, dias, generado_por)` — PDF landscape A4 con ReportLab.

---

## TiposDeFormularios/psfs_utils.py

| Función | Descripción |
|---------|-------------|
| `scores_from_post(request.POST)` | Lee puntajes del formulario |
| `initial_psfs_scores(puntajes)` | Primera sesión |
| `append_psfs_scores(cuestionario, puntajes)` | Nueva sesión seguimiento |
| `replace_last_psfs_session(cuestionario, puntajes)` | Sobrescribe última |
| `build_psfs_sessions(cuestionario)` | Lista para plantilla |
| `psfs_chart_series(cuestionario)` | Datos para gráfico |
| `repair_psfs_stored_totals(cuestionario)` | Corrige totales corruptos |

---

## ProyectoMainAPP/email_service.py

Funciones `notificar_*` — ver `documentacion/10-correos.md`.

---

## ProyectoMainAPP/error_handlers.py

- `handler400/403/404/500` — renderizan `templates/errors/page.html`
- `csrf_failure` — mensaje amigable token expirado
- `preview_error` — solo DEBUG

---

## ProyectoMainAPP/decorators/login_requerido.py

`@requiere_clinico`, `@requiere_admin_clinica`, `@requiere_admin_auditoria`.

---

## PanelDeControl/views.py — Helpers DSS

Funciones usadas en informes y ficha (no son vistas):

| Función | Propósito |
|---------|-----------|
| `EscalaSemaforo` | Interpretación semáforo integrado |
| `CreenciaDolor` | Catastrofización / creencias |
| `Neuropaticas` | Características dolor neuropático |
| `condicionesSalud` | Comorbilidades y recomendaciones |
| `Respuesta_evitativo_persistente` | EVPER conducta ante dolor |
| `evaluar_necesidad_apoyo` | Red de apoyo |

---

## Login/templatetags/form_utils.py

Tags para inputs de RUT y contraseña con formato chileno.

---

## Comandos de gestión (`Login/management/commands/`)

| Comando | Uso |
|---------|-----|
| `hash_passwords --yes` | Migrar contraseñas texto plano a hash |
| `cambiar_rut_clinico` | Cambiar RUT de un clínico en BD |

---

## PanelDeControl/middleware.py

`NoCacheMiddleware` — cabeceras anti-caché en respuestas.

---

## Dependencias (`requirements.txt`)

```
Django>=5.1.5
mysqlclient>=2.2.7
qrcode[pil]>=7.4.2
Pillow>=10.0.0
python-dotenv>=1.0.0
reportlab>=4.0.0
```
