from django.urls import path
from . import views

urlpatterns = [
    path('clear-session-message/', views.clear_session_message, name='clear_session_message'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]
