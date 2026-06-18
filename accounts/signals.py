import threading

from allauth.account.signals import email_confirmed
from django.core.mail import mail_admins
from django.dispatch import receiver


@receiver(email_confirmed)
def notify_admin_on_email_confirmation(sender, request, email_address, **kwargs):
    user = email_address.user
    threading.Thread(
        target=mail_admins,
        args=(
            f"Aktivasyon onayı: {user.email}",
            f"{user.email} adresini doğruladı. Admin panelinden aktifleştirin.\n\nhttp://localhost:8000/admin/auth/user/",
        ),
        kwargs={"fail_silently": True},
        daemon=True,
    ).start()
