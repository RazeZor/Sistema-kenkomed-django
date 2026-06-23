# Documentación KenkoMed

Sistema clínico web para centros de kinesiología y rehabilitación. Monolito Django 5.1 + MySQL 8, multiclínica, con soporte a decisiones clínica (DSS), cuestionarios estandarizados y cumplimiento Ley 21.719 (Chile).

**Producción:** `https://software.kenkomed.cl`

---

## Índice

| # | Documento | Contenido |
|---|-----------|-----------|
| 01 | [Introducción](01-introduccion.md) | Qué es el sistema, stack, estructura de carpetas |
| 02 | [Arquitectura](02-arquitectura.md) | Apps Django, flujo de datos, diagrama |
| 03 | [Modelos de datos](03-modelos-datos.md) | Entidades, relaciones, campos clave |
| 04 | [Rutas y URLs](04-rutas-urls.md) | Mapa completo de endpoints |
| 05 | [Autenticación y roles](05-autenticacion-roles.md) | Sesión, decoradores, permisos |
| 06 | [Sistema multiclínica](06-multiclinica.md) | Centros, membresías, aislamiento de datos |
| 07 | [Módulos funcionales](07-modulos-funcionales.md) | Panel, pacientes, historial, reservas, sesiones, recetas |
| 08 | [Cuestionarios clínicos](08-cuestionarios.md) | GROC, PSFS, EQ-5D, Barthel, Screening, ENA, Oswestry, LEFS |
| 09 | [Privacidad y cumplimiento](09-privacidad-cumplimiento.md) | Auditoría, ARCO, consentimiento, Ley 21.719 |
| 10 | [Correos electrónicos](10-correos.md) | Notificaciones SMTP |
| 11 | [Despliegue](11-despliegue.md) | Docker, VPS, Cloudflare Tunnel, backups |
| 12 | [Variables de entorno](12-variables-entorno.md) | `.env` y configuración |
| 13 | [Utilidades y servicios](13-utilidades.md) | Módulos auxiliares del código |
| 14 | [DSS e informes](14-dss-informes.md) | Sistema de soporte a decisiones y reportes |
| 15 | [Guía de desarrollo](15-guia-desarrollo.md) | Entorno local, migraciones, comandos |

---

## Inicio rápido (desarrollo local)

```bash
cp .env.example .env
# Completar DJANGO_SECRET_KEY y DB_PASSWORD en .env

docker compose up --build -d
docker compose exec web python manage.py migrate
```

Abrir `http://localhost:8000`

---

## Apps Django

| App | Responsabilidad |
|-----|-----------------|
| `ProyectoMainAPP` | Settings, URLs raíz, email, errores, decoradores |
| `Login` | Modelos centrales: clínicos, pacientes, formularios, auditoría |
| `clinicas` | Multitenancy: centros y membresías |
| `clinicos` | Perfil del profesional |
| `PanelDeControl` | Dashboard, estadísticas, calendario, exportación |
| `FormularioInicial` | Anamnesis DSS y formularios remotos (QR) |
| `TiposDeFormularios` | Cuestionarios de resultado clínico |
| `SesionesKinesicas` | Sesiones kinésicas (inicial, seguimiento, alta) |
| `RecetasMedicas` | Recetas médicas (vista; modelo en Login) |

---

*Última actualización: junio 2026 — refleja el estado actual del código en el repositorio.*
