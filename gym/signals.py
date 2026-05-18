from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import UserSessionLog


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    session_key = request.session.session_key
    UserSessionLog.objects.create(user=user, session_key=session_key)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        session_key = request.session.session_key
        log = UserSessionLog.objects.filter(
            user=user,
            session_key=session_key,
            logout_time__isnull=True
        ).first()
        if log:
            log.logout_time = timezone.now()
            log.save()
