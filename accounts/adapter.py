import threading

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.mail import mail_admins
from rest_framework.exceptions import PermissionDenied


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        # Block re-entry for existing users still awaiting activation.
        if sociallogin.is_existing and not sociallogin.user.is_active:
            raise PermissionDenied("Account pending admin approval.")

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.is_active = False
        user.save(update_fields=["is_active"])
        threading.Thread(
            target=mail_admins,
            args=(
                "New user pending approval",
                f"User {user.email} has registered and is awaiting activation.",
            ),
            kwargs={"fail_silently": True},
            daemon=True,
        ).start()
        return user
