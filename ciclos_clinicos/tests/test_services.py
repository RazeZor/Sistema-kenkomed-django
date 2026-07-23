"""Tests de reglas de negocio — ciclos clínicos."""
from django.test import TestCase

from Login.models import Clinico, Paciente
from SesionesKinesicas.models import SesionKinesica
from clinicas.models import Clinica, MembresiaClinica
from ciclos_clinicos.models import CicloClinico
from ciclos_clinicos.services import (
    CicloClinicoError,
    abandonar_ciclo,
    finalizar_ciclo,
    iniciar_nuevo_ciclo,
)
from Login.models import formularioClinico


class CicloClinicoServicesTests(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create(nombre='Centro Test', rut='11111111-1')
        self.clinico = Clinico.objects.create(
            rut='22222222-2', nombre='Ana', apellido='Kine', profesion='Kinesióloga',
        )
        MembresiaClinica.objects.create(clinico=self.clinico, clinica=self.clinica, activo=True)
        self.paciente = Paciente.objects.create(
            rut='33333333-3',
            nombre='Juan',
            apellido='Pérez',
            clinica=self.clinica,
            clinico=self.clinico,
        )

    def test_no_dos_ciclos_activos(self):
        iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        with self.assertRaises(CicloClinicoError):
            iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)

    def test_iniciar_incrementa_numero_ciclo(self):
        c1 = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        finalizar_ciclo(c1, self.clinico)
        c2 = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        self.assertEqual(c1.numero_ciclo, 1)
        self.assertEqual(c2.numero_ciclo, 2)

    def test_sesion_final_marca_ciclo_finalizado(self):
        ciclo = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        SesionKinesica.objects.create(
            paciente=self.paciente,
            ciclo=ciclo,
            clinico=self.clinico,
            numero_sesion=1,
            es_primera_sesion=True,
        )
        sesion_final = SesionKinesica.objects.create(
            paciente=self.paciente,
            ciclo=ciclo,
            clinico=self.clinico,
            numero_sesion=2,
            es_sesion_final=True,
        )
        finalizar_ciclo(ciclo, self.clinico)
        ciclo.refresh_from_db()
        self.assertEqual(ciclo.estado, CicloClinico.ESTADO_FINALIZADO)
        self.assertTrue(sesion_final.es_sesion_final)

    def test_anamnesis_ciclo_2_no_sobrescribe_ciclo_1(self):
        c1 = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        formularioClinico.objects.create(
            ciclo=c1, paciente=self.paciente, clinico=self.clinico,
            caracteristicasDeDolor='["c1"]',
        )
        finalizar_ciclo(c1, self.clinico)
        c2 = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        formularioClinico.objects.create(
            ciclo=c2, paciente=self.paciente, clinico=self.clinico,
            caracteristicasDeDolor='["c2"]',
        )
        self.assertEqual(c1.formulario.caracteristicasDeDolor, '["c1"]')
        self.assertEqual(c2.formulario.caracteristicasDeDolor, '["c2"]')

    def test_numero_sesion_reinicia_en_ciclo_2(self):
        c1 = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        SesionKinesica.objects.create(
            paciente=self.paciente, ciclo=c1, clinico=self.clinico,
            numero_sesion=1, es_primera_sesion=True,
        )
        SesionKinesica.objects.create(
            paciente=self.paciente, ciclo=c1, clinico=self.clinico,
            numero_sesion=2,
        )
        finalizar_ciclo(c1, self.clinico)
        c2 = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        SesionKinesica.objects.create(
            paciente=self.paciente, ciclo=c2, clinico=self.clinico,
            numero_sesion=1, es_primera_sesion=True,
        )
        self.assertEqual(
            SesionKinesica.objects.filter(ciclo=c2, numero_sesion=1).count(), 1,
        )

    def test_abandonar_ciclo_activo(self):
        ciclo = iniciar_nuevo_ciclo(self.paciente, self.clinica, self.clinico)
        abandonar_ciclo(ciclo, self.clinico, motivo='No asistió')
        ciclo.refresh_from_db()
        self.assertEqual(ciclo.estado, CicloClinico.ESTADO_ABANDONADO)
