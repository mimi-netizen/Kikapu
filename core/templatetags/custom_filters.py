from django import template
import random

register = template.Library()

@register.filter(name='random_percentage')
def random_percentage(value):
    """Returns a random percentage between 35 and 95"""
    return random.randint(35, 95)

@register.filter(name='subtract')
def subtract(value, arg):
    """Subtracts the arg from the value"""
    try:
        return value - arg
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return ''
