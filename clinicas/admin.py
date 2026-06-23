from django.contrib import admin, messages

from Login.models import Paciente

from .models import Clinica, MembresiaClinica
from .services import ClinicaServiceError, convertir_a_centro, unir_clinico_a_centro


def _aplicar_membresia_desde_admin(request, clinico, clinica, rol='miembro'):
    """Une un clínico a una clínica migrando pacientes (uso interno del admin)."""
    resultado = unir_clinico_a_centro(
        clinico_rut=clinico.rut,
        clinica_destino_id=clinica.id,
        rol=rol or 'miembro',
    )
    if resultado['ya_estaba']:
        messages.info(
            request,
            f'{clinico.nombre} {clinico.apellido} ya pertenecía a "{clinica.nombre}".',
        )
    else:
        messages.success(
            request,
            f'{clinico.nombre} {clinico.apellido} unido a "{clinica.nombre}". '
            f'{resultado["pacientes_migrados"]} paciente(s) migrado(s).',
        )
    return resultado


def _procesar_membresia_formset(request, form, formset, destino='clinica'):
    """
    Procesa inlines de MembresiaClinica desde el admin.
    destino='clinica' → se edita una Clínica y se agregan clínicos.
    destino='clinico' → se edita un Clínico y se asigna centro.
    """
    parent = form.instance
    if not parent.pk:
        return

    formset.save(commit=False)

    for obj in getattr(formset, 'deleted_objects', []):
        obj.activo = False
        obj.save(update_fields=['activo'])

    for inline_form in formset.forms:
        if not inline_form.cleaned_data or inline_form.cleaned_data.get('DELETE'):
            continue
        if not inline_form.has_changed() and inline_form.instance.pk:
            continue

        activo = inline_form.cleaned_data.get('activo', True)
        rol = inline_form.cleaned_data.get('rol') or 'miembro'

        if destino == 'clinica':
            clinico = inline_form.cleaned_data.get('clinico')
            clinica = parent
        else:
            clinico = parent
            clinica = inline_form.cleaned_data.get('clinica')

        if not clinico or not clinica:
            continue

        if activo:
            try:
                _aplicar_membresia_desde_admin(request, clinico, clinica, rol=rol)
            except ClinicaServiceError as exc:
                messages.error(request, str(exc))
        else:
            MembresiaClinica.objects.filter(clinico=clinico, clinica=clinica).update(activo=False)


class MembresiaClinicaInline(admin.TabularInline):
    model = MembresiaClinica
    extra = 1
    autocomplete_fields = ('clinico',)
    fields = ('clinico', 'rol', 'activo')
    verbose_name = 'Profesional del centro'
    verbose_name_plural = 'Profesionales del centro'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('clinico')


@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'miembros_activos', 'pacientes_centro', 'max_clinicos', 'ciudad', 'activa')
    list_filter = ('tipo', 'activa', 'ciudad')
    search_fields = ('nombre', 'rut_empresa', 'ciudad', 'correo')
    list_editable = ('tipo', 'max_clinicos', 'activa')
    inlines = [MembresiaClinicaInline]
    fieldsets = (
        ('Datos del centro', {
            'fields': ('nombre', 'tipo', 'max_clinicos', 'activa'),
            'description': (
                'Para un centro con varios kinesiólogos: tipo «Clínica / Centro», '
                'max_clinicos ≥ cantidad de profesionales, y agregar cada uno en la tabla inferior.'
            ),
        }),
        ('Marca y comunicaciones', {
            'fields': ('logo',),
            'description': (
                'Logo usado en correos a pacientes e informes PDF. '
                'Formato PNG o JPG, recomendado fondo transparente. Si no se sube, se usa KenkoMed.'
            ),
        }),
        ('Contacto y ubicación', {
            'fields': ('rut_empresa', 'direccion', 'ciudad', 'telefono', 'correo'),
        }),
    )

    actions = ['convertir_en_centro_compartido']

    @admin.display(description='Miembros')
    def miembros_activos(self, obj):
        return obj.miembros.filter(activo=True).count()

    @admin.display(description='Pacientes')
    def pacientes_centro(self, obj):
        return Paciente.objects.filter(clinica_id=obj.id).count()

    @admin.action(description='Convertir en centro compartido (tipo clínica, cupo 10)')
    def convertir_en_centro_compartido(self, request, queryset):
        for clinica in queryset:
            convertir_a_centro(clinica, max_clinicos=max(clinica.max_clinicos, 10))
        self.message_user(request, f'{queryset.count()} centro(s) convertido(s) a compartido.', messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.tipo == 'clinica' and obj.max_clinicos < 2:
            obj.max_clinicos = 10
            obj.save(update_fields=['max_clinicos'])

    def save_formset(self, request, form, formset, change):
        if formset.model is not MembresiaClinica:
            super().save_formset(request, form, formset, change)
            return
        _procesar_membresia_formset(request, form, formset, destino='clinica')


@admin.register(MembresiaClinica)
class MembresiaClinicaAdmin(admin.ModelAdmin):
    list_display = ('clinico', 'clinica', 'rol', 'activo', 'fecha_ingreso')
    list_filter = ('rol', 'activo', 'clinica', 'clinica__tipo')
    search_fields = ('clinico__nombre', 'clinico__apellido', 'clinico__rut', 'clinica__nombre')
    autocomplete_fields = ('clinico', 'clinica')
    list_editable = ('activo', 'rol')
    actions = ['activar_y_migrar_pacientes']

    @admin.action(description='Activar membresía y migrar pacientes al centro')
    def activar_y_migrar_pacientes(self, request, queryset):
        ok = 0
        for membresia in queryset.select_related('clinico', 'clinica'):
            try:
                _aplicar_membresia_desde_admin(
                    request, membresia.clinico, membresia.clinica, rol=membresia.rol or 'miembro'
                )
                ok += 1
            except ClinicaServiceError as exc:
                messages.error(request, str(exc))
        if ok:
            messages.success(request, f'{ok} membresía(s) procesada(s).')

    def save_model(self, request, obj, form, change):
        if obj.activo:
            try:
                _aplicar_membresia_desde_admin(request, obj.clinico, obj.clinica, rol=obj.rol or 'miembro')
            except ClinicaServiceError as exc:
                messages.error(request, str(exc))
                return
        else:
            super().save_model(request, obj, form, change)
