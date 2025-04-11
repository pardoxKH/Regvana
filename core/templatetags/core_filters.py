from django import template

register = template.Library()

@register.filter
def divisibleby(value, arg):
    """
    Returns the percentage of value divided by arg.
    """
    if not arg:
        return 0
    return (value / arg) * 100

@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the argument.
    """
    return value * arg

@register.filter
def split(value, arg):
    """Split a string by the given argument."""
    return value.split(arg) 