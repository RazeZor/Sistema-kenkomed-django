# 🏥 Manual de Despliegue — Sistema Kenkomed en Ubuntu Server

> **Sistema:** Django 5.1 + MySQL 8.0 + Docker + Cloudflare Tunnel  
> **Objetivo:** Dejar el sistema corriendo en un Ubuntu Server desde cero y accesible desde internet vía Cloudflare Tunnel.

---

## 📋 REQUISITOS PREVIOS

- Un servidor con **Ubuntu Server 22.04 LTS** (o 24.04 LTS) instalado
- Acceso por terminal SSH o acceso físico al servidor
- Conexión a internet en el servidor
- Una cuenta en [Cloudflare](https://cloudflare.com) (gratis)
- El código del proyecto en un repositorio Git (GitHub, GitLab, etc.)

---

## PARTE 1 — PREPARAR EL SERVIDOR UBUNTU

### 1.1 — Actualizar el sistema

Lo primero que siempre debes hacer en un servidor nuevo es actualizarlo todo.

```bash
sudo apt update && sudo apt upgrade -y
```

> Esto puede tardar varios minutos. Espera a que termine antes de continuar.

---

### 1.2 — Instalar herramientas básicas

```bash
sudo apt install -y curl wget git nano unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

**Para que sirve cada uno:**
- `curl`, `wget` — Descargar archivos desde internet
- `git` — Clonar el repositorio del proyecto
- `nano` — Editor de texto en terminal
- El resto — Necesarios para instalar Docker correctamente

---

## PARTE 2 — INSTALAR DOCKER

### 2.1 — Agregar la clave GPG oficial de Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### 2.2 — Agregar el repositorio oficial de Docker

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 2.3 — Instalar Docker Engine y Docker Compose

```bash
sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2.4 — Verificar que Docker se instalo correctamente

```bash
docker --version
docker compose version
```

Deberias ver algo como:
```
Docker version 26.x.x, build xxxxxxx
Docker Compose version v2.x.x
```

### 2.5 — Permitir usar Docker sin sudo

Por defecto Docker requiere `sudo` en cada comando. Esto lo evita:

```bash
sudo usermod -aG docker $USER
```

> IMPORTANTE: Debes cerrar sesion y volver a entrar para que esto tenga efecto.

```bash
exit
```

Vuelve a conectarte por SSH y verifica:

```bash
docker run hello-world
```

Si ves un mensaje que dice "Hello from Docker!", Docker esta perfecto.

### 2.6 — Habilitar Docker para que inicie automaticamente con el servidor

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

---

## PARTE 3 — OBTENER EL CODIGO DEL PROYECTO

### 3.1 — Crear una carpeta para el proyecto

```bash
mkdir -p /home/$USER/apps
cd /home/$USER/apps
```

### 3.2 — Clonar el repositorio

Reemplaza la URL con la de tu repositorio real:

```bash
git clone https://github.com/TU_USUARIO/Sistema-kenkomed-django.git
```

Si el repositorio es privado, necesitaras autenticarte con un token de GitHub:

```bash
git clone https://TU_USUARIO:TU_TOKEN@github.com/TU_USUARIO/Sistema-kenkomed-django.git
```

> Para crear un token en GitHub: Settings > Developer Settings > Personal access tokens > Generate new token (permisos: repo)

### 3.3 — Entrar a la carpeta del proyecto

```bash
cd Sistema-kenkomed-django
```

Verifica que los archivos estan:

```bash
ls -la
```

Deberias ver: `manage.py`, `docker-compose.yml`, `Dockerfile`, `requirements.txt`, etc.

---

## PARTE 4 — CONFIGURAR EL PROYECTO

### 4.1 — Revisar el archivo docker-compose.yml

```bash
cat docker-compose.yml
```

El archivo ya esta preconfigurado con estas credenciales:
- **Base de datos:** `my_database`
- **Usuario:** `django_user`
- **Contrasena:** `my_password`

### 4.2 — (Recomendado) Cambiar las contrasenas en produccion

```bash
nano docker-compose.yml
```

Cambia los valores de:
```yaml
MYSQL_ROOT_PASSWORD: TU_PASSWORD_ROOT_SEGURA
MYSQL_PASSWORD: TU_PASSWORD_SEGURA
DB_PASSWORD: TU_PASSWORD_SEGURA
```

Para guardar en nano: `Ctrl+O` luego `Enter` luego `Ctrl+X`

---

## PARTE 5 — CONSTRUIR Y LEVANTAR EL SISTEMA

### 5.1 — Construir las imagenes Docker (primera vez)

Este comando descarga MySQL, instala Python y todas las librerias del proyecto:

```bash
docker compose up --build -d
```

- `--build` — Construye la imagen del proyecto desde el Dockerfile
- `-d` — Corre en segundo plano (modo detached)

> La primera vez puede tardar 3 a 10 minutos dependiendo de la velocidad de internet.

### 5.2 — Verificar que los contenedores estan corriendo

```bash
docker compose ps
```

Debes ver algo asi:

```
NAME         IMAGE                  STATUS          PORTS
mysql_db     mysql:8.0              Up (healthy)    0.0.0.0:3306->3306/tcp
django_app   kenkomed-django-web    Up              0.0.0.0:8000->8000/tcp
```

> El contenedor `mysql_db` DEBE decir "Up (healthy)" — no solo "Up". Si dice "starting" espera unos segundos y vuelve a verificar.

### 5.3 — Ver los logs para diagnosticar problemas

```bash
# Ver todos los logs
docker compose logs -f

# Ver solo los logs de Django
docker compose logs -f web

# Ver solo los logs de MySQL
docker compose logs -f db
```

Para salir de los logs: `Ctrl + C`

---

## PARTE 6 — CONFIGURAR LA BASE DE DATOS

### 6.1 — Ejecutar las migraciones

Las migraciones crean todas las tablas en la base de datos:

```bash
docker compose exec web python manage.py migrate
```

Deberias ver una lista de migraciones aplicadas terminando en `OK`.

### 6.2 — Encriptar contrasenas ya existentes (si importas datos)

Si importas datos desde un backup con contrasenas en texto plano:

```bash
docker compose exec web python manage.py hash_passwords --yes
```

### 6.3 — Crear el primer usuario clinico/admin

```bash
docker compose exec web python manage.py shell
```

Dentro del shell de Django, pega esto:

```python
from Login.models import Clinico

# Crear el usuario
Clinico.objects.create(
    rut='11.111.111-1',
    nombre='Admin',
    apellido='Sistema',
    profesion='Administrador',
    correo='nachojaviert@gmail.com',
    EsAdmin=True,
    activo=True,
    contraseña='temporal'
)

# Asignar contrasena encriptada
clinico = Clinico.objects.get(rut='11.111.111-1')
clinico.set_password('root')
clinico.save()

print("Usuario creado:", clinico.nombre, clinico.apellido)
exit()
```

---

## PARTE 7 — VERIFICAR QUE EL SISTEMA FUNCIONA

### 7.1 — Probar en el mismo servidor

```bash
curl http://localhost:8000
```

Si recibes HTML de respuesta, el sistema esta corriendo.

### 7.2 — Probar desde otra maquina en la misma red

Obtener la IP del servidor:

```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

Luego desde tu PC abre en el navegador:

```
http://192.168.1.XXX:8000
```

---

## PARTE 8 — INSTALAR Y CONFIGURAR CLOUDFLARE TUNNEL

Cloudflare Tunnel permite exponer tu servidor a internet SIN abrir puertos en el router, SIN IP publica fija, y con HTTPS automatico.

### 8.1 — Instalar cloudflared en el servidor Ubuntu

```bash
# Descargar cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Instalar
sudo dpkg -i cloudflared-linux-amd64.deb

# Verificar instalacion
cloudflared --version
```

### 8.2 — Autenticarse con tu cuenta de Cloudflare

```bash
cloudflared tunnel login
```

Este comando te dara una URL. **Copiala y abrela en tu navegador** (en tu PC, no en el servidor). Inicia sesion con tu cuenta de Cloudflare y autoriza el acceso.

Cuando termines, el servidor recibira un certificado automaticamente.

### 8.3 — Crear el tunel

```bash
cloudflared tunnel create kenkomed
```

Guarda el **Tunnel ID** que aparece. Se ve asi:
```
Created tunnel kenkomed with id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 8.4 — Crear el archivo de configuracion del tunel

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Pega este contenido (reemplaza los valores con los tuyos):

```yaml
tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
credentials-file: /home/TU_USUARIO/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

ingress:
  - hostname: kenkomed.tudominio.cl
    service: http://localhost:8000
  - service: http_status:404
```

Para guardar: `Ctrl+O` luego `Enter` luego `Ctrl+X`

### 8.5 — Crear el registro DNS en Cloudflare

```bash
cloudflared tunnel route dns kenkomed kenkomed.tudominio.cl
```

### 8.6 — Instalar cloudflared como servicio del sistema

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Verificar que esta corriendo:

```bash
sudo systemctl status cloudflared
```

Debes ver `Active: active (running)`.

### 8.7 — Alternativa sin dominio propio (tunel temporal de prueba)

Si no tienes dominio propio y solo quieres probar:

```bash
cloudflared tunnel --url http://localhost:8000
```

Esto genera automaticamente una URL publica temporal:
```
https://algo-algo-algo.trycloudflare.com
```

> Esta URL cambia cada vez que reinicias el comando. Para algo permanente, necesitas el setup del 8.3 al 8.6.

---

## PARTE 9 — CONFIGURAR DJANGO PARA EL DOMINIO PUBLICO

### 9.1 — Agregar el dominio a ALLOWED_HOSTS

```bash
nano ProyectoMainAPP/settings.py
```

Busca `ALLOWED_HOSTS` y agrega tu dominio:

```python
ALLOWED_HOSTS = [
    '.ngrok-free.app',
    'localhost',
    '127.0.0.1',
    'kenkomed.tudominio.cl',    # Tu dominio
    '*.trycloudflare.com',      # Si usas el tunel temporal
]
```

Y en `CSRF_TRUSTED_ORIGINS`:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://kenkomed.tudominio.cl',
    'https://*.trycloudflare.com',
    'https://*.ngrok-free.app',
]
```

### 9.2 — Reiniciar Django para aplicar cambios

```bash
docker compose restart web
```

---

## PARTE 10 — VERIFICACION FINAL

```bash
# 1. Contenedores corriendo
docker compose ps

# 2. Django responde en localhost
curl -I http://localhost:8000

# 3. Cloudflare tunnel activo
sudo systemctl status cloudflared

# 4. Ver logs en tiempo real
docker compose logs -f web
```

Abre en tu navegador:
```
https://kenkomed.tudominio.cl
```

Si ves la pantalla de login de Kenkomed, el deploy esta completo.

---

## COMANDOS DE MANTENIMIENTO

```bash
# Reiniciar todo el sistema
docker compose restart

# Apagar el sistema (sin borrar datos)
docker compose down

# Volver a encender el sistema
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Actualizar el codigo despues de un git pull
git pull origin main
docker compose up --build -d
docker compose exec web python manage.py migrate

# Hacer backup de la base de datos
docker compose exec db mysqldump -u django_user -pmy_password my_database > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar un backup
cat backup_FECHA.sql | docker compose exec -T db mysql -u django_user -pmy_password my_database

# Ver estado de Cloudflare Tunnel
sudo systemctl status cloudflared
journalctl -u cloudflared -f
```

---

## SOLUCION DE PROBLEMAS COMUNES

### Error: "permission denied" al usar Docker
```bash
sudo usermod -aG docker $USER
exit  # Cerrar sesion y volver a entrar
```

### El contenedor MySQL no pasa a "healthy"
```bash
# Ver que esta pasando en MySQL
docker compose logs db

# Si el problema persiste, borrar el volumen y recrear (BORRA LOS DATOS)
docker compose down -v
docker compose up -d
```

### Error "No module named 'django'"
Asegurate de siempre usar `docker compose exec web python`:
```bash
# MAL
python manage.py migrate

# BIEN
docker compose exec web python manage.py migrate
```

### Django muestra "DisallowedHost"
Agrega el dominio a `ALLOWED_HOSTS` en `settings.py` y reinicia:
```bash
docker compose restart web
```

### Cloudflare Tunnel no conecta
```bash
journalctl -u cloudflared --no-pager -n 50
sudo systemctl restart cloudflared
```

### Puerto 8000 bloqueado por firewall de Ubuntu
```bash
sudo ufw status
sudo ufw allow from 192.168.0.0/16 to any port 8000
# Para Cloudflare Tunnel NO necesitas abrir puertos hacia internet
```

---

## RECOMENDACIONES DE SEGURIDAD PARA PRODUCCION

1. Cambiar todas las contrasenas por defecto en `docker-compose.yml`
2. Deshabilitar DEBUG en Django: `DEBUG = False` en `settings.py`
3. Usar un SECRET_KEY seguro:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
4. No exponer el puerto 3306 (MySQL) hacia internet — ya esta configurado asi
5. Mantener Docker y Ubuntu actualizados:
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker compose pull
   ```

---

*Manual generado para Sistema Kenkomed — Django 5.1 + MySQL 8.0 + Docker Compose*

La solución rápida (Mantener el túnel temporal vivo)
Puedes usar un comando de Linux llamado nohup (No Hang Up). Esto hace que el comando se ejecute en el fondo ("background") y siga vivo incluso si cierras tu sesión SSH.

En tu Ubuntu, escribe esto y dale Enter:

nohup cloudflared tunnel --url http://127.0.0.1:8000 > tunnel.log 2>&1 &

¿Cómo veo la URL que me generó? Como ahora se está ejecutando invisible en el fondo, guardará todo lo que imprime en un archivo llamado tunnel.log. Para leer ese archivo y ver tu URL, ejecuta:
cat tunnel.log | grep trycloudflare

Para "apagarlo" cuando ya no lo necesites, harás:
pkill cloudflared