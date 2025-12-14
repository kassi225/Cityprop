from django import template

register = template.Library()

@register.filter
def attr(obj, field_name):
    """Permet d'accéder dynamiquement à un champ d'un objet dans le template."""
    return getattr(obj, field_name, '')