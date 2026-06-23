# 01 — Introducción

## Qué es KenkoMed

KenkoMed es un sistema de gestión clínica orientado a kinesiología y rehabilitación. Permite a profesionales y centros:

- Registrar y gestionar pacientes por centro (multiclínica).
- Completar anamnesis inicial con **Sistema de Soporte a Decisiones (DSS)**.
- Aplicar cuestionarios estandarizados (PSFS, GROC, EQ-5D, etc.).
- Documentar sesiones kinésicas con evaluación inicial, seguimiento y alta.
- Agendar citas (agenda personal y del centro).
- Emitir recetas médicas y generar informes/fichas imprimibles.
- Cumplir requisitos de privacidad: auditoría de accesos, exportación ARCO, consentimiento en formulario QR.

Los **pacientes no tienen cuenta** en el sistema. Solo acceden al formulario remoto vía enlace/QR cuando el profesional lo genera.

---

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Django 5.1+ (Python 3.10) |
| Base de datos | MySQL 8.0 |
| Contenedores | Docker + Docker Compose |
| Email | SMTP (Gmail u otro) |
| PDF | ReportLab (auditoría) |
| QR | `qrcode` + Pillow |
| Frontend | Templates Django + HTML/CSS/JS (Tailwind en varias vistas) |
| Configuración | `python-dotenv` (`.env`) |

---

## Estructura del repositorio

```
Sistema-kenkomed-django/
├── ProyectoMainAPP/       # Proyecto Django (settings, urls, email, errores)
├── Login/                 # Modelos principales y autenticación
├── clinicas/              # Centros y membresías
├── clinicos/              # Perfil del clínico
├── PanelDeControl/        # Panel, estadísticas, reservas, privacidad
├── FormularioInicial/     # Anamnesis DSS y QR
├── TiposDeFormularios/    # Cuestionarios clínicos
├── SesionesKinesicas/     # Sesiones kinésicas
├── RecetasMedicas/        # Vistas de recetas
├── templates/             # Plantillas globales (base, menú, errores, emails)
├── static/                # CSS y JS
├── media/                 # Logos de clínicas (upload)
├── documentacion/         # Esta documentación
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
└── .env.example
```

---

## Usuarios del sistema

| Rol | Descripción |
|-----|-------------|
| **Admin KenkoMed** | `Clinico.EsAdmin=True`. Acceso global si no hay centro en sesión; con centro activo, datos acotados al centro. |
| **Admin del centro** | `MembresiaClinica.rol='admin'`. Estadísticas del centro, agenda compartida, auditoría. |
| **Miembro del centro** | Profesional con acceso a pacientes y agenda de su centro. |
| **Paciente** | Solo formulario público con token UUID (sin login). |

---

## Flujo clínico típico

1. Profesional inicia sesión → se asigna o crea su centro.
2. Alta de paciente (manual o vía anamnesis).
3. Anamnesis DSS (panel o QR remoto con consentimiento).
4. Historial clínico → cuestionarios, sesiones kinésicas, notas, receta.
5. Informe DSS / ficha profesional para impresión o revisión.
6. Estadísticas y seguimiento evolutivo (PSFS, GROC, etc.).
7. Todas las acciones relevantes quedan en el registro de auditoría.
