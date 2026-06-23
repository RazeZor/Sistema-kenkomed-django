from django.urls import path
from . import views

urlpatterns = [
    path('perfil/', views.RenderizarPerfil, name='perfilClinico'),
]
