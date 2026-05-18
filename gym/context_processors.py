import calendar
from datetime import timezone as dt_timezone

from django.utils import timezone


def site_datetime_context(request):
    """Контекст: текущая дата, календарь текстом, часовой пояс сервера."""
    now = timezone.localtime(timezone.now())
    now_utc = timezone.now().astimezone(dt_timezone.utc)
    text_calendar = calendar.TextCalendar(firstweekday=0).formatmonth(now.year, now.month)
    return {
        'server_now_local': now,
        'server_now_utc': now_utc,
        'server_timezone': str(timezone.get_current_timezone()),
        'text_calendar': text_calendar,
        'current_date_ddmmyyyy': now.strftime('%d/%m/%Y'),
    }
