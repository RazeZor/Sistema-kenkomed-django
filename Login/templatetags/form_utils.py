from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def rut_input(name="rut", id_attr="rut", placeholder="12.345.678-9", required=True, css_class=""):
    """
    Tag personalizado para renderizar un input de RUT con formato automático
    
    Uso: {% rut_input name="rut" id_attr="rut" placeholder="12.345.678-9" %}
    """
    required_attr = "required" if required else ""
    
    html = f"""
    <div class="relative">
        <input 
            type="text" 
            id="{id_attr}" 
            name="{name}" 
            maxlength="12" 
            class="rut-input block w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent {css_class}" 
            placeholder="{placeholder}" 
            pattern="[0-9]{{1,2}}\.[0-9]{{3}}\.[0-9]{{3}}-[0-9Kk]{{1}}" 
            title="Formato: 12.345.678-9 o 12.345.678-K" 
            {required_attr}
        >
        <div class="rut-error hidden text-red-600 text-sm mt-1"></div>
    </div>
    """
    
    return mark_safe(html)

@register.simple_tag
def password_input(name="password", id_attr="password", placeholder="••••••••", required=True, css_class=""):
    """
    Tag personalizado para renderizar un input de contraseña con toggle de visibilidad
    
    Uso: {% password_input name="password" id_attr="password" %}
    """
    required_attr = "required" if required else ""
    
    html = f"""
    <div class="relative">
        <input 
            type="password" 
            id="{id_attr}" 
            name="{name}" 
            class="block w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent {css_class}" 
            placeholder="{placeholder}" 
            {required_attr}
        >
        <button 
            type="button" 
            id="togglePassword_{id_attr}" 
            class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 focus:outline-none" 
            title="Mostrar/ocultar contraseña"
        >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
        </button>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            setupPasswordToggle('{id_attr}', 'togglePassword_{id_attr}');
        }});
    </script>
    """
    
    return mark_safe(html)

@register.filter
def format_rut(value):
    """
    Filtro para formatear un RUT
    
    Uso: {{ rut_value|format_rut }}
    """
    if not value:
        return ""
    
    # Limpiar el RUT
    clean_rut = ''.join(c for c in str(value) if c.isdigit() or c.upper() == 'K')
    
    if len(clean_rut) < 2:
        return clean_rut
    
    # Formatear
    cuerpo = clean_rut[:-1]
    dv = clean_rut[-1]
    
    # Agregar puntos cada 3 dígitos desde la derecha
    formatted_cuerpo = ""
    for i, digit in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            formatted_cuerpo = "." + formatted_cuerpo
        formatted_cuerpo = digit + formatted_cuerpo
    
    return f"{formatted_cuerpo}-{dv}"
