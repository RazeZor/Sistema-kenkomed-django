# 09 — Privacidad y cumplimiento (Ley 21.719)

KenkoMed actúa como **encargado del tratamiento**; cada centro/clínica es **responsable** frente a sus pacientes.

---

## Funcionalidades implementadas en código

### 1. Aviso de privacidad

- **URL pública:** `/privacidad-paciente/`
- **Plantilla:** `templates/privacidad_paciente.html`
- Explica responsable, encargado, finalidades, derechos ARCO, plazos de conservación.

### 2. Consentimiento

- **Modelo:** `FormularioInicial.ConsentimientoDatos`
- **Origen `formulario_qr`:** checkbox obligatorio en formulario público; guarda IP y token.
- **Origen `alta_panel`:** previsto en modelo; pendiente de implementar en alta manual del panel.

### 3. Exportación ARCO (portabilidad / acceso)

**Vista:** `PanelDeControl.views_privacidad.exportar_ficha`  
**URL:** `/panel/exportar-ficha/?rut=...&format=json|html`

- **JSON:** esquema `kenkomed-arco-v1` — `PanelDeControl/exportacion.py`
- **HTML:** ficha profesional descargable vía `RenderFichaClinica`

Incluye: paciente, anamnesis, todos los cuestionarios, sesiones kinésicas, reservas, receta, notas.

### 4. Auditoría de accesos

**Modelo:** `Login.AuditoriaAcceso`  
**Registro:** `Login/auditoria.py` → `registrar_auditoria()`

#### Tipos de acción registrados

| Categoría | Acciones |
|-----------|----------|
| Historial | `consulta_historial`, `edicion_nota_clinica` |
| Informes | `consulta_informe_dss`, `consulta_ficha_profesional`, `consulta_resumen_paciente` |
| Pacientes | `alta_paciente`, `edicion_paciente`, `eliminacion_paciente`, `consulta_lista_pacientes` |
| ARCO | `exportacion_arco_json`, `exportacion_arco_html` |
| Reservas | `reserva_crear`, `reserva_modificar`, `reserva_eliminar`, `consulta_calendario` |
| Cuestionarios | `consulta_cuestionario`, `edicion_cuestionario` |
| Sesiones kiné | `consulta_lista_sesiones_kine`, `consulta_sesion_kine`, `alta_sesion_kine`, `edicion_sesion_kine` |
| Recetas | `consulta_receta`, `receta_crear`, `receta_editar`, `receta_eliminar` |
| Anamnesis / QR | `consulta_formulario_inicial`, `edicion_anamnesis`, `qr_generar`, `qr_desactivar`, `formulario_qr_enviado` |
| Estadísticas | `consulta_estadisticas_centro`, `consulta_estadisticas_paciente` |
| Auditoría meta | `consulta_auditoria`, `exportacion_auditoria_pdf` |

#### Vista de auditoría

- **URL:** `/panel/auditoria-accesos/`
- **Permiso:** admin del centro (`@requiere_admin_auditoria`)
- **Filtro:** últimos 30, 90 o 180 días (máx. 1000 registros)
- **PDF:** `/panel/auditoria-accesos/exportar-pdf/` — `auditoria_pdf.py` (ReportLab)

Cada registro almacena: paciente, clínico, clínica, IP, flags admin, detalle, fecha.

---

## Seguridad técnica (settings)

Con `DJANGO_DEBUG=False`:

- `SECRET_KEY` obligatoria
- Redirect HTTPS, cookies seguras, HSTS
- `SECURE_PROXY_SSL_HEADER` para proxy Cloudflare/Nginx
- Contraseñas hasheadas (`make_password`)
- Aislamiento por `clinica_id` en todas las consultas
- Correos sin datos clínicos sensibles en asunto

---

## Lo que requiere trabajo operativo/legal (fuera del código)

| Ítem | Estado |
|------|--------|
| DPA / contrato encargado con cada clínica | Documento legal |
| Procedimiento ARCO para clínicas | Operativo |
| Backups automáticos en producción | Infraestructura |
| Consentimiento en alta manual panel | Código pendiente |
| Registro de actividades de tratamiento | Documento |
| Plan de respuesta a brechas | Documento interno |

---

## Recomendaciones para piloto

1. Firmar anexo de encargado con clínica piloto.
2. Designar contacto ARCO en cada centro.
3. Aplicar migraciones `0068`, `0069` en producción.
4. `DEBUG=False` y backups diarios de MySQL.
5. Capacitar: no compartir logins; revisar auditoría periódicamente.
