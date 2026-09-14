"""Контекст для всех шаблонов."""
from django.conf import settings
from django.utils import timezone

from .utils import build_text_calendar


def site_calendar(request):
    """Текстовый календарь текущего месяца в часовом поясе проекта."""
    local_today = timezone.localdate()
    return {
        'text_calendar': build_text_calendar(local_today.year, local_today.month),
        'text_calendar_caption': (
            f"{local_today.strftime('%d/%m/%Y')} — "
            f"часовой пояс {settings.TIME_ZONE}"
        ),
    }


def cart_summary(request):
    """Счётчик корзины для шапки сайта (доступен во всех шаблонах)."""
    from .utils import get_cart

    try:
        cart = get_cart(request, create=False)
    except Exception:  # noqa: BLE001 — шапка не должна падать из-за корзины
        cart = None
    if cart is None:
        return {'cart_quantity': 0, 'cart_total': 0}
    return {
        'cart_quantity': cart.total_quantity,
        'cart_total': cart.total_price,
    }
