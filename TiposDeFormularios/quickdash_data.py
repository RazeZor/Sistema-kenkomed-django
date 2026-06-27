"""Ítems del cuestionario QuickDASH (español Puerto Rico / IWH)."""

QUICKDASH_INSTRUCCIONES = (
    'Conteste según su condición durante la última semana. '
    'Si no pudo realizar una actividad, elija la respuesta que mejor describa '
    'su situación si hubiese podido hacerla.'
)

# (campo, texto, tipo_escala)
# tipo: 'dificultad' | 'impacto_social' | 'limitacion' | 'sintoma'
QUICKDASH_PREGUNTAS = (
    ('pregunta_1', 'Abrir un pote que tenga la tapa apretada, dándole vueltas', 'dificultad'),
    ('pregunta_2', 'Realizar los quehaceres del hogar más fuertes (lavar ventanas, mapear)', 'dificultad'),
    ('pregunta_3', 'Cargar una bolsa de compra o un maletín', 'dificultad'),
    ('pregunta_4', 'Lavarse la espalda', 'dificultad'),
    ('pregunta_5', 'Usar un cuchillo para cortar alimentos', 'dificultad'),
    (
        'pregunta_6',
        'Actividades recreativas con impacto en el brazo, hombro o mano '
        '(batear, golf, tenis, etc.)',
        'dificultad',
    ),
    (
        'pregunta_7',
        '¿Hasta qué punto el problema dificultó las actividades sociales '
        'con familiares, amigos o grupos?',
        'impacto_social',
    ),
    (
        'pregunta_8',
        '¿Tuvo que limitar su trabajo u otras actividades diarias por el problema '
        'del brazo, hombro o mano?',
        'limitacion',
    ),
    ('pregunta_9', 'Dolor de brazo, hombro o mano', 'sintoma'),
    ('pregunta_10', 'Hormigueo en el brazo, hombro o mano', 'sintoma'),
    (
        'pregunta_11',
        '¿Cuánta dificultad ha tenido para dormir a causa del dolor '
        'de brazo, hombro o mano?',
        'dificultad',
    ),
)

ESCALAS_RESPUESTA = {
    'dificultad': (
        (1, 'Ninguna dificultad'),
        (2, 'Poca dificultad'),
        (3, 'Dificultad moderada'),
        (4, 'Mucha dificultad'),
        (5, 'Incapaz'),
    ),
    'impacto_social': (
        (1, 'En lo absoluto'),
        (2, 'Poco'),
        (3, 'Moderadamente'),
        (4, 'Bastante'),
        (5, 'Muchísimo'),
    ),
    'limitacion': (
        (1, 'En lo absoluto'),
        (2, 'Poco'),
        (3, 'Moderadamente'),
        (4, 'Mucho'),
        (5, 'Totalmente'),
    ),
    'sintoma': (
        (1, 'Ninguna'),
        (2, 'Poca'),
        (3, 'Moderada'),
        (4, 'Mucha'),
        (5, 'Muchísima'),
    ),
}

CAMPOS_QUICKDASH = [p[0] for p in QUICKDASH_PREGUNTAS]
