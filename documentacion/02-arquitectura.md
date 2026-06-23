# 02 — Arquitectura

## Visión general

KenkoMed es un **monolito Django** con separación lógica por apps. La mayoría de los modelos de dominio viven en `Login`; las demás apps aportan vistas, plantillas y lógica de negocio específica.

```
                    ┌─────────────────────────────────────┐
                    │         Navegador / Paciente QR      │
                    └──────────────────┬──────────────────┘
                                       │ HTTPS
                    ┌──────────────────▼──────────────────┐
                    │  Cloudflare (Tunnel o proxy) [prod]  │
                    └──────────────────┬──────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         Django (ProyectoMainAPP)                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │ Middleware  │→ │ Decoradores  │→ │   Vistas    │→ │ registrar_auditoria│ │
│  │ Clinica+    │  │ requiere_*   │  │  por app    │  │ email_service    │ │
│  │ NoCache     │  └──────────────┘  └─────────────┘  └──────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │              MySQL 8.0                 │
                    │  Paciente, Clinico, Clinica, formularios │
                    └───────────────────────────────────────┘
```

---

## Apps y responsabilidades

### ProyectoMainAPP

- `settings.py` — configuración, seguridad HTTPS, base de datos, email.
- `urls.py` — enrutamiento principal.
- `email_service.py` — envío de correos HTML.
- `error_handlers.py` — páginas 400/403/404/500 y fallo CSRF.
- `decorators/login_requerido.py` — `@requiere_clinico`, `@requiere_admin_auditoria`.

### Login

Capa de datos central:

- Usuarios (`Clinico`) con contraseña hasheada (no usa `django.contrib.auth.User`).
- Pacientes, reservas, anamnesis (`formularioClinico`), notas, cuestionarios legacy, recetas, auditoría.

### clinicas

- Modelos `Clinica` y `MembresiaClinica`.
- Middleware que sincroniza `clinica_id` en sesión.
- Utilidades de filtrado por centro (`utils.py`).
- Servicios de unión de profesionales a centros (`services.py`).
- Context processor para permisos en plantillas.

### PanelDeControl

- Dashboard y métricas (`metricas_panel.py`).
- Historial clínico, resumen paciente, estadísticas.
- Calendario y API REST de reservas (`views_reservas.py`).
- Exportación ARCO y vista de auditoría (`views_privacidad.py`, `exportacion.py`, `auditoria_pdf.py`).
- Helpers DSS para informes (`views.py`, `views_informe.py`).

### FormularioInicial

- Formulario multi-página de anamnesis DSS.
- Tokens UUID para formulario remoto (`TokenFormulario`).
- Consentimiento de datos (`ConsentimientoDatos`).
- Generación y descarga de QR.

### TiposDeFormularios

- Vistas y plantillas de cada cuestionario.
- Modelos `EvaluacionOswestry` y `EvaluacionLEFS` (múltiples evaluaciones por paciente).
- Utilidades PSFS (`psfs_utils.py`).

### SesionesKinesicas

- Modelo `SesionKinesica` con evaluación inicial JSON, notas, evolución y campos de alta.

### RecetasMedicas

- Vista CRUD de recetas; modelo `RecetaMedica` en `Login.models`.

### clinicos

- Vista de perfil del profesional (`/clinicos/perfil/`).

---

## Middleware

| Middleware | Función |
|------------|---------|
| `ClinicaMiddleware` | Mantiene `clinica_id` y `es_admin_clinica` coherentes con la membresía activa. |
| `NoCacheMiddleware` | Cabeceras anti-caché para evitar volver atrás tras cerrar sesión. |

Orden definido en `settings.py` (estándar Django + custom).

---

## Autenticación

No hay JWT ni OAuth. Es **sesión Django** con claves custom:

- `rut_clinico`, `nombre_clinico`, `es_admin`, `clinica_id`, `clinica_nombre`, `es_admin_clinica`.

Login en `Login.views.validarLogin` — valida RUT + contraseña contra modelo `Clinico`.

---

## Aislamiento de datos (multitenancy)

Cada `Paciente` tiene `clinica_id`. Las consultas pasan por funciones en `clinicas/utils.py`:

- `filtrar_pacientes_por_sesion`
- `obtener_paciente_por_rut`
- `filtrar_auditoria_por_sesion`
- `filtrar_reservas_por_sesion`

Un profesional solo ve datos de su centro activo (salvo admin KenkoMed sin centro en sesión).

---

## Archivos estáticos y media

- **Static:** `static/` → CSS por módulo, `js/utils.js`.
- **Media:** `media/clinicas/logos/` — logos subidos por centro.
- En producción conviene `collectstatic` + Nginx; en DEBUG se sirven vía Django.

---

## Decisiones de diseño

1. **Modelos concentrados en Login** — histórico del proyecto; apps satélite solo vistas.
2. **JSONField / TextField JSON** — muchos cuestionarios guardan series temporales como listas JSON.
3. **Auditoría transversal** — `registrar_auditoria()` llamado desde vistas, no middleware automático (más explícito y con contexto).
4. **Admin Django oculto** — URL `/administradordjangogeneral` para operaciones de soporte.
