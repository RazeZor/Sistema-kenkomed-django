from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    # Dashboard principal (secretaria + admin)
    path('', views.dashboard_pagos, name='dashboard'),

    # Detalle financiero de un paciente
    path('paciente/', views.detalle_pagos_paciente, name='detalle_paciente'),

    # Registrar pago individual
    path('registrar/', views.registrar_pago_view, name='registrar'),

    # Packs de atenciones
    path('pack/crear/', views.crear_pack_view, name='crear_pack'),
    path('pack/<int:pack_id>/', views.detalle_pack_view, name='detalle_pack'),

    # Anular / Editar / Eliminar pago
    path('anular/<int:pago_id>/', views.anular_pago_view, name='anular_pago'),
    path('editar/<int:pago_id>/', views.editar_pago_view, name='editar_pago'),
    path('eliminar/<int:pago_id>/', views.eliminar_pago_view, name='eliminar_pago'),

    # Acciones 1-clic
    path('pago-masivo/', views.pago_masivo_view, name='pago_masivo'),
    path('descontar-pack/<int:sesion_id>/', views.descontar_pack_rapido_view, name='descontar_pack_rapido'),

    # APIs JSON
    path('api/estado/<str:rut>/', views.api_estado_pago, name='api_estado'),
    path('api/resumen/', views.api_resumen_financiero, name='api_resumen'),
]
