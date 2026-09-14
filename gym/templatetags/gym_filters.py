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


@register.filter
def html_datetime(value):
    """
    Значение для атрибута datetime тега <time> в формате HTML.

    Django-фильтр `date:"c"` печатает микросекунды, а спецификация HTML
    допускает не более трёх знаков в долях секунды — валидатор W3C считает
    это ошибкой. Фильтр отдаёт корректный ISO 8601: 2026-09-12T22:57:12+03:00.
    """
    if not value:
        return ''
    try:
        return value.replace(microsecond=0).isoformat()
    except (AttributeError, TypeError, ValueError):
        return str(value)


@register.filter
def tel_href(value):
    """
    Телефон в виде, пригодном для схемы tel:.

    В URI недопустимы пробелы и скобки, поэтому +375 (29) 123-45-67
    превращается в +375291234567.
    """
    if not value:
        return ''
    text = str(value)
    plus = '+' if text.strip().startswith('+') else ''
    digits = ''.join(ch for ch in text if ch.isdigit())
    return f"{plus}{digits}"
