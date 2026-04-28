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
from django.urls import path, include
from Login import views as l
from PanelDeControl import views as v # Importa la vista PanelDeControl desde el archivo views.py de la aplicación PanelDeControl.
from CrudClinico import views as vistaClinico # Importa las vistas de la aplicación CrudClinico.
from FormularioInicial import views as vistaClinicos
from informe import views as vistaInforme
from ListaDePacientes import views as lista
from TiposDeFormularios import views as tiposFormularios
from PerfilClinico import views as perfil
from menu import views as m
from RecetasMedicas import views as recetaViews  # Importar las vistas de la aplicación RecetasMedicas
urlpatterns = [
    path('adminlfhjghjghgfnfgnhgfnhngf/', admin.site.urls), # Asocia la URL /admin/ con la vista de administración de Django.
    path('', l.validarLogin,name='login'),  # Asocia la URL / con la vista Login.validarLogin.
    path('panel/', v.panel, name="panel"),  # Asocia la URL /panel/ con la vista PanelDeControl.),
    path('Ver/', vistaClinico.VerClinicos,name='ver'),
    path('panel/FormularioInicial/', vistaClinicos.FormularioInicial,name='formularioInicial'),
    path('Cerrar/',v.cerrar_sesion,name='cerrarSesion'),
    
    path('informe/',vistaInforme.RenderInforme,name='informe'),
    path('ficha-clinica/',vistaInforme.RenderFichaClinica,name='fichaClinica'),

    path('editar/', vistaClinico.EditarClinicos, name='editar'),
    path('eliminar_paciente/', lista.EliminarPaciente, name='eliminar'),

    path('menu/',m.sidebar,name='menu'),
    #vistas derivadas del panel
    path('panel/fichaPacientes/',v.VerInformePacientes,name='ficha'),
    path('panel/historialClinico/', v.HistorialClinico, name='historialClinico'),
    path('PerfilClinico/',perfil.RenderizarPerfil,name='perfilClinico'),
    path('AgregarClinico/', vistaClinico.AgregarClinico,name='agregar'),
    path('panel/ListaPacientes',lista.MostrarPacientes,name='pacientes'),
    path('panel/AgregarPaciente',lista.AgregarPacienteBasico,name='AgregarPacienteBasico'),
    
    # Incluir las URLs de PanelDeControl
    path('', include('PanelDeControl.urls')),
    
    # Incluir las URLs de SesionesKinesicas
    path('sesiones-kinesicas/', include('SesionesKinesicas.urls')),

    #renderizacion de cuestionarios
    path('CuestionarioGROC/',tiposFormularios.RenderizarGROC,name='GROK'),
    path('CuestionarioENA/', tiposFormularios.renderizar_CuestionarioENA, name='ENA'),
    path('CuestionarioPSFS/', tiposFormularios.gestionar_psfs, name='gestionar_psfs'),
    path('CuestionarioEQ_5D/',tiposFormularios.RenderizarEQ_5D,name='EQ_5D'),
    path('CuestionarioBartel/', tiposFormularios.renderizar_CuestionarioBarthel, name='bartel'),
    path("CuestionarioScrenning/",tiposFormularios.renderizar_cuestionarioScrening,name="Screnning"),
    path('RecetaMedica/',recetaViews.renderizar_html_receta,name='receta') ,  # Incluir las URLs de la aplicación RecetasMedicas

    # URLs para sistema de QR
    path('generar-qr-formulario/', vistaClinicos.generar_token_formulario, name='generar_qr'),
    path('descargar-qr/<uuid:token_id>/', vistaClinicos.descargar_qr, name='descargar_qr'),
    path('formulario-publico/<uuid:token_id>/', vistaClinicos.formulario_publico, name='formulario_publico'),
    path('desactivar-token/<uuid:token_id>/', vistaClinicos.desactivar_token, name='desactivar_token'),
    
]
