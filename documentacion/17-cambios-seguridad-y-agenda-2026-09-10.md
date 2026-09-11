# Registro de Cambios y Mejoras de Seguridad / Agenda

**Fecha:** 10 de Septiembre de 2026  
**Autor:** Antigravity AI & NachoDev  
**Proyecto:** Sistema KenkoMed Django  

---

## 📋 Resumen Ejecutivo

En esta fecha se llevaron a cabo dos grandes bloques de mejoras en el sistema:

1. **Gestión de Modalidad de Atención y Colores en la Agenda**: Etiquetado dinámico por colores para distinguir atenciones Presenciales, a Domicilio y por Telemedicina en la ficha clínica del paciente, junto con el control de reenvío de correos de notificación.
2. **Auditoría de Seguridad Completa y Hardening de Producción**: Corrección de vulnerabilidades críticas y de severidad alta en la gestión de credenciales, protección CSRF, rate-limiting anti fuerza bruta y prevención de XSS.

---

## 🎨 1. Mejoras en Agenda y Modalidades de Atención

### 1.1 Modelo de Datos (`Reserva`)
- Se añadió el campo `tipo_atencion` al modelo `Reserva` en `Login/models.py`:
  - `presencial`: Atención en Consulta (Color por defecto: Azul/Por Defecto).
  - `domicilio`: Atención en Domicilio (Color: Verde).
  - `telemedicina`: Telemedicina (Color: Morado/Púrpura).

### 1.2 Interfaz de Usuario y Tarjetas de la Agenda
- **Tarjetas Dinámicas (`ficha_clinica.html`):**
  - La tarjeta de cada cita en la agenda ahora cambia de color según la modalidad seleccionada o asignada.
  - Al arrastrar o mover una reserva (`api_mover_reserva`), la tarjeta mantiene su color y modalidad asignada.
- **Control de Notificaciones por Correo:**
  - En la modal de edición/actualización de citas, se incorporó un interruptor/checkbox para indicar opcionalmente si se desea reenviar el correo de notificación al paciente al modificar la cita.

---

## 🛡️ 2. Auditoría y Hardening de Seguridad

### 2.1 Remoción de Secretos Hardcodeados 🔴 (Severidad Crítica)
- **`ProyectoMainAPP/settings.py`**:
  - Se eliminó la clave API de Resend hardcodeada (`re_PvrP64v9_...`).
  - Se eliminó la contraseña de aplicación de Gmail hardcodeada (`irykslbyckmeiewn`).
  - Se desacopló la `SECRET_KEY` de Django hacia la variable de entorno `DJANGO_SECRET_KEY`.
- **`ProyectoMainAPP/email_service.py`**:
  - Se eliminó el valor fallback hardcodeado de la clave de Resend. Ahora lanza un error explícito si la variable no está en el entorno en producción o un mensaje en consola en desarrollo.
- **`docker-compose.yml` y `.env.example`**:
  - Se actualizaron las definiciones de servicio para leer variables de entorno (`DB_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `DJANGO_SECRET_KEY`, `RESEND_API_KEY`).
  - Se creó y actualizó el archivo `.env.example` para documentar todas las variables requeridas.

### 2.2 Eliminación de Exenciones CSRF 🔴 (Severidad Alta)
- Se eliminó el decorador `@csrf_exempt` en los siguientes endpoints críticos:
  - `PanelDeControl/views_reservas.py`: `api_crear_reserva`, `api_mover_reserva`, `api_eliminar_reserva`.
  - `PanelDeControl/views.py`: `clear_session_message`.
  - `SesionesKinesicas/views.py`: `api_sesiones_paciente`.
- **Frontend JS:** Las funciones helpers `apiPost()` y peticiones `fetch()` en la plantilla base envían automáticamente el encabezado `X-CSRFToken` validado por Django.

### 2.3 Rate Limiting y Protección Anti-Fuerza Bruta 🟠 (Severidad Alta)
- Se instaló e integró la librería `django-axes>=7.0.0`:
  - Configurado en `INSTALLED_APPS` y `MIDDLEWARE` (`axes.middleware.AxesMiddleware`).
  - Integrado en `Login/views.py` (`validarLogin`) utilizando `AxesProxyHandler`.
  - **Política de Bloqueo:** Tras 5 intentos fallidos consecutivos de login por IP o RUT, la cuenta/IP se bloquea temporalmente por 1 hora (3600 segundos).

### 2.4 Prevención de XSS (Cross-Site Scripting) 🟡 (Severidad Media)
- **`FormularioInicial/templates/error.html`**:
  - Se eliminó el filtro `|safe` de `{{ mensaje|safe }}` y `{{ error_message|safe }}`, forzando el auto-escape seguro de datos provenientes de excepciones o entrada de usuario.

### 2.5 Configuración de Cookies y Seguridad SSL
- Se agregaron las siguientes directivas en `settings.py`:
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = 'Lax'`
  - `CSRF_COOKIE_HTTPONLY = False` (para permitir lectura por el helper JS `apiPost()`)
  - `CSRF_COOKIE_SAMESITE = 'Lax'`
  - `SECURE_SSL_REDIRECT = _env_bool('SECURE_SSL_REDIRECT', default=True)` (condicionado a `DEBUG=False`).

---

## 📁 3. Archivos Modificados / Creados

| Archivo | Tipo de Cambio | Descripción |
|---|---|---|
| `Login/models.py` | Modificado | Adición de `tipo_atencion` a `Reserva`. |
| `PanelDeControl/views_reservas.py` | Modificado | Lógica de `tipo_atencion` y remoción de `@csrf_exempt`. |
| `PanelDeControl/templates/ficha_clinica.html` | Modificado | Estilos y lógica JS para colores y modal de cita. |
| `ProyectoMainAPP/settings.py` | Modificado | Variables de entorno, `django-axes` y seguridad de cookies. |
| `ProyectoMainAPP/email_service.py` | Modificado | Eliminación de credenciales hardcodeadas. |
| `Login/views.py` | Modificado | Integración de `AxesProxyHandler` para rate limiting. |
| `FormularioInicial/templates/error.html` | Modificado | Remoción de `|safe` para prevenir XSS. |
| `requirements.txt` | Modificado | Adición de `django-axes>=7.0.0`. |
| `docker-compose.yml` | Modificado | Paso de secretos a variables de entorno `.env`. |
| `.env.example` | Creado | Plantilla de variables de entorno para el proyecto. |
| `.env` | Creado (local) | Variables de desarrollo local (en `.gitignore`). |

---

## 🛠️ 4. Guía de Despliegue y Mantenimiento

### 4.1 En Servidor de Producción
1. Generar/Revocar las API Keys antiguas en Resend y Google App Passwords.
2. Definir las variables reales en el archivo `.env` del servidor.
3. Ejecutar la reconstrucción y migración:
   ```bash
   docker compose build web
   docker compose up -d
   docker compose exec web python manage.py migrate
   ```

---

*Documentación generada automáticamente como registro oficial de cambios del proyecto.*
