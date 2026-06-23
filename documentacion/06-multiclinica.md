# 06 — Sistema multiclínica

## Conceptos

| Término | Significado |
|---------|-------------|
| **Centro / Clínica** | Institución que agrupa pacientes y profesionales (`clinicas.Clinica`) |
| **Membresía** | Vínculo Clinico ↔ Clinica con rol (`MembresiaClinica`) |
| **Centro individual** | Clínica `tipo=individual`, 1 profesional, creada automáticamente al primer login |
| **Centro compartido** | `tipo=clinica`, varios profesionales, `max_clinicos` configurable |

Cada **paciente pertenece a un solo centro** (`Paciente.clinica`). Los datos clínicos heredan ese aislamiento.

---

## Creación automática de centro individual

Al iniciar sesión un clínico sin membresía activa:

1. `clinicas.signals` / servicios crean `Clinica` tipo `individual`.
2. Se crea `MembresiaClinica` con `rol=admin`.
3. Sesión queda con `clinica_id` del nuevo centro.

---

## Funciones de filtrado (`clinicas/utils.py`)

| Función | Uso |
|---------|-----|
| `obtener_clinica_de_sesion(request)` | Objeto Clinica activa |
| `filtrar_por_clinica_sesion(qs, lookup)` | Filtra cualquier queryset por `clinica_id` |
| `filtrar_pacientes_por_sesion(request)` | Pacientes del centro |
| `obtener_paciente_por_rut(request, rut)` | Paciente si pertenece al centro |
| `paciente_pertenece_a_sesion(request, paciente)` | Boolean permiso |
| `obtener_clinicos_del_centro(request)` | Profesionales del centro |
| `filtrar_reservas_por_sesion(request, alcance)` | Citas personales o del centro |
| `filtrar_auditoria_por_sesion(request)` | Registros de auditoría del centro |
| `requiere_centro_o_admin_sistema(request)` | Guard para vistas que necesitan centro |

### Admin KenkoMed sin centro en sesión

`es_admin=True` y `clinica_id=None` → ve **todos** los registros (modo soporte global).

Con `clinica_id` en sesión → mismo alcance que un usuario del centro.

---

## Operaciones administrativas

Gestionadas desde **Django Admin** (`/administradordjangogeneral`):

### `unir_clinico_a_centro` (`clinicas/services.py`)

- Migra pacientes del centro individual al centro destino.
- Desactiva membresía anterior.
- Respeta `max_clinicos`.

### `convertir_a_centro`

- Cambia `tipo` de `individual` a `clinica`.
- Aumenta cupo de profesionales.

---

## Vista Mi Centro

**URL:** `/clinicas/mi-centro/`  
**Vista:** `clinicas.views.mi_centro`

Muestra información del centro activo y equipo (solo lectura). La gestión avanzada es vía Admin.

---

## Branding por centro

`clinicas/branding.py` — `url_logo_clinica(clinica)`:

- Usa `Clinica.logo` si existe.
- Fallback a logo KenkoMed.
- Integrado en informes, fichas y correos (CID inline).

---

## Agenda compartida

En centros `tipo=clinica` con más de un miembro activo:

- Los miembros pueden **ver** la agenda del centro.
- Solo **admin del centro** puede crear/mover/eliminar citas en agenda centro (`puede_editar_calendario_clinica`).

---

## Multiclínica y cumplimiento

- La auditoría filtra por `clinica_id` — cada centro ve solo sus trazas.
- La exportación ARCO verifica que el paciente pertenezca al centro de sesión.
- El aviso de privacidad identifica a la clínica como responsable y KenkoMed como encargado.
