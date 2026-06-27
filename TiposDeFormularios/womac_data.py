"""Ítems del cuestionario WOMAC — versión española (Likert 0–4)."""

WOMAC_INSTRUCCIONES = (
    'Indique cuánto dolor, rigidez o dificultad ha notado en sus caderas y/o rodillas '
    'como consecuencia de su artrosis durante los últimos días. '
    '0 = Ninguno/a · 1 = Poco/a · 2 = Bastante · 3 = Mucho/a · 4 = Muchísimo/a'
)

WOMAC_SECCIONES = (
    {
        'id': 'dolor',
        'titulo': 'A. Dolor',
        'pregunta': '¿Cuánto dolor tiene?',
        'items': (
            'Al andar por terreno llano',
            'Al subir o bajar escaleras',
            'Por la noche en la cama',
            'Al estar sentado o tumbado',
            'Al estar de pie',
        ),
    },
    {
        'id': 'rigidez',
        'titulo': 'B. Rigidez',
        'pregunta': '¿Cuánta rigidez nota?',
        'items': (
            'Después de despertarse por la mañana',
            'Durante el resto del día, después de estar sentado, tumbado o descansando',
        ),
    },
    {
        'id': 'funcion',
        'titulo': 'C. Capacidad funcional',
        'pregunta': '¿Qué grado de dificultad tiene al…?',
        'items': (
            'Bajar escaleras',
            'Subir escaleras',
            'Levantarse después de estar sentado',
            'Estar de pie',
            'Agacharse para coger algo del suelo',
            'Andar por un terreno llano',
            'Entrar y salir de un coche',
            'Ir de compras',
            'Ponerse las medias o los calcetines',
            'Levantarse de la cama',
            'Quitarse las medias o los calcetines',
            'Estar tumbado en la cama',
            'Entrar y salir de la ducha o bañera',
            'Estar sentado',
            'Sentarse y levantarse del retrete',
            'Hacer tareas domésticas pesadas',
            'Hacer tareas domésticas ligeras',
        ),
    },
)

WOMAC_ETIQUETAS = (
    (0, 'Ninguno/a'),
    (1, 'Poco/a'),
    (2, 'Bastante'),
    (3, 'Mucho/a'),
    (4, 'Muchísimo/a'),
)

WOMAC_TOTAL_ITEMS = sum(len(s['items']) for s in WOMAC_SECCIONES)
