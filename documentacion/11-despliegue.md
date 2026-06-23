# 11 — Despliegue

Stack de producción recomendado: **DigitalOcean Droplet** + **Docker** + **Cloudflare Tunnel** + **backups**.

Dominio actual: `https://software.kenkomed.cl`

---

## Arquitectura de producción

```
Internet → Cloudflare (Tunnel) → 127.0.0.1:8000 (Docker web)
                                      ↓
                                 MySQL (contenedor db, red interna)
```

**Pendiente recomendado para producción estable:** reemplazar `runserver` por **Gunicorn** (+ Nginx opcional delante).

---

## Requisitos del servidor

- Ubuntu Server 22.04 o 24.04 LTS
- Mínimo 2 GB RAM (4 GB recomendado con MySQL en el mismo droplet)
- Cuenta DigitalOcean + cuenta Cloudflare (gratis)
- Repositorio Git del proyecto

---

## Parte 1 — Preparar Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano unzip software-properties-common
```

---

## Parte 2 — Instalar Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
docker run hello-world
sudo systemctl enable docker
```

---

## Parte 3 — Clonar y configurar

```bash
mkdir -p ~/apps && cd ~/apps
git clone https://github.com/TU_USUARIO/Sistema-kenkomed-django.git
cd Sistema-kenkomed-django
cp .env.example .env
nano .env   # Completar valores de producción
```

### Cambiar contraseñas en `docker-compose.yml`

No usar `my_password` en producción. Actualizar:

- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `DB_PASSWORD` en servicio web

### Variables críticas en `.env`

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generar clave larga>
DJANGO_ALLOWED_HOSTS=software.kenkomed.cl,www.software.kenkomed.cl
DJANGO_CSRF_TRUSTED_ORIGINS=https://software.kenkomed.cl,https://www.software.kenkomed.cl
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
DB_PASSWORD=<igual que docker-compose>
```

Generar SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Parte 4 — Levantar el sistema

```bash
docker compose up --build -d
docker compose ps          # mysql_db debe estar "healthy"
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

Crear primer admin (shell Django):

```bash
docker compose exec web python manage.py shell
```

```python
from Login.models import Clinico
c = Clinico.objects.create(rut='11.111.111-1', nombre='Admin', apellido='Sistema',
    profesion='Administrador', correo='admin@ejemplo.cl', EsAdmin=True, activo=True, contraseña='x')
c.set_password('CAMBIAR_PASSWORD')
c.save()
exit()
```

---

## Parte 5 — Cloudflare Tunnel

### Instalar cloudflared

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
cloudflared tunnel login
cloudflared tunnel create kenkomed
```

### Configurar `~/.cloudflared/config.yml`

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/USUARIO/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: software.kenkomed.cl
    service: http://127.0.0.1:8000
  - service: http_status:404
```

```bash
cloudflared tunnel route dns kenkomed software.kenkomed.cl
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Con Tunnel **no hace falta abrir puertos 80/443** en el firewall hacia internet.

---

## Parte 6 — Backups (DigitalOcean)

### Nivel 1 — Snapshots del droplet

En el panel DO: activar **Backups automáticos** del droplet (~20% extra del costo mensual).

### Nivel 2 — Dump lógico MySQL (recomendado)

Cron diario en el servidor:

```bash
# /home/USUARIO/backup-mysql.sh
#!/bin/bash
FECHA=$(date +%Y%m%d_%H%M%S)
docker compose -f /home/USUARIO/apps/Sistema-kenkomed-django/docker-compose.yml \
  exec -T db mysqldump -u django_user -pCONTRASEÑA my_database \
  > /home/USUARIO/backups/kenkomed_$FECHA.sql
# Opcional: subir a DigitalOcean Spaces con s3cmd o rclone
find /home/USUARIO/backups -name "*.sql" -mtime +30 -delete
```

```bash
chmod +x backup-mysql.sh
crontab -e
# 0 3 * * * /home/USUARIO/backup-mysql.sh
```

### Restaurar backup

```bash
cat backup_FECHA.sql | docker compose exec -T db mysql -u django_user -pCONTRASEÑA my_database
```

---

## Comandos de mantenimiento

```bash
docker compose restart
docker compose down          # sin borrar datos
docker compose up -d
docker compose logs -f web

# Actualizar código
git pull origin main
docker compose up --build -d
docker compose exec web python manage.py migrate

# Estado Cloudflare
sudo systemctl status cloudflared
journalctl -u cloudflared -f
```

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `DisallowedHost` | Agregar dominio a `DJANGO_ALLOWED_HOSTS` en `.env` |
| `No module named django` | Usar `docker compose exec web python` |
| MySQL no healthy | `docker compose logs db`; esperar healthcheck |
| 502 en Cloudflare | Verificar `127.0.0.1:8000` en config.yml; `docker compose logs web` |
| Tunnel no conecta | `journalctl -u cloudflared -n 50`; reiniciar servicio |

---

## Seguridad en producción

1. Contraseñas fuertes en Docker y `.env`.
2. `DJANGO_DEBUG=False` siempre.
3. No exponer MySQL (puerto 3306) a internet.
4. SSH solo con llave; desactivar login root por contraseña.
5. Mantener Ubuntu y Docker actualizados.
6. Rotar credenciales SMTP si estuvieron expuestas.

---

## Evolución recomendada (post-piloto)

- **Gunicorn** en lugar de `runserver` en `Dockerfile` / `docker-compose.yml`.
- **Nginx** como reverse proxy local.
- **MySQL Managed Database** en DO (backups automáticos del proveedor).
- Monitoreo (Uptime, logs centralizados).

Ver también: `documentacion/09-privacidad-cumplimiento.md` (subencargados DO + Cloudflare en DPA).
