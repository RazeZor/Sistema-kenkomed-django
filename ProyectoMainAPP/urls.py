"""
URL configuration for ProyectoMainAPP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Login import views as l
from PanelDeControl import views as v # Importa la vista PanelDeControl desde el archivo views.py de la aplicación PanelDeControl.
from CrudClinico import views as vistaClinico # Importa las vistas de la aplicación CrudClinico.
from FormularioInicial import views as vistaClinicos
from informe import views as vistaInforme
from ListaDePacientes import views as lista
from TiposDeFormularios import views as tiposFormularios
from PerfilClinico import views as perfil
from Servicios import views as s
from menu import views as m
urlpatterns = [
    path('admin/', admin.site.urls), # Asocia la URL /admin/ con la vista de administración de Django.
    path('',s.VerServicios),
    path('login/', l.validarLogin,name='login'),  # Asocia la URL / con la vista Login.validarLogin.
    path('panel/', v.panel, name="panel"),  # Asocia la URL /panel/ con la vista PanelDeControl.),
    path('AgregarClinico/', vistaClinico.AgregarClinico,name='agregar'),
    path('Ver/', vistaClinico.VerClinicos,name='ver'),
    path('panel/FormularioInicial/', vistaClinicos.FormularioInicial,name='formularioInicial'),
    path('Cerrar/',v.cerrar_sesion,name='cerrarSesion'),
    path('cuerpoHumano/',vistaClinicos.CuerpoHumano),
    path('panel/fichaPacientes/',v.VerInformePacientes,name='ficha'),
    path('panel/historialClinico/', v.HistorialClinico, name='historialClinico'),
    path('informe/',vistaInforme.RenderInforme,name='informe'),
    path('panel/ListaPacientes',lista.MostrarPacientes,name='pacientes'),
    path('editar/', vistaClinico.EditarClinicos, name='editar'),
    path('eliminar_paciente/', lista.EliminarPaciente, name='eliminar'),
    path('CuestionarioGROC/',tiposFormularios.RenderizarGROC,name='GROK'),
    path('CuestionarioPSFS/',tiposFormularios.gestionar_psfs, name='gestionar_psfs'),
    path('CuestionarioEQ_5D/',tiposFormularios.RenderizarEQ_5D,name='EQ_5D'),
    path('PerfilClinico/',perfil.RenderizarPerfil,name='perfilClinico'),
    path('menu/',m.sidebar,name='menu'),
    path('CuestionarioBartel/', tiposFormularios.renderizar_CuestionarioBarthel, name='bartel'),
    path('CuestionarioENA/', tiposFormularios.renderizar_CuestionarioENA, name='ENA'),
    


    
    
    
]
