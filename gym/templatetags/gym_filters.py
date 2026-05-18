from django import template

register = template.Library()


@register.filter
def sum_attr(queryset, attr):
    """Суммирует значения указанного атрибута в списке объектов"""
    try:
        return sum(item[attr] for item in queryset)
    except (KeyError, TypeError):
        return 0
