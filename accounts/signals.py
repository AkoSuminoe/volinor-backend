import logging
import threading

from allauth.account.signals import email_confirmed
from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@receiver(email_confirmed)
def notify_admin_on_email_confirmation(sender, request, email_address, **kwargs):
    user = email_address.user
    base = settings.BACKEND_URL

    approve_token = signing.dumps({"user_id": user.id, "action": "approve"}, salt="admin-manage-user")
    reject_token = signing.dumps({"user_id": user.id, "action": "reject"}, salt="admin-manage-user")

    context = {
        "user_email": user.email,
        "approve_url": f"{base}/api/auth/manage-user/{approve_token}/",
        "reject_url": f"{base}/api/auth/manage-user/{reject_token}/",
    }

    def _send():
        try:
            html_body = render_to_string("accounts/admin_notify.html", context)
            plain_body = (
                f"{user.email} e-postasını doğruladı.\n\n"
                f"Onayla: {context['approve_url']}\n"
                f"Reddet: {context['reject_url']}"
            )
            admin_emails = [email for _, email in settings.ADMINS]
            msg = EmailMultiAlternatives(
                subject=f"Aktivasyon onayı: {user.email}",
                body=plain_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=admin_emails,
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()
        except Exception as exc:
            logger.error("Admin notification failed: %s", exc)

    threading.Thread(target=_send, daemon=True).start()
