# 10 — Correos electrónicos

**Servicio:** `ProyectoMainAPP/email_service.py`  
**Configuración:** variables SMTP en `.env` (ver doc 12).

---

## Configuración SMTP

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS
EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL
```

---

## Plantillas

Ubicación: `templates/emails/`

| Archivo | Uso |
|---------|-----|
| `base_email.html` | Layout base con logo |
| `alta_paciente.html` | Alta kinésica (sesión final) |
| `formulario_completado.html` | Paciente completó QR |
| `nuevo_paciente.html` | Registro de paciente |
| `receta_creada.html` / `receta_actualizada.html` | Recetas |
| `reserva_creada.html` / `reserva_reagendada.html` / `reserva_cancelada.html` | Citas |

---

## Funciones de notificación

| Función | Cuándo se llama | Destinatarios |
|---------|-----------------|---------------|
| `notificar_nuevo_paciente` | Alta paciente en anamnesis | Paciente + clínico |
| `notificar_formulario_completado` | QR enviado | Clínico |
| `notificar_receta_creada` | Nueva receta | Paciente |
| `notificar_receta_actualizada` | Edición receta | Paciente |
| `notificar_alta_paciente` | Sesión kinésica final | Paciente + clínico |
| `notificar_reserva_creada` | API crear reserva | Paciente |
| `notificar_reserva_reagendada` | API mover reserva | Paciente |
| `notificar_reserva_cancelada` | API eliminar reserva | Paciente |

---

## Detalles de implementación

- Correos en **HTML** con logo de clínica embebido (CID) vía `clinicas/branding.py`.
- **Sin datos clínicos sensibles** en el asunto (cumplimiento).
- Reservas: envío en **hilo background** (`threading.Thread`) para no bloquear la API.
- Errores de envío se registran en log; no interrumpen el flujo principal.

---

## Privacidad en correos

Los correos informan eventos genéricos ("tiene una nueva cita", "su receta fue actualizada") sin incluir diagnósticos ni detalles clínicos en el cuerpo del mensaje de notificación estándar.
