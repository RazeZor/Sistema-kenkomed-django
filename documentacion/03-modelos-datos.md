# 03 — Modelos de datos

## Diagrama relacional (simplificado)

```
Clinica ──┬── MembresiaClinica ── Clinico
          ├── Paciente ──┬── CicloClinico (1:N) ──┬── formularioClinico (1:1 por ciclo)
          │              │                       ├── CuestionarioPSFS, Groc, EQ-5D, Barthel, Screening, ENA (1:1)
          │              │                       ├── SesionKinesica (1:N)
          │              │                       └── EvaluacionOswestry, LEFS, QuickDASH, WOMAC (1:N)
          │              ├── Notas (1:1)          ← global al paciente
          │              ├── RecetaMedica (1:1)   ← global al paciente
          │              ├── Reserva (1:N)
          │              ├── ConsentimientoDatos (1:N)
          │              └── AuditoriaAcceso (1:N)
          └── AuditoriaAcceso (1:N)
```

---

## Login — Clinico

| Campo | Tipo | Notas |
|-------|------|-------|
| `rut` | PK | Identificador del profesional |
| `nombre`, `apellido` | CharField | |
| `profesion` | CharField | |
| `correo` | EmailField | |
| `contraseña` | CharField | Hasheada (`set_password` / `check_password`) |
| `EsAdmin` | Boolean | Admin sistema KenkoMed |
| `activo` | Boolean | |

---

## Login — Paciente

| Campo | Tipo | Notas |
|-------|------|-------|
| `rut` | PK | |
| `nombre`, `apellido`, `genero` | | |
| `fechaNacimiento` | Date | |
| `contacto`, `correo` | | Teléfono normalizado con prefijo 56 |
| `cobertura_de_salud`, `trabajo`, `profesion` | | |
| `LicenciaInicio`, `LicenciaFin`, `LicenciaDias` | | Licencia médica |
| `clinico` | FK Clinico | Profesional asociado |
| `clinica` | FK Clinica | **Centro propietario del dato** |
| `clinico_creador` | FK Clinico | Quién registró al paciente |

---

## ciclos_clinicos — CicloClinico

Episodio de tratamiento kinésico. Ver doc completa: [16-ciclos-clinicos.md](16-ciclos-clinicos.md).

| Campo | Notas |
|-------|-------|
| `paciente`, `clinica` | FK — alcance por centro |
| `clinico_responsable` | FK nullable |
| `numero_ciclo` | Secuencial por `(paciente, clínica)` |
| `estado` | `activo`, `finalizado`, `abandonado` |
| `motivo_consulta`, `notas_cierre` | Texto |
| `fecha_inicio`, `fecha_cierre` | DateTime |

**Restricción:** un solo ciclo `activo` por `(paciente, clinica)`.

---

## Login — formularioClinico (anamnesis DSS)

OneToOne con `CicloClinico` (y FK legacy a `Paciente`). Contiene decenas de campos de anamnesis:

- Datos demográficos extendidos, dolor (ubicación, intensidad, características JSON).
- Cuestionarios integrados: semáforo, creencias, apoyo, EVPER, sustancias, sueño, etc.
- Muchos campos son `TextField` con JSON serializado.
- `fechaCreacion` — usada en métricas del panel.

---

## Login — Reserva

| Campo | Notas |
|-------|-------|
| `paciente`, `clinico` | FK |
| `fecha`, `hora_inicio`, `hora_fin` | Validación solapamiento 07:00–21:00 |
| `estado` | Confirmada, Pendiente, Cancelada, etc. |
| `motivo` | Texto libre |

---

## Login — Cuestionarios (1:1 con CicloClinico)

| Modelo | Contenido principal |
|--------|---------------------|
| `CuestionarioPSFS` | 3 actividades + puntajes por sesión (JSON), nota |
| `Groc` | Lista de puntajes GROC + nota |
| `CuestionarioEQ_5D` | 5 dimensiones + VAS como listas por sesión |
| `CuestionarioBarthel` | 10 ítems ADL como JSON por sesión |
| `CuestionarioScrenning` | Screening Örebro (dolor funcional) |
| `CuestionarioEvaluacionENA` | `estado_por_sesion` JSON (niveles ENA) |

---

## Login — RecetaMedica

OneToOne `Paciente`. Campos: `medicamentos`, `indicaciones`, `NotaRecetaMedica`, `clinico`, `fecha_creacion`.

---

## Login — AuditoriaAcceso

| Campo | Notas |
|-------|-------|
| `accion` | ~33 códigos (ver doc 09) |
| `detalle` | Texto libre (ej. nombre cuestionario) |
| `paciente`, `clinico`, `clinica` | FK nullable SET_NULL |
| `es_admin_sistema`, `es_admin_centro` | Flags de rol al momento del evento |
| `ip_address` | Soporta `X-Forwarded-For` |
| `fecha` | auto_now_add |

---

## clinicas — Clinica

| Campo | Notas |
|-------|-------|
| `nombre` | |
| `tipo` | `individual` o `clinica` |
| `max_clinicos` | Cupo de profesionales |
| `logo` | ImageField → `media/clinicas/logos/` |
| `activa` | Boolean |

---

## clinicas — MembresiaClinica

| Campo | Notas |
|-------|-------|
| `clinico`, `clinica` | unique_together |
| `rol` | `admin` o `miembro` |
| `activo` | Solo una membresía activa por clínico |

---

## FormularioInicial — TokenFormulario

| Campo | Notas |
|-------|-------|
| `id` | UUID PK |
| `clinico`, `paciente` | FK |
| `activo`, `usado` | Control de uso único |
| `fecha_expiracion` | Días configurables al crear |
| `fecha_creacion` | |

Métodos: `crear_token()`, `is_valid()`, `marcar_como_usado()`, `desactivar()`.

---

## FormularioInicial — ConsentimientoDatos

| Campo | Notas |
|-------|-------|
| `paciente`, `clinica` | FK |
| `origen` | `formulario_qr` o `alta_panel` |
| `ip_address` | |
| `token` | FK opcional al token QR |
| `fecha` | auto |

---

## TiposDeFormularios — EvaluacionOswestry

10 secciones (0–5 cada una), múltiples evaluaciones por paciente. Métodos:

- `get_total_puntos()`, `get_porcentaje_incapacidad()`, `get_interpretacion()`.

---

## TiposDeFormularios — EvaluacionLEFS

20 actividades (0–4 cada una), múltiples evaluaciones. Métodos:

- `get_total_puntos()` (0–80), `get_porcentaje_funcionalidad()`, `get_interpretacion()`.

---

## SesionesKinesicas — SesionKinesica

| Campo | Notas |
|-------|-------|
| `paciente`, `clinico`, `ciclo` | FK — `ciclo` obligatorio |
| `numero_sesion` | unique con `ciclo` (se reinicia en cada ciclo) |
| `es_primera_sesion` | Evaluación inicial completa en JSON |
| `es_sesion_final` | Alta con diagnóstico, resumen, recomendaciones |
| `evaluacion_inicial` | JSONField (anamnesis kinésica detallada) |
| `notas_clinicas`, `evolucion` | Texto |
| `diagnostico_final`, `resumen_tratamiento`, `logros_obtenidos`, `estado_al_alta`, `recomendaciones_alta`, `plan_seguimiento` | Sesión final |

---

## Login — Notas

OneToOne `Paciente` (PK = paciente). Campo `notas` — notas libres del historial clínico.
