from django.contrib import admin

from .forms import ClinicoAdminForm
from .models import AuditoriaAcceso, Clinico, Paciente
from clinicas.models import MembresiaClinica
from clinicas.admin import _procesar_membresia_formset


class MembresiaClinicaInline(admin.TabularInline):
    model = MembresiaClinica
    fk_name = 'clinico'
    extra = 0
    max_num = 1
    autocomplete_fields = ('clinica',)
    fields = ('clinica', 'rol', 'activo')
    verbose_name = 'Centro asignado'
    verbose_name_plural = 'Centro asignado (gestionar aquí para cambiar de clínica)'


@admin.register(Clinico)
class ClinicoAdmin(admin.ModelAdmin):
    form = ClinicoAdminForm
    list_display = ('rut', 'nombre', 'apellido', 'profesion', 'correo', 'activo', 'EsAdmin', 'clinica_actual', 'tipo_centro')
    list_filter = ('activo', 'EsAdmin', 'ciudad', 'membresias__clinica__tipo')
    search_fields = ('rut', 'nombre', 'apellido', 'correo')
    inlines = [MembresiaClinicaInline]
    fieldsets = (
        ('Identificación', {
            'fields': ('rut', 'nombre', 'apellido'),
        }),
        ('Datos profesionales', {
            'fields': ('profesion', 'especialidad', 'numero_registro', 'centro_trabajo', 'ciudad', 'experiencia', 'descripcion'),
        }),
        ('Contacto', {
            'fields': ('correo', 'telefono'),
        }),
        ('Acceso al sistema', {
            'fields': ('nueva_contraseña', 'EsAdmin', 'activo'),
            'description': 'El RUT no se puede cambiar una vez creado el clínico (es la clave primaria del sistema).',
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('rut',)
        return ()

    @admin.display(description='Clínica activa')
    def clinica_actual(self, obj):
        membresia = obj.membresias.filter(activo=True).select_related('clinica').first()
        if not membresia:
            return '—'
        return membresia.clinica.nombre

    @admin.display(description='Tipo centro')
    def tipo_centro(self, obj):
        membresia = obj.membresias.filter(activo=True).select_related('clinica').first()
        if not membresia:
            return '—'
        return membresia.clinica.get_tipo_display()

    def save_formset(self, request, form, formset, change):
        if formset.model is not MembresiaClinica:
            super().save_formset(request, form, formset, change)
            return
        _procesar_membresia_formset(request, form, formset, destino='clinico')


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'apellido', 'clinica', 'clinico_creador', 'contacto')
    list_filter = ('clinica', 'genero', 'cobertura_de_salud')
    search_fields = ('rut', 'nombre', 'apellido', 'correo', 'contacto')
    autocomplete_fields = ('clinica', 'clinico', 'clinico_creador')
    list_editable = ('clinica',)


@admin.register(AuditoriaAcceso)
class AuditoriaAccesoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'accion', 'paciente', 'clinico', 'clinica', 'ip_address')
    list_filter = ('accion', 'clinica', 'fecha')
    search_fields = ('paciente__rut', 'clinico__rut', 'clinico__nombre')
    readonly_fields = ('fecha', 'paciente', 'clinico', 'clinica', 'accion', 'ip_address')
    date_hierarchy = 'fecha'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
