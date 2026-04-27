from django import template

register = template.Library()


@register.filter
def getitem(obj, key):
    """Permite acceder a dict/objeto con clave dinámica en templates."""
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return ''
