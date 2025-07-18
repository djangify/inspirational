from django import template

register = template.Library()

@register.filter
def intdiv(value, arg):
    """Integer division filter that returns value // arg"""
    try:
        return int(value) // int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
    