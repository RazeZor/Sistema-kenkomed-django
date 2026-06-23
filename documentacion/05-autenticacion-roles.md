# 05 — Autenticación y roles

## Modelo de usuario

KenkoMed **no usa** `django.contrib.auth.User`. El usuario es el modelo `Login.models.Clinico`.

### Contraseñas

```python
clinico.set_password('texto_plano')  # hashea con make_password
clinico.check_password('texto_plano')  # verifica
```

Comando de migración legacy: `python manage.py hash_passwords --yes`

---

## Flujo de login

**Vista:** `Login.views.validarLogin`  
**URL:** `/`

1. POST con RUT y contraseña.
2. Busca `Clinico` por RUT, verifica `activo` y contraseña.
3. Si no tiene membresía activa → `crear_clinica_individual()` (signal/servicio en `clinicas`).
4. Escribe en sesión:
   - `rut_clinico`, `nombre_clinico`
   - `es_admin` ← `Clinico.EsAdmin`
   - `clinica_id`, `clinica_nombre`
   - `es_admin_clinica` ← `MembresiaClinica.rol == 'admin'`
5. Redirect a `/panel/`.

Opción "recordarme" puede extender duración de sesión (30 días).

---

## Cierre de sesión

**Vista:** `PanelDeControl.views.cerrar_sesion`  
- `request.session.flush()`
- `delete_cookie(sessionid)`
- Cabeceras `Cache-Control: no-store`

---

## Decoradores

Archivo: `ProyectoMainAPP/decorators/login_requerido.py`

### `@requiere_clinico`

- Exige `nombre_clinico` en sesión.
- Si no es admin KenkoMed, exige `clinica_id`.
- Usado en casi todas las vistas clínicas.

### `@requiere_admin_clinica`

- Exige `es_admin_clinica=True`.
- Estadísticas del centro, edición agenda centro.

### `@requiere_admin_auditoria`

- Admin del centro + clínica activa.
- Vista de auditoría y export PDF.

---

## Matriz de permisos

| Función | Miembro | Admin centro | Admin KenkoMed |
|---------|---------|--------------|----------------|
| Panel, pacientes propios | ✅ | ✅ | ✅ |
| Historial, cuestionarios | ✅ | ✅ | ✅ |
| Estadísticas del centro | ❌ | ✅ | ✅ (con centro) |
| Agenda del centro | Solo si clínica compartida | ✅ | ✅ |
| Auditoría clínica | ❌ | ✅ | ✅ (con centro) |
| Vista global sin centro | ❌ | ❌ | ✅ |

---

## Context processor

`clinicas.context_processors.clinica_sesion` expone en todas las plantillas:

- `clinica_actual`, `es_admin_clinica`, `es_admin_sistema`
- `puede_ver_auditoria`
- `puede_ver_estadisticas_centro`
- `puede_ver_agenda_centro`

Usado en `templates/menu.html` para mostrar/ocultar enlaces.

---

## Pacientes (sin login)

El formulario público (`/formulario-publico/<uuid>/`):

1. Verifica token válido (activo, no usado, no expirado).
2. Paso 1: verificación de RUT en sesión (`rut_verificado_{token_id}`).
3. Paso 2: formulario + checkbox `consentimiento_datos` obligatorio.
4. Al enviar: guarda anamnesis, `ConsentimientoDatos`, marca token usado, notifica al clínico.

No se crea sesión de `Clinico` para el paciente.

---

## Middleware de clínica

`ClinicaMiddleware` en cada request:

- Lee membresía activa del clínico logueado.
- Actualiza `clinica_id` / `es_admin_clinica` si cambió en BD.

---

## Seguridad de sesión (producción)

Con `DJANGO_DEBUG=False`:

- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_SSL_REDIRECT=True`
- `SECURE_PROXY_SSL_HEADER` para Cloudflare/Nginx
- HSTS habilitado

Ver `documentacion/12-variables-entorno.md`.
