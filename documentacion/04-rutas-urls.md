# 04 — Rutas y URLs

Prefijo de producción: `https://software.kenkomed.cl`

---

## Autenticación y navegación

| Ruta | Nombre | Vista |
|------|--------|-------|
| `/` | `login` | Login por RUT + contraseña |
| `/Cerrar/` | `cerrarSesion` | Cierra sesión y borra cookie |
| `/menu/` | `menu` | Menú lateral (drawer) |
| `/panel/` | `panel` | Dashboard principal |

---

## Pacientes

| Ruta | Nombre | Vista |
|------|--------|-------|
| `/panel/ListaPacientes` | `pacientes` | Listado paginado |
| `/panel/AgregarPaciente` | `AgregarPacienteBasico` | Alta manual |
| `/panel/EditarPaciente` | `editar_paciente` | Edición demográfica |
| `/eliminar_paciente/` | `eliminar` | POST — eliminar paciente |

---

## Ciclos clínicos (`/ciclos/`)

| Ruta | Método | Nombre | Descripción |
|------|--------|--------|-------------|
| `/ciclos/iniciar/` | POST | `ciclos_clinicos:iniciar` | Nuevo ciclo (`rut`, `motivo_consulta`) |
| `/ciclos/finalizar/` | POST | `ciclos_clinicos:finalizar` | Cierre normal (`rut`, `ciclo_id`, `notas_cierre`) |
| `/ciclos/abandonar/` | POST | `ciclos_clinicos:abandonar` | Abandono (`rut`, `ciclo_id`, `motivo`) |
| `/ciclos/paciente/` | GET | `ciclos_clinicos:listar` | JSON de ciclos del paciente (`?rut=`) |

**Parámetro transversal:** `ciclo_id=<pk>` en query string (junto con `rut=`) para historial, cuestionarios, sesiones, informes y exportación ARCO. Si se omite, se usa el ciclo activo del centro o el guardado en sesión (`ciclo_activo_id`).

---

## Historial e informes

| Ruta | Nombre | Vista |
|------|--------|-------|
| `/panel/historialClinico/` | `historialClinico` | Hub clínico del paciente (`?rut=&ciclo_id=`) |
| `/panel/fichaPacientes/` | `ficha` | Resumen DSS del paciente |
| `/informe/` | `informe` | Informe DSS imprimible (`?rut=`) |
| `/ficha-clinica/` | `fichaClinica` | Ficha profesional completa |
| `/panel/exportar-ficha/` | `exportar_ficha` | ARCO: `?rut=&format=json\|html` |

---

## Anamnesis y formularios remotos

| Ruta | Nombre | Vista |
|------|--------|-------|
| `/panel/FormularioInicial/` | `formularioInicial` | Anamnesis DSS (sesión clínico) |
| `/generar-qr-formulario/` | `generar_qr` | Gestor de tokens QR |
| `/descargar-qr/<uuid>/` | `descargar_qr` | Pantalla QR + enlace |
| `/formulario-publico/<uuid>/` | `formulario_publico` | Formulario paciente (RUT + consentimiento) |
| `/desactivar-token/<uuid>/` | `desactivar_token` | Desactivar token |
| `/generar-formulario-remoto/` | `generar_formulario_remoto` | POST desde historial |
| `/privacidad-paciente/` | `privacidad_paciente` | Aviso público de privacidad |

---

## Cuestionarios

| Ruta | Nombre | Instrumento |
|------|--------|-------------|
| `/CuestionarioGROC/` | `GROK` | GROC |
| `/CuestionarioPSFS/` | `gestionar_psfs` | PSFS |
| `/CuestionarioEQ_5D/` | `EQ_5D` | EQ-5D |
| `/CuestionarioBarthel/` | `bartel` | Índice de Barthel |
| `/CuestionarioScrenning/` | `Screnning` | Screening Örebro |
| `/CuestionarioENA/` | `ENA` | Escala de necesidad de atención |
| `/CuestionarioOswestry/` | `oswestry` | ODI (lumbalgia) |
| `/CuestionarioLEFS/` | `lefs` | LEFS (extremidad inferior) |

Todas aceptan `?rut=` del paciente y `?ciclo_id=` del episodio.

---

## Sesiones kinésicas (`/sesiones-kinesicas/`)

| Ruta | Nombre |
|------|--------|
| `listar/` | `sesiones_kinesicas:listar` |
| `crear-primera/` | `crear_primera` |
| `crear-seguimiento/` | `crear_seguimiento` |
| `crear-final/` | `crear_final` |
| `ver/` | `ver` (`?rut=&numero_sesion=`) |
| `editar/` | `editar` |
| `api/sesiones/` | `api_sesiones` (JSON para combobox) |

---

## Recetas

| Ruta | Nombre |
|------|--------|
| `/RecetaMedica/` | `receta` |

---

## Calendario y reservas (incluidas en raíz)

| Ruta | Nombre |
|------|--------|
| `/calendario/` | `calendario_reservas` |
| `/calendario/personal/` | `calendario_personal` |
| `/calendario/clinica/` | `calendario_clinica` |
| `/api/reservas/` | GET — listar eventos |
| `/api/reservas/crear/` | POST — crear cita |
| `/api/reservas/mover/<id>/` | POST — reagendar |
| `/api/reservas/eliminar/<id>/` | POST — cancelar |

---

## Estadísticas

| Ruta | Nombre |
|------|--------|
| `/estadisticas/` | `estadisticas` — centro (solo admin centro) |
| `/estadisticas_paciente/` | `estadisticas_paciente` — por paciente |

---

## Privacidad y auditoría

| Ruta | Nombre |
|------|--------|
| `/panel/auditoria-accesos/` | `auditoria_accesos` |
| `/panel/auditoria-accesos/exportar-pdf/` | `exportar_auditoria_pdf` |

---

## Clínicas y perfil

| Ruta | Nombre |
|------|--------|
| `/clinicas/mi-centro/` | `mi_centro` |
| `/clinicos/perfil/` | `perfilClinico` |
| `/PerfilClinico/` | Redirect permanente a perfil |

---

## Admin y utilidades

| Ruta | Notas |
|------|-------|
| `/administradordjangogeneral` | Django Admin (URL no estándar) |
| `/clear-session-message/` | AJAX — limpiar mensaje flash |
| `/__preview__/error/<código>/` | Solo DEBUG — vista previa errores |

---

## Handlers de error

- `400`, `403`, `404`, `500` → `templates/errors/page.html`
- Fallo CSRF → vista custom en `error_handlers.py`
