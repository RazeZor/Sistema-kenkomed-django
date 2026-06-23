from django import forms

from .models import Clinico


class ClinicoAdminForm(forms.ModelForm):
    nueva_contraseña = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
        required=False,
        help_text='Al editar: déjala en blanco para no cambiarla.',
    )

    class Meta:
        model = Clinico
        exclude = ('contraseña',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rut'].help_text = (
            'Identificador único del clínico. No se puede modificar después de crear el registro.'
        )
        if not self.instance.pk:
            self.fields['nueva_contraseña'].required = True
            self.fields['nueva_contraseña'].help_text = 'Contraseña de acceso al sistema.'

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk and not cleaned.get('nueva_contraseña'):
            self.add_error('nueva_contraseña', 'La contraseña es obligatoria al crear un clínico.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        nueva = self.cleaned_data.get('nueva_contraseña')
        if nueva:
            instance.set_password(nueva)
        if commit:
            instance.save()
        return instance
