from django.urls import path
from . import views
from . import views_reservas

urlpatterns = [
    path('clear-session-message/', views.clear_session_message, name='clear_session_message'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    
    # Reservas / Calendario
    path('calendario/', views_reservas.calendario_view, name='calendario_reservas'),
    path('api/reservas/', views_reservas.api_obtener_reservas, name='api_obtener_reservas'),
    path('api/reservas/crear/', views_reservas.api_crear_reserva, name='api_crear_reserva'),
    path('api/reservas/mover/<int:reserva_id>/', views_reservas.api_mover_reserva, name='api_mover_reserva'),
    path('api/reservas/eliminar/<int:reserva_id>/', views_reservas.api_eliminar_reserva, name='api_eliminar_reserva'),
]
