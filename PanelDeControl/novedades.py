# PanelDeControl/novedades.py
# Lista centralizada de actualizaciones para mostrar en el "Release Notes" de KenkoMed

# La versión actual (última versión liberada). Si es mayor a clinico.version_novedades_leida, muestra popup.
VERSION_ACTUAL = "v1.2"

# Historial de actualizaciones. La primera de la lista debe ser la más reciente.
NOVEDADES_HISTORIAL = [
    {
        "version": "v1.2",
        "fecha": "Septiembre 2026",
        "titulo": "Nuevo Módulo de Pagos y Packs",
        "items": [
            {
                "icono": "bx-wallet",
                "titulo": "Packs de Atención",
                "descripcion": "Vende packs de 10 sesiones y descuéntalos de manera sencilla a medida que tus pacientes asisten."
            },
            {
                "icono": "bx-transfer",
                "titulo": "Cruce Automático de Deuda",
                "descripcion": "Ahora las sesiones kinésicas se enlazan automáticamente a los pagos ingresados, calculando la deuda exacta de cada paciente sin márgenes de error."
            },
            {
                "icono": "bx-line-chart",
                "titulo": "Dashboard Financiero",
                "descripcion": "Controla los ingresos del mes, detecta pacientes con deudas y lleva un registro de bonos por cobrar de un solo vistazo."
            }
        ]
    },
    {
        "version": "v1.1",
        "fecha": "Septiembre 2026",
        "titulo": "Nuevas Herramientas y Mejoras",
        "items": [
            {
                "icono": "bx-microphone",
                "titulo": "Dictado por Voz Integrado",
                "descripcion": "Ahorra tiempo dictando tus notas clínicas y evoluciones directamente usando el micrófono (procesado de forma segura)."
            },
            {
                "icono": "bx-list-check",
                "titulo": "Nuevas Escalas Funcionales",
                "descripcion": "Agregamos evaluaciones clave como Timed Up & Go (TUG), Single Leg Squat, Drop Test, Berg y Tinetti."
            },
            {
                "icono": "bx-palette",
                "titulo": "Colores en la Agenda",
                "descripcion": "Mejoramos la organización visual de tus citas con nuevos códigos de color según su estado."
            }
        ]
    }
]
