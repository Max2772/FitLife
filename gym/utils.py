"""Вспомогательные функции для FitLife Gym."""
import calendar
import re
from datetime import date
from decimal import Decimal

from django.utils import timezone

from .models import Promocode


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


def get_valid_promocode_for_membership(code, membership_type):
    """
    Проверяет промокод для выбранного типа абонемента.

    Returns:
        (Promocode | None, str | None): промокод и текст ошибки.
        Пустой код — (None, None) без ошибки.
    """
    if code is None:
        return None, None
    code = str(code).strip()
    if not code:
        return None, None
    if membership_type is None:
        return None, 'Сначала выберите тип абонемента.'
    try:
        promo = Promocode.objects.get(
            code__iexact=code,
            is_active=True,
        )
    except Promocode.DoesNotExist:
        return None, 'Неверный или неактивный промокод.'
    if promo.membership_type_id and promo.membership_type_id != membership_type.pk:
        return None, 'Промокод не подходит к выбранному абонементу.'
    if promo.valid_until and promo.valid_until < date.today():
        return None, 'Промокод истёк.'
    return promo, None


MONTH_NAMES_RU = (
    '',
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
)


def build_text_calendar(year=None, month=None, *, highlight_day=None):
    """
    Текстовая сетка календаря на месяц (понедельник — первый день недели).
    Текущий день отмечается в квадратных скобках, например [20].
    """
    today = date.today()
    year = year or today.year
    month = month or today.month
    if highlight_day is None and today.year == year and today.month == month:
        highlight_day = today.day

    cal = calendar.Calendar(firstweekday=0)
    title = f"{MONTH_NAMES_RU[month]} {year}".center(28)
    header = "Пн  Вт  Ср  Чт  Пт  Сб  Вс"
    lines = [title, header]

    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append("    ")
            elif day == highlight_day:
                row.append(f"[{day:2d}]")
            else:
                row.append(f" {day:2d} ")
        lines.append("".join(row))

    return "\n".join(lines)


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


# --------------------------------------------------------------------------
# ЛР1: работа с корзиной заказа
# --------------------------------------------------------------------------

def get_cart(request, create=True):
    """
    Возвращает корзину текущего посетителя.

    Для авторизованного пользователя корзина привязана к User, для гостя —
    к ключу сессии. При входе в аккаунт гостевая корзина сливается с личной.
    """
    from .models import Cart  # локальный импорт: избегаем циклической зависимости

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart is None and create:
            cart = Cart.objects.create(user=request.user)
        return cart

    if not request.session.session_key:
        if not create:
            return None
        request.session.create()
    session_key = request.session.session_key
    cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
    if cart is None and create:
        cart = Cart.objects.create(session_key=session_key)
    return cart


def merge_session_cart(request, user):
    """Переносит позиции гостевой корзины в корзину пользователя после входа."""
    from .models import Cart, CartItem

    session_key = request.session.session_key
    if not session_key:
        return
    guest_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
    if guest_cart is None:
        return
    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in guest_cart.items.all():
        target, created = CartItem.objects.get_or_create(
            cart=user_cart, membership_type=item.membership_type,
            defaults={'quantity': item.quantity},
        )
        if not created:
            target.quantity = min(target.quantity + item.quantity, 99)
            target.save(update_fields=['quantity'])
    guest_cart.delete()


def generate_order_number():
    """Человекочитаемый номер заказа вида FL-20260912-A3F19C."""
    import uuid
    return f"FL-{date.today():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"


def get_valid_promocode(code):
    """Проверяет промокод без привязки к конкретному абонементу (для корзины)."""
    if not code:
        return None, None
    code = str(code).strip()
    if not code:
        return None, None
    promo = Promocode.objects.filter(code__iexact=code, is_active=True).first()
    if promo is None:
        return None, 'Неверный или неактивный промокод.'
    if promo.valid_until and promo.valid_until < date.today():
        return None, 'Срок действия промокода истёк.'
    return promo, None


def get_main_company():
    """
    Возвращает основную запись CompanyInfo (используется на страницах
    «О компании» и «Контакты»).

    load_test_data создаёт несколько тестовых "филиалов" с разными
    названиями для демонстрации выборок из прошлой лабы. Чтобы страница
    «О компании» не показывала случайный из них, ищем по конкретному имени;
    если не нашли — берём любую запись, лишь бы страница не была пустой.
    """
    from .models import CompanyInfo  # локальный импорт: избегаем циклической зависимости

    return CompanyInfo.objects.filter(name='FitLife Gym').first() or CompanyInfo.objects.first()
