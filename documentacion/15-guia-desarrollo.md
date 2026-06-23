# 15 — Guía de desarrollo

## Requisitos locales

- Docker Desktop (Windows/Mac) o Docker + Compose (Linux)
- Git
- Editor con soporte Python/Django

---

## Primer arranque

```bash
git clone <repo>
cd Sistema-kenkomed-django
cp .env.example .env
```

Editar `.env`:
- `DJANGO_DEBUG=True`
- `DJANGO_SECRET_KEY` cualquiera para dev
- `DB_PASSWORD=my_password` (coincidir con docker-compose)

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
```

Abrir: http://localhost:8000

**MySQL desde host:** puerto `3307` (mapeo en docker-compose).

---

## Estructura de trabajo

| Tarea | Dónde |
|-------|-------|
| Nuevo modelo clínico | `Login/models.py` + migración |
| Nueva vista panel | `PanelDeControl/views*.py` + template |
| Nueva ruta | `ProyectoMainAPP/urls.py` o `app/urls.py` |
| Permisos | `decorators/login_requerido.py` + `clinicas/utils.py` |
| Auditoría nueva acción | `Login/models.py` ACCIONES + migración + `registrar_auditoria()` |
| Email nuevo evento | `email_service.py` + template en `templates/emails/` |

---

## Migraciones

```bash
# Crear
docker compose exec web python manage.py makemigrations

# Aplicar
docker compose exec web python manage.py migrate

# Estado
docker compose exec web python manage.py showmigrations
```

Migraciones recientes importantes:
- `Login.0067` — AuditoriaAcceso inicial
- `Login.0068` — Auditoría ampliada
- `Login.0069` — Acciones auditoría sistema completo
- `FormularioInicial.0004` — ConsentimientoDatos

---

## Shell y admin

```bash
docker compose exec web python manage.py shell
docker compose exec web python manage.py createsuperuser  # solo si se usa User de Django (no es el login clínico)
```

Admin Django: http://localhost:8000/administradordjangogeneral

---

## Logs

```bash
docker compose logs -f web
docker compose logs -f db
```

---

## Previsualizar páginas de error (DEBUG)

```
http://localhost:8000/__preview__/error/404/
http://localhost:8000/__preview__/error/500/
```

---

## Tests

```bash
docker compose exec web python manage.py test
```

Apps con `tests.py`: varias tienen plantillas vacías o mínimas — ampliar según necesidad.

---

## Estilo y convenciones del proyecto

- Español en mensajes de usuario y documentación.
- Sesión clínico: siempre verificar con `@requiere_clinico`.
- Acceso a paciente: usar `obtener_paciente_por_rut(request, rut)` — nunca `Paciente.objects.get` sin filtro de clínica.
- Acciones sobre datos sensibles: llamar `registrar_auditoria`.
- JSON en modelos legacy: validar con `json.loads` y manejar strings vacíos.
- PSFS: usar siempre `psfs_utils` — no manipular JSONField manualmente con `json.dumps` en campos ya JSON.

---

## Actualizar dependencias

```bash
pip install -r requirements.txt   # local venv
# o rebuild Docker:
docker compose build --no-cache web
```

---

## Documentación

Toda la documentación del proyecto vive en `documentacion/`.  
Índice: `documentacion/README.md`.

Al cambiar arquitectura o módulos significativos, actualizar el archivo correspondiente.
