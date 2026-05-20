from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import UserSessionLog


def _close_open_session_logs(user, logout_time=None):
    """Закрывает незавершённые сессии пользователя корректным временем выхода."""
    logout_time = logout_time or timezone.now()
    for log in UserSessionLog.objects.filter(user=user, logout_time__isnull=True):
        end = logout_time
        if end < log.login_time:
            end = log.login_time
        log.logout_time = end
        log.save(update_fields=['logout_time'])


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key or ''
    _close_open_session_logs(user)
    UserSessionLog.objects.create(user=user, session_key=session_key)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        _close_open_session_logs(user)
