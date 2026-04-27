from django import template

register = template.Library()


@register.filter
def getitem(obj, key):
    """Permite acceder a dict/objeto con clave dinámica en templates."""
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return ''


@register.filter
def zip_lists(a, b):
    """Combina dos listas en pares. Uso: list1|zip_lists:list2"""
    try:
        return zip(a, b)
    except TypeError:
        return []


@register.filter
def percentage(value, total):
    """Calcula porcentaje. Uso: value|percentage:total"""
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ZeroDivisionError, TypeError, ValueError):
        return 0
