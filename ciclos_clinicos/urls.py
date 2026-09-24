from django.urls import path

from ciclos_clinicos import views

app_name = 'ciclos_clinicos'

urlpatterns = [
    path('iniciar/', views.iniciar_ciclo_view, name='iniciar'),
    path('finalizar/', views.finalizar_ciclo_view, name='finalizar'),
    path('abandonar/', views.abandonar_ciclo_view, name='abandonar'),
    path('paciente/', views.listar_ciclos_view, name='listar'),
    path('adjuntos/subir/', views.subir_adjunto_view, name='subir_adjunto'),
    path('adjuntos/eliminar/', views.eliminar_adjunto_view, name='eliminar_adjunto'),
]
