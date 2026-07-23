from django.urls import path

from ciclos_clinicos import views

app_name = 'ciclos_clinicos'

urlpatterns = [
    path('iniciar/', views.iniciar_ciclo_view, name='iniciar'),
    path('finalizar/', views.finalizar_ciclo_view, name='finalizar'),
    path('abandonar/', views.abandonar_ciclo_view, name='abandonar'),
    path('paciente/', views.listar_ciclos_view, name='listar'),
]
