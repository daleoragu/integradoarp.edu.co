# notas/templatetags/auth_extras.py
from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo específico.
    Uso en la plantilla: {% if user|has_group:"NombreDelGrupo" %}
    """
    return user.groups.filter(name=group_name).exists()
