from django import template

from gym.utils import dual_datetime_display

register = template.Library()


@register.filter
def sum_attr(queryset, attr):
    """Суммирует значения указанного атрибута в списке объектов."""
    try:
        return sum(item[attr] for item in queryset)
    except (KeyError, TypeError):
        return 0


@register.filter
def dual_datetime(value):
    """Дата в локальной TZ и UTC (DD/MM/YYYY)."""
    return dual_datetime_display(value)


@register.filter
def client_display_name(client):
    if not client:
        return ''
    parts = [client.last_name, client.first_name]
    if client.patronymic:
        parts.append(client.patronymic)
    return ' '.join(parts)
