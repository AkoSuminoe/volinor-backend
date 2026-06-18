import logging

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model
from django.core import signing
from django.http import HttpResponse
from django.views import View
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)
User = get_user_model()


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:5173/auth/callback"
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(data=request.data)
        self.serializer.is_valid(raise_exception=True)
        user = self.serializer.validated_data.get("user")
        if not user.is_active:
            return Response(
                {"detail": "Account pending admin approval."},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.login()
        return self.get_response()


class AdminManageUserView(View):
    def get(self, request, token):
        try:
            data = signing.loads(token, max_age=86400, salt="admin-manage-user")
        except signing.SignatureExpired:
            return self._page("⏳ Link Süresi Doldu", "Bu bağlantının 24 saatlik geçerlilik süresi dolmuş.", "#d97706")
        except signing.BadSignature:
            return self._page("⛔ Geçersiz Link", "Bu bağlantı geçersiz veya değiştirilmiş.", "#dc2626")

        try:
            user = User.objects.get(pk=data["user_id"])
        except User.DoesNotExist:
            return self._page("👻 Kullanıcı Bulunamadı", "Bu kullanıcı zaten silinmiş olabilir.", "#6b7280")

        action = data.get("action")
        if action == "approve":
            user.is_active = True
            user.save(update_fields=["is_active"])
            EmailAddress.objects.update_or_create(
                user=user,
                email=user.email,
                defaults={"verified": True, "primary": True},
            )
            return self._page("✅ Onaylandı", f"{user.email} aktifleştirildi ve giriş yapabilir.", "#0ea5e9")
        elif action == "reject":
            email = user.email
            user.delete()
            return self._page("🗑️ Reddedildi", f"{email} sistemden silindi.", "#dc2626")

        return self._page("⚠️ Hata", "Geçersiz işlem.", "#dc2626")

    @staticmethod
    def _page(title, body, accent):
        emoji = title.split()[0]
        heading = " ".join(title.split()[1:])
        return HttpResponse(f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>{heading}</title></head>
<body style="margin:0;background:#07080d;font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;">
  <div style="text-align:center;padding:48px;background:#0d0f1a;border:1px solid #1c2136;border-top:3px solid {accent};border-radius:12px;max-width:440px;">
    <p style="margin:0 0 12px;font-size:32px;">{emoji}</p>
    <h2 style="margin:0 0 14px;color:#dde3f0;font-size:18px;font-weight:600;">{heading}</h2>
    <p style="margin:0;color:#6b7a9a;font-size:14px;line-height:1.7;">{body}</p>
  </div>
</body>
</html>""")
