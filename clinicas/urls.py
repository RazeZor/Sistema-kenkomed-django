from django.urls import path

from . import views

urlpatterns = [
    path('mi-centro/', views.mi_centro, name='mi_centro'),
]
