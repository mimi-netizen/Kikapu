from django import template

register = template.Library()

@register.filter
def filter_by_category(ads, category):
    """Filter ads by category"""
    return [ad for ad in ads if ad.category == category]

@register.filter
def split(value, delimiter=','):
    """Split a string into a list using the delimiter"""
    return value.split(delimiter)

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return None
