"""Вспомогательные функции для FitLife Gym."""
import re
from datetime import date
from decimal import Decimal

from django.utils import timezone


VALID_OPERATOR_CODES = ('29', '33', '44', '25')


def calculate_age(birth_date):
    """Возраст в полных годах."""
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def validate_minimum_age(birth_date, minimum=18):
    if calculate_age(birth_date) < minimum:
        raise ValueError(f"Возраст должен быть не менее {minimum} лет.")


def format_belarus_phone(phone):
    """Нормализует телефон к формату +375 (29) XXX-XX-XX."""
    cleaned = re.sub(r'\D', '', phone or '')
    if len(cleaned) == 9:
        cleaned = '375' + cleaned
    if len(cleaned) != 12 or not cleaned.startswith('375'):
        raise ValueError(
            "Введите номер в формате +375 (29) XXX-XX-XX. "
            "Допустимые коды: 29, 33, 44, 25."
        )
    operator = cleaned[3:5]
    if operator not in VALID_OPERATOR_CODES:
        raise ValueError(
            "Введите номер в формате +375 (29) XXX-XX-XX. "
            "Допустимые коды: 29, 33, 44, 25."
        )
    number = cleaned[5:]
    if len(number) != 7:
        raise ValueError(
            "Введите номер в формате +375 (29) XXX-XX-XX. "
            "Допустимые коды: 29, 33, 44, 25."
        )
    return f"+375 ({operator}) {number[:3]}-{number[3:5]}-{number[5:7]}"


def apply_promocode_discount(base_price, promocode):
    """Рассчитывает цену со скидкой по промокоду."""
    if not promocode:
        return Decimal(base_price)
    discount = Decimal(promocode.discount_percent) / Decimal('100')
    return (Decimal(base_price) * (Decimal('1') - discount)).quantize(Decimal('0.01'))


def dual_datetime_display(dt):
    """Строка даты/времени: локальная TZ проекта и UTC (DD/MM/YYYY)."""
    if not dt:
        return ''
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    local = timezone.localtime(dt)
    from datetime import timezone as dt_timezone
    utc = dt.astimezone(dt_timezone.utc)
    return (
        f"{local.strftime('%d/%m/%Y %H:%M')} "
        f"(UTC: {utc.strftime('%d/%m/%Y %H:%M')})"
    )
