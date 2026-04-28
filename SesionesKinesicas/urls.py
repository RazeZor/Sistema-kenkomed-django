from django.urls import path
from . import views

app_name = 'sesiones_kinesicas'

urlpatterns = [
    # Listar sesiones del paciente
    path('listar/', views.listar_sesiones_paciente, name='listar'),
    
    # Crear primera sesión
    path('crear-primera/', views.crear_primera_sesion, name='crear_primera'),
    
    # Crear sesión de seguimiento
    path('crear-seguimiento/', views.crear_sesion_seguimiento, name='crear_seguimiento'),
    
    # Crear sesión final (cierre de tratamiento)
    path('crear-final/', views.crear_sesion_final, name='crear_final'),
    
    # Ver una sesión específica
    path('ver/', views.ver_sesion_kinesica, name='ver'),
    
    # Editar sesión
    path('editar/', views.editar_sesion_kinesica, name='editar'),
    
    # API para combobox
    path('api/sesiones/', views.api_sesiones_paciente, name='api_sesiones'),
]
