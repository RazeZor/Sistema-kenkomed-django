from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from typing import Optional, Tuple, Dict, Any
import logging

from Login.models import Paciente, Clinico, RecetaMedica

logger = logging.getLogger(__name__)


# ========== SERVICIOS DE AUTENTICACIÓN ==========
class AuthService:
    """Servicio para manejar autenticación y permisos"""
    
    @staticmethod
    def verificar_sesion(request) -> Optional[Dict[str, Any]]:
        """Verifica si existe sesión activa y retorna datos del clínico"""
        if 'nombre_clinico' not in request.session:
            return None
        
        return {
            'rut_clinico': request.session.get('rut_clinico'),
            'nombre_clinico': request.session.get('nombre_clinico'),
            'es_admin': request.session.get('es_admin', False)
        }
    
    @staticmethod
    def obtener_clinico(rut_clinico: str) -> Optional[Clinico]:
        """Obtiene el clínico por RUT"""
        try:
            return Clinico.objects.get(rut=rut_clinico)
        except ObjectDoesNotExist:
            logger.error(f"Clínico no encontrado: {rut_clinico}")
            return None
    
    @staticmethod
    def verificar_permiso_paciente(paciente: Paciente, clinico: Clinico, es_admin: bool) -> bool:
        """Verifica si el clínico tiene permiso para acceder al paciente"""
        return es_admin or paciente.clinico == clinico


# ========== SERVICIOS DE PACIENTE ==========
class PacienteService:
    """Servicio para operaciones relacionadas con pacientes"""
    
    @staticmethod
    def buscar_paciente_por_rut(rut: str) -> Optional[Paciente]:
        """Busca un paciente por RUT"""
        try:
            rut = rut.strip()
            if not rut:
                return None
            return Paciente.objects.get(rut=rut)
        except ObjectDoesNotExist:
            logger.info(f"Paciente no encontrado: {rut}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar paciente {rut}: {str(e)}")
            return None


# ========== SERVICIOS DE RECETA ==========
class RecetaService:
    """Servicio para operaciones CRUD de recetas médicas"""
    
    @staticmethod
    def obtener_receta(paciente: Paciente) -> Optional[RecetaMedica]:
        """Obtiene la receta de un paciente"""
        try:
            return RecetaMedica.objects.filter(paciente=paciente).first()
        except Exception as e:
            logger.error(f"Error al obtener receta del paciente {paciente.rut}: {str(e)}")
            return None
    
    @staticmethod
    @transaction.atomic
    def crear_receta(paciente: Paciente, clinico: Clinico, datos: Dict[str, str]) -> Tuple[bool, str, Optional[RecetaMedica]]:
        """
        Crea una nueva receta médica
        Returns: (éxito, mensaje, receta)
        """
        try:
            # Verificar si ya existe receta
            if RecetaMedica.objects.filter(paciente=paciente).exists():
                return False, "El paciente ya tiene una receta registrada.", None
            
            # Validar datos
            medicamentos = datos.get('medicamentos', '').strip()
            indicaciones = datos.get('indicaciones', '').strip()
            notas = datos.get('notas', '').strip()
            
            if not medicamentos:
                return False, "Los medicamentos son obligatorios.", None
            
            # Crear receta
            receta = RecetaMedica.objects.create(
                paciente=paciente,
                clinico=clinico,
                medicamentos=medicamentos,
                indicaciones=indicaciones,
                NotaRecetaMedica=notas
            )
            
            logger.info(f"Receta creada para paciente {paciente.rut} por clínico {clinico.rut}")
            return True, "Receta médica creada exitosamente.", receta
            
        except ValidationError as e:
            logger.error(f"Error de validación al crear receta: {str(e)}")
            return False, "Error de validación en los datos de la receta.", None
        except Exception as e:
            logger.error(f"Error inesperado al crear receta: {str(e)}")
            return False, "Error al crear la receta médica.", None
    
    @staticmethod
    @transaction.atomic
    def actualizar_receta(receta: RecetaMedica, datos: Dict[str, str]) -> Tuple[bool, str]:
        """
        Actualiza una receta existente
        Returns: (éxito, mensaje)
        """
        try:
            if not receta:
                return False, "No existe una receta para editar."
            
            medicamentos = datos.get('medicamentos', '').strip()
            if not medicamentos:
                return False, "Los medicamentos son obligatorios."
            
            receta.medicamentos = medicamentos
            receta.indicaciones = datos.get('indicaciones', '').strip()
            receta.NotaRecetaMedica = datos.get('notas', '').strip()
            receta.save()
            
            logger.info(f"Receta actualizada para paciente {receta.paciente.rut}")
            return True, "Receta médica actualizada correctamente."
            
        except ValidationError as e:
            logger.error(f"Error de validación al actualizar receta: {str(e)}")
            return False, "Error de validación en los datos de la receta."
        except Exception as e:
            logger.error(f"Error inesperado al actualizar receta: {str(e)}")
            return False, "Error al actualizar la receta médica."
    
    @staticmethod
    @transaction.atomic
    def eliminar_receta(receta: RecetaMedica) -> Tuple[bool, str]:
        """
        Elimina una receta
        Returns: (éxito, mensaje)
        """
        try:
            if not receta:
                return False, "No existe receta para eliminar."
            
            paciente_rut = receta.paciente.rut
            receta.delete()
            
            logger.info(f"Receta eliminada para paciente {paciente_rut}")
            return True, "Receta médica eliminada correctamente."
            
        except Exception as e:
            logger.error(f"Error al eliminar receta: {str(e)}")
            return False, "Error al eliminar la receta médica."


# ========== MANEJADORES DE ACCIONES ==========
class AccionRecetaHandler:
    """Manejador de acciones CRUD sobre recetas"""
    
    def __init__(self, receta_service: RecetaService):
        self.receta_service = receta_service
    
    def ejecutar(self, accion: str, paciente: Paciente, clinico: Clinico, 
                 receta: Optional[RecetaMedica], datos: Dict[str, str]) -> Dict[str, Any]:
        """
        Ejecuta la acción correspondiente
        Returns: dict con 'receta', 'mensaje', 'error'
        """
        resultado = {
            'receta': receta,
            'mensaje': None,
            'error': None
        }
        
        if accion == 'crear':
            exito, mensaje, nueva_receta = self.receta_service.crear_receta(paciente, clinico, datos)
            if exito:
                resultado['receta'] = nueva_receta
                resultado['mensaje'] = mensaje
            else:
                resultado['error'] = mensaje
                
        elif accion == 'editar':
            exito, mensaje = self.receta_service.actualizar_receta(receta, datos)
            if exito:
                resultado['mensaje'] = mensaje
            else:
                resultado['error'] = mensaje
                
        elif accion == 'eliminar':
            exito, mensaje = self.receta_service.eliminar_receta(receta)
            if exito:
                resultado['receta'] = None
                resultado['mensaje'] = mensaje
            else:
                resultado['error'] = mensaje
        
        return resultado


# ========== PROCESADORES DE REQUEST ==========
class RequestProcessor:
    """Procesador principal de requests"""
    
    def __init__(self):
        self.receta_service = RecetaService()
        self.accion_handler = AccionRecetaHandler(self.receta_service)
    
    def procesar_busqueda_paciente(self, rut: str, clinico: Clinico, es_admin: bool) -> Dict[str, Any]:
        """Procesa la búsqueda de un paciente"""
        resultado = {
            'paciente': None,
            'receta': None,
            'error': None
        }
        
        paciente = PacienteService.buscar_paciente_por_rut(rut)
        
        if not paciente:
            resultado['error'] = "No se encontró ningún paciente con ese RUT."
            return resultado
        
        if not AuthService.verificar_permiso_paciente(paciente, clinico, es_admin):
            resultado['error'] = "No tienes permisos para ver este paciente."
            return resultado
        
        resultado['paciente'] = paciente
        resultado['receta'] = self.receta_service.obtener_receta(paciente)
        
        return resultado
    
    def procesar_post(self, request, clinico: Clinico, es_admin: bool) -> Dict[str, Any]:
        """Procesa una petición POST"""
        rut = request.POST.get('rutsito', '').strip()
        accion = request.POST.get('accion', '').lower()
        
        # Buscar paciente
        busqueda = self.procesar_busqueda_paciente(rut, clinico, es_admin)
        if busqueda['error']:
            return busqueda
        
        paciente = busqueda['paciente']
        receta = busqueda['receta']
        
        # Ejecutar acción
        datos = {
            'medicamentos': request.POST.get('medicamentos', ''),
            'indicaciones': request.POST.get('indicaciones', ''),
            'notas': request.POST.get('notas', '')
        }
        
        resultado_accion = self.accion_handler.ejecutar(accion, paciente, clinico, receta, datos)
        
        return {
            'paciente': paciente,
            'receta': resultado_accion['receta'],
            'error': resultado_accion['error'],
            'mensaje': resultado_accion['mensaje'],
            'mostrar_formulario': False
        }
    
    def procesar_get(self, request, clinico: Clinico, es_admin: bool) -> Dict[str, Any]:
        """Procesa una petición GET"""
        rut = request.GET.get('rut', '').strip()
        accion = request.GET.get('accion', '').lower()
        
        if not rut:
            return {
                'paciente': None,
                'receta': None,
                'error': None,
                'mensaje': None,
                'mostrar_formulario': False
            }
        
        # Buscar paciente
        busqueda = self.procesar_busqueda_paciente(rut, clinico, es_admin)
        busqueda['mostrar_formulario'] = accion in ['nueva', 'editar']
        busqueda['mensaje'] = None
        
        return busqueda


# ========== VISTA PRINCIPAL ==========
def renderizar_html_receta(request):
    """Vista principal para gestionar recetas médicas"""
    try:
        # Verificar sesión
        sesion = AuthService.verificar_sesion(request)
        if not sesion:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('login')
        
        # Obtener clínico
        clinico = AuthService.obtener_clinico(sesion['rut_clinico'])
        if not clinico:
            messages.error(request, 'No se encontró el clínico en el sistema.')
            return redirect('login')
        
        # Procesar request
        processor = RequestProcessor()
        
        if request.method == 'POST':
            contexto = processor.procesar_post(request, clinico, sesion['es_admin'])
        else:  # GET
            contexto = processor.procesar_get(request, clinico, sesion['es_admin'])
        
        return render(request, 'agregar_receta.html', contexto)
        
    except Exception as e:
        logger.critical(f"Error crítico en renderizar_html_receta: {str(e)}", exc_info=True)
        messages.error(request, 'Ocurrió un error inesperado. Por favor, intenta nuevamente.')
        return redirect('login')