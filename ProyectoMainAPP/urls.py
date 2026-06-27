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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from Login import views as l
from PanelDeControl import views as v 
from PanelDeControl import views_pacientes as vp
from PanelDeControl import views_informe as vi
from PanelDeControl import views_privacidad as vpriv
from FormularioInicial import views as vistaClinicos
from TiposDeFormularios import views as tiposFormularios
from RecetasMedicas import views as recetaViews

urlpatterns = [
    path('administradordjangogeneral', admin.site.urls), 
    path('', l.validarLogin,name='login'),  
    path('panel/', v.panel, name="panel"),  
    path('panel/FormularioInicial/', vistaClinicos.FormularioInicial,name='formularioInicial'),
    path('Cerrar/',v.cerrar_sesion,name='cerrarSesion'),
    
    path('informe/', vi.RenderInforme, name='informe'),
    path('ficha-clinica/', vi.RenderFichaClinica, name='fichaClinica'),
    path('panel/exportar-ficha/', vpriv.exportar_ficha, name='exportar_ficha'),
    path('panel/auditoria-accesos/', vpriv.auditoria_accesos, name='auditoria_accesos'),
    path('panel/auditoria-accesos/exportar-pdf/', vpriv.exportar_auditoria_pdf, name='exportar_auditoria_pdf'),
    path('privacidad-paciente/', vistaClinicos.aviso_privacidad_paciente, name='privacidad_paciente'),

    path('eliminar_paciente/', vp.EliminarPaciente, name='eliminar'),

    path('menu/', v.sidebar, name='menu'),
    
    #vistas derivadas del panel
    path('panel/fichaPacientes/', v.VerInformePacientes, name='ficha'),
    path('panel/historialClinico/', v.HistorialClinico, name='historialClinico'),
    path('PerfilClinico/', RedirectView.as_view(pattern_name='perfilClinico', permanent=True)),
    path('panel/ListaPacientes', vp.MostrarPacientes, name='pacientes'),
    path('panel/AgregarPaciente', vp.AgregarPacienteBasico, name='AgregarPacienteBasico'),
    path('panel/EditarPaciente', vp.EditarPaciente, name='editar_paciente'),
    
    # Incluir las URLs de PanelDeControl
    path('', include('PanelDeControl.urls')),
    
    # Incluir las URLs de SesionesKinesicas
    path('sesiones-kinesicas/', include('SesionesKinesicas.urls')),

    #renderizacion de cuestionarios
    path('CuestionarioGROC/',tiposFormularios.RenderizarGROC,name='GROK'),
    path('CuestionarioENA/', tiposFormularios.renderizar_CuestionarioENA, name='ENA'),
    path('CuestionarioPSFS/', tiposFormularios.gestionar_psfs, name='gestionar_psfs'),
    path('CuestionarioEQ_5D/',tiposFormularios.RenderizarEQ_5D,name='EQ_5D'),
    path('CuestionarioBarthel/', tiposFormularios.renderizar_CuestionarioBarthel, name='bartel'),
    path("CuestionarioScrenning/",tiposFormularios.renderizar_cuestionarioScrening,name="Screnning"),
    path('CuestionarioOswestry/', tiposFormularios.renderizar_cuestionario_oswestry, name='oswestry'),
    path('CuestionarioLEFS/', tiposFormularios.renderizar_cuestionario_lefs, name='lefs'),
    path('CuestionarioQuickDASH/', tiposFormularios.renderizar_cuestionario_quickdash, name='quickdash'),
    path('CuestionarioWOMAC/', tiposFormularios.renderizar_cuestionario_womac, name='womac'),
    path('RecetaMedica/',recetaViews.renderizar_html_receta,name='receta') ,  

    # URLs para sistema de formularios remotos
    path('generar-qr-formulario/', vistaClinicos.generar_token_formulario, name='generar_qr'),
    path('descargar-qr/<uuid:token_id>/', vistaClinicos.descargar_qr, name='descargar_qr'),
    path('formulario-publico/<uuid:token_id>/', vistaClinicos.formulario_publico, name='formulario_publico'),
    path('desactivar-token/<uuid:token_id>/', vistaClinicos.desactivar_token, name='desactivar_token'),
    path('generar-formulario-remoto/', vistaClinicos.generar_token_desde_historial, name='generar_formulario_remoto'),
    
    # URLs de clinicos e clinicas
    path('clinicas/', include('clinicas.urls')),
    path('clinicos/', include('clinicos.urls')),
]

handler400 = 'ProyectoMainAPP.error_handlers.handler400'
handler403 = 'ProyectoMainAPP.error_handlers.handler403'
handler404 = 'ProyectoMainAPP.error_handlers.handler404'
handler500 = 'ProyectoMainAPP.error_handlers.handler500'

if settings.DEBUG:
    from ProyectoMainAPP.error_handlers import preview_error
    urlpatterns += [
        path('__preview__/error/<int:code>/', preview_error, name='preview_error'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
