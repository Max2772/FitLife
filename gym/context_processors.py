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
