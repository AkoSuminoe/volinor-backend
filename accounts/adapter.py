import logging
import threading

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        def _send():
            try:
                super(CustomAccountAdapter, self).send_mail(template_prefix, email, context)
            except Exception as exc:
                logger.error("Email delivery failed | to=%s template=%s error=%s", email, template_prefix, exc)

        threading.Thread(target=_send, daemon=True).start()

    def get_email_confirmation_url(self, request, emailconfirmation):
        return f"{settings.FRONTEND_URL}/verify-email/{emailconfirmation.key}"

    def get_password_reset_url(self, request, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

    def respond_user_inactive(self, request, user):
        raise PermissionDenied("Account pending admin approval.")


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing and not sociallogin.user.is_active:
            raise PermissionDenied("Account pending admin approval.")

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.is_active = False
        user.save(update_fields=["is_active"])

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        base = settings.BACKEND_URL
        approve_url = f"{base}/api/auth/approval/{uid}/{token}/approve/"
        reject_url = f"{base}/api/auth/approval/{uid}/{token}/reject/"

        ctx = {"user": user, "approve_url": approve_url, "reject_url": reject_url}
        html = render_to_string("emails/admin_approval.html", ctx)

        def _send():
            try:
                for _, addr in settings.ADMINS:
                    msg = EmailMultiAlternatives(
                        subject="[Volinor] Google ile Yeni Kayıt — Onay Bekliyor",
                        body=approve_url,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[addr],
                    )
                    msg.attach_alternative(html, "text/html")
                    msg.send()
            except Exception as exc:
                logger.error("Social approval email failed | user=%s error=%s", user.email, exc)

        threading.Thread(target=_send, daemon=True).start()
        return user
