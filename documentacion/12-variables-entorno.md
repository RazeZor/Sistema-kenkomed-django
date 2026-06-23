# 12 — Variables de entorno

El proyecto carga configuración desde `.env` en la raíz (via `python-dotenv` en `settings.py`).  
**Nunca commitear `.env`** — usar `.env.example` como plantilla.

---

## Referencia completa

| Variable | Obligatoria prod | Descripción | Ejemplo |
|----------|------------------|-------------|---------|
| `DJANGO_DEBUG` | Sí | `False` en producción | `False` |
| `DJANGO_SECRET_KEY` | Sí (si DEBUG=False) | Clave criptográfica Django | string largo aleatorio |
| `DJANGO_ALLOWED_HOSTS` | Recomendado | Hosts separados por coma | `software.kenkomed.cl` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Recomendado | Orígenes HTTPS para CSRF | `https://software.kenkomed.cl` |
| `DB_HOST` | Sí | Host MySQL | `db` (Docker) o IP |
| `DB_NAME` | Sí | Nombre BD | `my_database` |
| `DB_USER` | Sí | Usuario MySQL | `django_user` |
| `DB_PASSWORD` | Sí | Contraseña MySQL | — |
| `DB_PORT` | No | Puerto | `3306` |
| `DB_CONN_MAX_AGE` | No | Pool conexiones (seg) | `60` |
| `EMAIL_HOST` | Para correos | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | No | Puerto SMTP | `587` |
| `EMAIL_USE_TLS` | No | TLS | `True` |
| `EMAIL_HOST_USER` | Para correos | Usuario SMTP | |
| `EMAIL_HOST_PASSWORD` | Para correos | App password / clave | |
| `DEFAULT_FROM_EMAIL` | No | Remitente | `noreply@kenkomed.cl` |
| `SECURE_SSL_REDIRECT` | Prod | Redirect HTTP→HTTPS | `True` |
| `SESSION_COOKIE_SECURE` | Prod | Cookie solo HTTPS | `True` |
| `CSRF_COOKIE_SECURE` | Prod | CSRF cookie HTTPS | `True` |
| `SECURE_HSTS_SECONDS` | No | HSTS (default 1 año) | `31536000` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | No | HSTS subdominios | `True` |

---

## Desarrollo local (Docker)

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-only-key-not-for-production
DB_HOST=db
DB_PASSWORD=my_password
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

MySQL en host Windows: puerto mapeado `3307:3306` en `docker-compose.yml`.

---

## Producción detrás de Cloudflare

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<clave única>
DJANGO_ALLOWED_HOSTS=software.kenkomed.cl,www.software.kenkomed.cl
DJANGO_CSRF_TRUSTED_ORIGINS=https://software.kenkomed.cl,https://www.software.kenkomed.cl
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

`settings.py` define `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` para que Django detecte HTTPS detrás del proxy.

---

## Generar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

o

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Gmail / SMTP

Para Gmail usar **contraseña de aplicación** (no la contraseña normal de la cuenta).  
Configurar en Google Account → Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones.
