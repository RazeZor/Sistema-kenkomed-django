from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class EvaluacionLEFS(models.Model):
    """
    Escala Funcional de la Extremidad Inferior (LEFS)
    20 actividades, cada una puntúa de 0-4
    Resultado: suma total (rango 0-80)
    Mayor puntaje = mejor función
    """
    
    paciente = models.ForeignKey('Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_lefs')
    ciclo = models.ForeignKey(
        'ciclos_clinicos.CicloClinico',
        on_delete=models.CASCADE,
        related_name='evaluaciones_lefs',
    )
    clinico = models.ForeignKey('Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_lefs')
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    
    # 20 actividades del cuestionario (0-4 cada una)
    actividad_1_trabajo = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Trabajo usual, domestico o escuela"
    )
    actividad_2_pasatiempos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Pasatiempos, recreación o deportes"
    )
    actividad_3_banio = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Entrar o salir del baño"
    )
    actividad_4_andar_cuartos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Andar entre cuartos"
    )
    actividad_5_zapatos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Ponerse zapatos o calcetines"
    )
    actividad_6_cuclillas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Ponerse en cuclillas"
    )
    actividad_7_levantar_objeto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Levantar objeto del piso"
    )
    actividad_8_actividades_ligeras = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Actividades ligeras domesticas"
    )
    actividad_9_actividades_pesadas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Actividades pesadas domesticas"
    )
    actividad_10_coche = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Entrar o salir de un coche"
    )
    actividad_11_caminar_2cuadras = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Caminar 2 cuadras"
    )
    actividad_12_caminar_milla = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Caminar una milla"
    )
    actividad_13_escalones = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Subir o bajar 10 escalones"
    )
    actividad_14_estar_pie = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Estar de pie por 1 hora"
    )
    actividad_15_estar_sentado = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Estar sentado por 1 hora"
    )
    actividad_16_correr_plano = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Correr sobre suelo plano"
    )
    actividad_17_correr_desigual = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Correr sobre suelo desigual"
    )
    actividad_18_vueltas_bruscas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Hacer vueltas bruscas corriendo"
    )
    actividad_19_saltar = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Saltar"
    )
    actividad_20_vuelta_cama = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Darse la vuelta en la cama"
    )
    
    # Notas opcionales
    notas_clinicas = models.TextField(null=True, blank=True, help_text="Observaciones clínicas adicionales")
    
    class Meta:
        verbose_name = "Evaluación LEFS"
        verbose_name_plural = "Evaluaciones LEFS"
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f"LEFS - {self.paciente.nombre} ({self.fecha_evaluacion.strftime('%d/%m/%Y')})"
    
    def get_total_puntos(self):
        """Calcula la suma total de las 20 actividades"""
        total = (
            self.actividad_1_trabajo + self.actividad_2_pasatiempos +
            self.actividad_3_banio + self.actividad_4_andar_cuartos +
            self.actividad_5_zapatos + self.actividad_6_cuclillas +
            self.actividad_7_levantar_objeto + self.actividad_8_actividades_ligeras +
            self.actividad_9_actividades_pesadas + self.actividad_10_coche +
            self.actividad_11_caminar_2cuadras + self.actividad_12_caminar_milla +
            self.actividad_13_escalones + self.actividad_14_estar_pie +
            self.actividad_15_estar_sentado + self.actividad_16_correr_plano +
            self.actividad_17_correr_desigual + self.actividad_18_vueltas_bruscas +
            self.actividad_19_saltar + self.actividad_20_vuelta_cama
        )
        return total
    
    def get_porcentaje_funcionalidad(self):
        """Calcula el porcentaje de funcionalidad (total/80 * 100)"""
        return round((self.get_total_puntos() / 80) * 100, 1)
    
    def get_interpretacion(self):
        """Devuelve la interpretación clínica según el puntaje"""
        total = self.get_total_puntos()
        
        if total >= 72:  # 90-100%
            return {
                'nivel': 'Funcionalidad Excelente',
                'rango': '72-80 puntos',
                'descripcion': 'Mínima o ninguna limitación funcional. Paciente altamente funcional.',
                'recomendacion': 'Mantener nivel de actividad. Prevención de lesiones.'
            }
        elif total >= 64:  # 80-89%
            return {
                'nivel': 'Funcionalidad Buena',
                'rango': '64-71 puntos',
                'descripcion': 'Limitaciones funcionales leves. Buen nivel de independencia.',
                'recomendacion': 'Continuar rehabilitación. Enfoque en actividades específicas.'
            }
        elif total >= 48:  # 60-79%
            return {
                'nivel': 'Funcionalidad Moderada',
                'rango': '48-63 puntos',
                'descripcion': 'Limitaciones funcionales moderadas. Afecta actividades diarias.',
                'recomendacion': 'Intensificar tratamiento. Terapia funcional dirigida.'
            }
        elif total >= 32:  # 40-59%
            return {
                'nivel': 'Funcionalidad Limitada',
                'rango': '32-47 puntos',
                'descripcion': 'Limitaciones funcionales significativas. Dependencia parcial.',
                'recomendacion': 'Tratamiento intensivo. Considerar ayudas técnicas.'
            }
        elif total >= 16:  # 20-39%
            return {
                'nivel': 'Funcionalidad Severamente Limitada',
                'rango': '16-31 puntos',
                'descripcion': 'Limitaciones severas. Alta dependencia para actividades.',
                'recomendacion': 'URGENTE: Evaluación especializada. Intervención multidisciplinaria.'
            }
        else:  # 0-19%
            return {
                'nivel': 'Funcionalidad Mínima',
                'rango': '0-15 puntos',
                'descripcion': 'Dependencia casi total. Limitación funcional extrema.',
                'recomendacion': 'CRÍTICO: Evaluación médica urgente. Plan de cuidados integral.'
            }


class EvaluacionOswestry(models.Model):
    """
    Índice de Incapacidad de Oswestry (ODI)
    Escala para evaluar el grado de incapacidad por dolor lumbar
    10 secciones, cada una puntúa de 0-5
    Resultado: (suma x 2) = % incapacidad
    """
    
    paciente = models.ForeignKey('Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_oswestry')
    ciclo = models.ForeignKey(
        'ciclos_clinicos.CicloClinico',
        on_delete=models.CASCADE,
        related_name='evaluaciones_oswestry',
    )
    clinico = models.ForeignKey('Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_oswestry')
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    
    # 10 secciones del cuestionario (0-5 cada una)
    seccion_1_intensidad_dolor = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Intensidad del dolor"
    )
    seccion_2_estar_de_pie = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para estar de pie"
    )
    seccion_3_cuidados_personales = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Cuidados personales"
    )
    seccion_4_dormir = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Calidad del sueño"
    )
    seccion_5_levantar_peso = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para levantar peso"
    )
    seccion_6_actividad_sexual = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Actividad sexual"
    )
    seccion_7_andar = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para andar"
    )
    seccion_8_vida_social = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Vida social"
    )
    seccion_9_estar_sentado = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para estar sentado"
    )
    seccion_10_viajar = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para viajar"
    )
    
    # Notas opcionales
    notas_clinicas = models.TextField(null=True, blank=True, help_text="Observaciones clínicas adicionales")
    
    class Meta:
        verbose_name = "Evaluación Oswestry"
        verbose_name_plural = "Evaluaciones Oswestry"
        ordering = ['-fecha_evaluacion']
        unique_together = []
    
    def __str__(self):
        return f"ODI - {self.paciente.nombre} ({self.fecha_evaluacion.strftime('%d/%m/%Y')})"
    
    def get_total_puntos(self):
        """Calcula la suma total de las 10 secciones"""
        total = (
            self.seccion_1_intensidad_dolor +
            self.seccion_2_estar_de_pie +
            self.seccion_3_cuidados_personales +
            self.seccion_4_dormir +
            self.seccion_5_levantar_peso +
            self.seccion_6_actividad_sexual +
            self.seccion_7_andar +
            self.seccion_8_vida_social +
            self.seccion_9_estar_sentado +
            self.seccion_10_viajar
        )
        return total
    
    def get_porcentaje_incapacidad(self):
        """Calcula el porcentaje de incapacidad (total x 2)"""
        return self.get_total_puntos() * 2
    
    def get_interpretacion(self):
        """Devuelve la interpretación clínica según el porcentaje"""
        porcentaje = self.get_porcentaje_incapacidad()
        
        if porcentaje == 0:
            return {
                'nivel': 'Sin incapacidad',
                'rango': '0%',
                'descripcion': 'Sin limitación funcional. Paciente funcional normal.',
                'recomendacion': 'Mantener actividades normales. Reevaluar periódicamente.'
            }
        elif porcentaje <= 20:
            return {
                'nivel': 'Incapacidad mínima',
                'rango': '0-20%',
                'descripcion': 'Ligeras limitaciones en actividades. Síntomas leves.',
                'recomendacion': 'Continuar actividades con moderación. Educación en ergonomía.'
            }
        elif porcentaje <= 40:
            return {
                'nivel': 'Incapacidad moderada',
                'rango': '20-40%',
                'descripcion': 'Limitaciones moderadas. Interfiere con algunas actividades.',
                'recomendacion': 'Intensificar rehabilitación. Ajustar actividades laborales si es necesario.'
            }
        elif porcentaje <= 60:
            return {
                'nivel': 'Incapacidad severa',
                'rango': '40-60%',
                'descripcion': 'Limitaciones severas. Afecta significativamente la función.',
                'recomendacion': 'Tratamiento intensivo. Considerar referencias especializadas.'
            }
        elif porcentaje <= 80:
            return {
                'nivel': 'Incapacidad muy severa',
                'rango': '60-80%',
                'descripcion': 'Paciente incapacitado para la mayoría de actividades.',
                'recomendacion': 'URGENCIA: Consulta con especialista. Evaluación médica completa.'
            }
        else:
            return {
                'nivel': 'Incapacidad total',
                'rango': '80-100%',
                'descripcion': 'Incapacidad completa. Paciente confinado.',
                'recomendacion': 'CRÍTICO: Evaluación médica urgente. Posible referencia quirúrgica.'
            }


class EvaluacionQuickDASH(models.Model):
    """
    QuickDASH — discapacidad de hombro, codo y mano.
    11 ítems (escala 1–5). Puntuación: ((promedio) - 1) × 25 = % discapacidad.
    Requiere al menos 10 ítems completados.
    """

    paciente = models.ForeignKey(
        'Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_quickdash',
    )
    ciclo = models.ForeignKey(
        'ciclos_clinicos.CicloClinico',
        on_delete=models.CASCADE,
        related_name='evaluaciones_quickdash',
    )
    clinico = models.ForeignKey(
        'Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_quickdash',
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    notas_clinicas = models.TextField(null=True, blank=True)

    pregunta_1 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_2 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_3 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_4 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_5 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_6 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_7 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_8 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_9 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_10 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_11 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        verbose_name = 'Evaluación QuickDASH'
        verbose_name_plural = 'Evaluaciones QuickDASH'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'QuickDASH - {self.paciente.nombre} ({self.fecha_evaluacion.strftime("%d/%m/%Y")})'

    def _valores(self):
        from .quickdash_data import CAMPOS_QUICKDASH
        return [getattr(self, c) for c in CAMPOS_QUICKDASH]

    def get_porcentaje_discapacidad(self):
        valores = self._valores()
        n = len(valores)
        if n < 10:
            return None
        promedio = sum(valores) / n
        return round((promedio - 1) * 25, 1)

    def get_interpretacion(self):
        pct = self.get_porcentaje_discapacidad()
        if pct is None:
            return {'nivel': 'Incompleto', 'descripcion': 'Faltan ítems para calcular.'}
        if pct <= 20:
            nivel = 'Discapacidad leve'
        elif pct <= 40:
            nivel = 'Discapacidad moderada'
        elif pct <= 60:
            nivel = 'Discapacidad severa'
        else:
            nivel = 'Discapacidad muy severa'
        return {
            'nivel': nivel,
            'porcentaje': pct,
            'descripcion': f'Puntuación QuickDASH: {pct}% de discapacidad (mayor = peor).',
        }


class EvaluacionWOMAC(models.Model):
    """
    WOMAC — dolor, rigidez y función en artrosis de rodilla/cadera.
    24 ítems (0–4). Total 0–96; mayor puntuación = peor afectación.
    """

    paciente = models.ForeignKey(
        'Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_womac',
    )
    ciclo = models.ForeignKey(
        'ciclos_clinicos.CicloClinico',
        on_delete=models.CASCADE,
        related_name='evaluaciones_womac',
    )
    clinico = models.ForeignKey(
        'Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_womac',
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    respuestas = models.JSONField(help_text='Lista de 24 enteros (0–4) en orden WOMAC')
    notas_clinicas = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Evaluación WOMAC'
        verbose_name_plural = 'Evaluaciones WOMAC'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'WOMAC - {self.paciente.nombre} ({self.fecha_evaluacion.strftime("%d/%m/%Y")})'

    def get_puntaje_dolor(self):
        return sum(self.respuestas[0:5])

    def get_puntaje_rigidez(self):
        return sum(self.respuestas[5:7])

    def get_puntaje_funcion(self):
        return sum(self.respuestas[7:24])

    def get_total_puntos(self):
        return sum(self.respuestas)

    def get_porcentaje_afectacion(self):
        return round((self.get_total_puntos() / 96) * 100, 1)

    def get_interpretacion(self):
        total = self.get_total_puntos()
        if total <= 24:
            nivel = 'Afectación ligera'
        elif total <= 48:
            nivel = 'Afectación moderada'
        elif total <= 72:
            nivel = 'Afectación intensa'
        else:
            nivel = 'Afectación muy intensa'
        return {
            'nivel': nivel,
            'total': total,
            'dolor': self.get_puntaje_dolor(),
            'rigidez': self.get_puntaje_rigidez(),
            'funcion': self.get_puntaje_funcion(),
            'porcentaje': self.get_porcentaje_afectacion(),
            'descripcion': (
                f'Total {total}/96 — Dolor {self.get_puntaje_dolor()}/20, '
                f'Rigidez {self.get_puntaje_rigidez()}/8, '
                f'Función {self.get_puntaje_funcion()}/68.'
            ),
        }



class EvaluacionTUG(models.Model):
    """
    Timed Up and Go Test (TUG)
    El paciente se levanta de una silla, camina 3 metros, da la vuelta y regresa.
    Se registra el tiempo en segundos. Mayor tiempo = peor movilidad / mayor riesgo de caída.

    Baremos:
        < 10 s  -> Sin riesgo de caída
        10-12 s -> Riesgo leve
        12-20 s -> Riesgo moderado de caída
        > 20 s  -> Riesgo severo / dependencia funcional
    """

    paciente = models.ForeignKey(
        'Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_tug',
    )
    ciclo = models.ForeignKey(
        'ciclos_clinicos.CicloClinico',
        on_delete=models.CASCADE,
        related_name='evaluaciones_tug',
    )
    clinico = models.ForeignKey(
        'Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_tug',
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)

    tiempo_segundos = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text='Tiempo en segundos que tardó el paciente en completar el test',
    )

    usa_ayuda_marcha = models.BooleanField(
        default=False,
        help_text='El paciente utilizó dispositivo de ayuda durante el test',
    )

    observaciones = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de observaciones clínicas marcadas durante el test',
    )

    notas_clinicas = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Evaluación TUG'
        verbose_name_plural = 'Evaluaciones TUG'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'TUG - {self.paciente.nombre} ({self.fecha_evaluacion.strftime("%d/%m/%Y")}) — {self.tiempo_segundos}s'

    def get_interpretacion(self):
        """Devuelve interpretación clínica según los baremos del TUG."""
        t = self.tiempo_segundos

        if t < 10:
            return {
                'nivel': 'Sin riesgo de caída',
                'riesgo': 'ninguno',
                'color': 'green',
                'rango': '< 10 segundos',
                'descripcion': 'Movilidad funcional normal. Sin riesgo de caída identificado.',
                'recomendacion': 'Mantener nivel de actividad física. Control periódico.',
                'dss_status': 'success',
                'dss_bullets': [
                    'Movilidad funcional conservada.',
                    'Tiempo dentro de los rangos normativos para adultos.',
                ],
            }
        elif t < 12:
            return {
                'nivel': 'Riesgo leve',
                'riesgo': 'leve',
                'color': 'yellow',
                'rango': '10–12 segundos',
                'descripcion': 'Movilidad levemente reducida. Zona limítrofe de riesgo de caída.',
                'recomendacion': 'Valorar entrenamiento de equilibrio y fortalecimiento de MMII.',
                'dss_status': 'warning',
                'dss_bullets': [
                    'Tiempo en zona limítrofe (10–12 s). Vigilancia recomendada.',
                    'Considerar evaluación de equilibrio estático y dinámico.',
                    'Valorar entrenamiento preventivo de caídas.',
                ],
            }
        elif t <= 20:
            return {
                'nivel': 'Riesgo moderado de caída',
                'riesgo': 'moderado',
                'color': 'orange',
                'rango': '12–20 segundos',
                'descripcion': 'El paciente presenta riesgo significativo de caída (>=12 s). Movilidad reducida.',
                'recomendacion': (
                    'Implementar programa de equilibrio y marcha. '
                    'Evaluar entorno domiciliario. Considerar fisioterapia preventiva de caídas.'
                ),
                'dss_status': 'danger',
                'dss_bullets': [
                    'TUG >= 12 s: riesgo de caída confirmado según literatura clínica.',
                    'Riesgo moderado: el paciente puede movilizarse pero con limitaciones.',
                    'Recomendar programa de entrenamiento de equilibrio (ej. Otago, Tai Chi).',
                    'Revisar medicación que pueda afectar el equilibrio.',
                    'Evaluar necesidad de dispositivo de ayuda a la marcha.',
                ],
            }
        else:
            return {
                'nivel': 'Riesgo severo / Dependencia funcional',
                'riesgo': 'severo',
                'color': 'red',
                'rango': '> 20 segundos',
                'descripcion': (
                    'Movilidad severamente comprometida. Alto riesgo de caída y dependencia funcional.'
                ),
                'recomendacion': (
                    'Derivar urgente a programa especializado de rehabilitación de marcha y equilibrio. '
                    'Evaluar necesidad de apoyo domiciliario. Notificar a médico tratante.'
                ),
                'dss_status': 'danger',
                'dss_bullets': [
                    'TUG > 20 s: dependencia funcional significativa.',
                    'Alto riesgo de caídas con posibles consecuencias graves.',
                    'Derivar a programa especializado de rehabilitación.',
                    'Considerar evaluación de adaptaciones del hogar.',
                    'Notificar al médico tratante para evaluación integral.',
                    'Valorar necesidad de apoyo de cuidador.',
                ],
            }


class EvaluacionBerg(models.Model):
    """
    Escala de Equilibrio de Berg (Berg Balance Scale - BBS)
    Evaluación cuantitativa del equilibrio funcional en 14 tareas diarias (0-4 pts por ítem).
    Puntuación total: 0 a 56. Mayor puntaje = mejor equilibrio.

    Baremos de Riesgo de Caída:
        0-20  -> Alto riesgo de caída
        21-40 -> Moderado riesgo de caída
        41-56 -> Leve / Bajo riesgo de caída

    Corte clínico: < 45 indica alteración del equilibrio. >= 45 para deambulación independiente segura.

    Grupos Funcionales:
        33-39 -> Inicio de bipedestación
        40-44 -> Inicio de marcha
        45-49 -> Marcha con/sin ayudas técnicas
        50-54 -> Marcha independiente
        55-56 -> Marcha funcional
    """

    paciente = models.ForeignKey(
        'Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_berg',
    )
    ciclo = models.ForeignKey(
        'ciclos_clinicos.CicloClinico',
        on_delete=models.CASCADE,
        related_name='evaluaciones_berg',
    )
    clinico = models.ForeignKey(
        'Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_berg',
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)

    item_01 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="1. Sedestación a bipedestación (0-4)")
    item_02 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="2. Bipedestación sin ayuda 2 min (0-4)")
    item_03 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="3. Sedestación sin apoyar espalda 2 min (0-4)")
    item_04 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="4. Bipedestación a sedestación (0-4)")
    item_05 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="5. Transferencias (0-4)")
    item_06 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="6. Bipedestación ojos cerrados 10s (0-4)")
    item_07 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="7. Bipedestación pies juntos 1 min (0-4)")
    item_08 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="8. Brazo extendido hacia delante (0-4)")
    item_09 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="9. Recoger objeto del suelo (0-4)")
    item_10 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="10. Girarse para mirar atrás (0-4)")
    item_11 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="11. Girar 360 grados (0-4)")
    item_12 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="12. Subir pies al escalón alternante (0-4)")
    item_13 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="13. Pies en tándem (0-4)")
    item_14 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], help_text="14. Bipedestación sobre un pie (0-4)")

    notas_clinicas = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Evaluación Berg'
        verbose_name_plural = 'Evaluaciones Berg'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'Berg - {self.paciente.nombre} ({self.fecha_evaluacion.strftime("%d/%m/%Y")}) — {self.get_total_puntos()}/56 pts'

    def get_total_puntos(self):
        items = [
            self.item_01, self.item_02, self.item_03, self.item_04, self.item_05,
            self.item_06, self.item_07, self.item_08, self.item_09, self.item_10,
            self.item_11, self.item_12, self.item_13, self.item_14,
        ]
        return sum(item for item in items if item is not None)

    def get_interpretacion(self):
        total = self.get_total_puntos()

        # Grupo funcional motor
        if total >= 55:
            grupo = 'Marcha funcional'
        elif total >= 50:
            grupo = 'Marcha independiente'
        elif total >= 45:
            grupo = 'Marcha con/sin ayudas técnicas'
        elif total >= 40:
            grupo = 'Inicio de marcha'
        elif total >= 33:
            grupo = 'Inicio de bipedestación'
        else:
            grupo = 'Fase inicial de sedestación / control postural'

        # Deambulación independiente
        deambulación_segura = total >= 45

        # Baremos de riesgo de caída
        if total <= 20:
            nivel = 'Alto riesgo de caída'
            riesgo = 'alto'
            color = 'red'
            dss_status = 'danger'
            rango = '0–20 puntos'
            descripcion = 'Equilibrio severamente afectado. Alto riesgo de caídas recurrentes.'
            recomendacion = 'Requerimiento de supervisión continua y asistencia asistencial. Entrenamiento intenso de control postural estático.'
        elif total <= 40:
            nivel = 'Moderado riesgo de caída'
            riesgo = 'moderado'
            color = 'orange'
            dss_status = 'warning'
            rango = '21–40 puntos'
            descripcion = 'Equilibrio moderadamente alterado. Mayor a 12 veces más probabilidad de caída que pacientes >40 pts.'
            recomendacion = 'Programa enfocado en transferencias, transferencias de peso y apoyo en marcha asistida.'
        else:
            nivel = 'Leve / Bajo riesgo de caída'
            riesgo = 'leve'
            color = 'green'
            dss_status = 'success'
            rango = '41–56 puntos'
            descripcion = 'Buen control del equilibrio postural estático y dinámico.'
            recomendacion = 'Mantenimiento y reeducación de la marcha independiente sin apoyos o con asistencia mínima.'

        bullets = [
            f'Puntaje total: {total}/56 puntos ({rango}).',
            f'Nivel de riesgo de caídas: {nivel}.',
            f'Grupo de capacidad motora/funcional: {grupo}.',
            'Punto de corte >= 45 pts: ' + ('Superado (Deambulación independiente segura).' if deambulación_segura else 'No alcanzado (Indicador de alteración del equilibrio).'),
        ]

        if total < 40:
            bullets.append('Nota clínica: Pacientes con < 40 pts presentan casi 12 veces más probabilidad de sufrir caídas.')

        return {
            'nivel': nivel,
            'riesgo': riesgo,
            'color': color,
            'rango': rango,
            'total': total,
            'grupo_funcional': grupo,
            'deambulacion_segura': deambulación_segura,
            'descripcion': descripcion,
            'recomendacion': recomendacion,
            'dss_status': dss_status,
            'dss_bullets': bullets,
        }


class EvaluacionTinetti(models.Model):
    """
    Escala de Tinetti para la Evaluación de Equilibrio y Marcha
    Subescala de Equilibrio (9 ítems, 0-16 pts) + Subescala de Marcha (7 ítems, 0-12 pts).
    Puntuación Total: 0 a 28 pts.

    Baremos de Riesgo de Caída:
        <= 18 pts -> Alto riesgo de caída
        19-24 pts -> Moderado riesgo de caída
        25-28 pts -> Bajo / Sin riesgo de caída
    """

    paciente = models.ForeignKey(
        'Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_tinetti',
    )
    ciclo = models.ForeignKey(
        'ciclos_clinicos.CicloClinico',
        on_delete=models.CASCADE,
        related_name='evaluaciones_tinetti',
    )
    clinico = models.ForeignKey(
        'Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_tinetti',
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)

    # Subescala Equilibrio (9 ítems)
    eq_01_sentado = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)], help_text="Equilibrio sentado (0-1)")
    eq_02_levantarse = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Levantarse (0-2)")
    eq_03_intentos = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Intentos para levantarse (0-2)")
    eq_04_equi_inmediato = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Equilibrio inmediato primeros 5s (0-2)")
    eq_05_equi_bipedestacion = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Equilibrio en bipedestación (0-2)")
    eq_06_empujon = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Empujón tórax 3 veces (0-2)")
    eq_07_ojos_cerrados = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)], help_text="Ojos cerrados pies juntos (0-1)")
    eq_08_giro_360 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Giro 360 grados (0-2)")
    eq_09_sentarse = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Sentarse (0-2)")

    # Subescala Marcha (7 ítems)
    ma_01_iniciacion = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)], help_text="Iniciación de la marcha (0-1)")
    ma_02_longitud_altura = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Longitud y altura del paso (0-2)")
    ma_03_simetria = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)], help_text="Simetría del paso (0-1)")
    ma_04_continuidad = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)], help_text="Continuidad de los pasos (0-1)")
    ma_05_trayectoria = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Trayectoria (0-2)")
    ma_06_tronco = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], help_text="Tronco (0-2)")
    ma_07_postura_marcha = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)], help_text="Postura al caminar (0-1)")

    notas_clinicas = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Evaluación Tinetti'
        verbose_name_plural = 'Evaluaciones Tinetti'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'Tinetti - {self.paciente.nombre} ({self.fecha_evaluacion.strftime("%d/%m/%Y")}) — Total: {self.get_total_puntos()}/28 pts'

    def get_puntaje_equilibrio(self):
        items = [
            self.eq_01_sentado, self.eq_02_levantarse, self.eq_03_intentos,
            self.eq_04_equi_inmediato, self.eq_05_equi_bipedestacion,
            self.eq_06_empujon, self.eq_07_ojos_cerrados, self.eq_08_giro_360,
            self.eq_09_sentarse,
        ]
        return sum(item for item in items if item is not None)

    def get_puntaje_marcha(self):
        items = [
            self.ma_01_iniciacion, self.ma_02_longitud_altura, self.ma_03_simetria,
            self.ma_04_continuidad, self.ma_05_trayectoria, self.ma_06_tronco,
            self.ma_07_postura_marcha,
        ]
        return sum(item for item in items if item is not None)

    def get_total_puntos(self):
        return self.get_puntaje_equilibrio() + self.get_puntaje_marcha()

    def get_interpretacion(self):
        total = self.get_total_puntos()
        eq = self.get_puntaje_equilibrio()
        ma = self.get_puntaje_marcha()

        if total <= 18:
            nivel = 'Alto riesgo de caída'
            riesgo = 'alto'
            color = 'red'
            dss_status = 'danger'
            rango = '<= 18 puntos'
            descripcion = 'Riesgo elevado de caídas con compromiso severo de la marcha y/o el equilibrio.'
            recomendacion = 'Diseñar plan de intervención integral con énfasis en reeducación de la marcha, fortalecimiento y uso de órtesis/ayuda técnica.'
        elif total <= 24:
            nivel = 'Moderado riesgo de caída'
            riesgo = 'moderado'
            color = 'orange'
            dss_status = 'warning'
            rango = '19–24 puntos'
            descripcion = 'Alteración moderada del equilibrio o de la marcha. Riesgo intermedio de caídas.'
            recomendacion = 'Treinamiento dinámico del equilibrio, ejercicios de coordinación y prevención de caídas.'
        else:
            nivel = 'Bajo / Sin riesgo de caída'
            riesgo = 'bajo'
            color = 'green'
            dss_status = 'success'
            rango = '25–28 puntos'
            descripcion = 'Patrón de marcha y equilibrio funcionales sin riesgo elevado de caídas.'
            recomendacion = 'Mantener acondicionamiento físico y reevaluar periódicamente.'

        bullets = [
            f'Puntuación total: {total}/28 pts (Equilibrio: {eq}/16 pts, Marcha: {ma}/12 pts).',
            f'Nivel de riesgo de caídas: {nivel} ({rango}).',
            'Desglose subescalas: ' + ('Equilibrio descendido' if eq < 10 else 'Equilibrio funcional') + ' | ' + ('Marcha descendida' if ma < 8 else 'Marcha funcional'),
        ]

        return {
            'nivel': nivel,
            'riesgo': riesgo,
            'color': color,
            'rango': rango,
            'total': total,
            'equilibrio': eq,
            'marcha': ma,
            'descripcion': descripcion,
            'recomendacion': recomendacion,
            'dss_status': dss_status,
            'dss_bullets': bullets,
        }

