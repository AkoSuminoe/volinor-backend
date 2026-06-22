import logging
import threading

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.http import FileResponse, Http404, HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Certificate, ModelLibrary, Video
from accounts.serializers import CertificateSerializer, ModelLibrarySerializer, VideoSerializer

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

            def _send():
                try:
                    html = render_to_string("emails/user_approved.html", {"user": user})
                    msg = EmailMultiAlternatives(
                        subject="Volinor - Hesabınız Onaylandı",
                        body=f"Hesabınız onaylandı. Giriş yapın: {settings.FRONTEND_URL}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    msg.attach_alternative(html, "text/html")
                    msg.send()
                except Exception as exc:
                    logger.error("Approval notification email failed | user=%s error=%s", user.email, exc)

            threading.Thread(target=_send, daemon=True).start()
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


class AdminQuickApprovalView(View):
    def get(self, request, uidb64, token, action):
        try:
            pk = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return self._page("⛔ Geçersiz Link", "Kullanıcı bulunamadı veya link bozuk.", "#dc2626")

        if not default_token_generator.check_token(user, token):
            return self._page("⏳ Link Geçersiz", "Bu bağlantı kullanılmış veya süresi dolmuş.", "#d97706")

        if action == "approve":
            user.is_active = True
            user.save(update_fields=["is_active"])
            EmailAddress.objects.update_or_create(
                user=user,
                email=user.email,
                defaults={"verified": True, "primary": True},
            )

            def _send():
                try:
                    html = render_to_string("emails/user_approved.html", {"user": user})
                    msg = EmailMultiAlternatives(
                        subject="Volinor - Hesabınız Onaylandı",
                        body=f"Hesabınız onaylandı. Giriş yapın: {settings.FRONTEND_URL}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    msg.attach_alternative(html, "text/html")
                    msg.send()
                except Exception as exc:
                    logger.error("Approval notification email failed | user=%s error=%s", user.email, exc)

            threading.Thread(target=_send, daemon=True).start()
            return self._page("✅ Onaylandı", f"{user.email} aktifleştirildi.", "#22c55e")

        if action == "reject":
            email = user.email
            user.delete()
            return self._page("🗑️ Reddedildi", f"{email} sistemden silindi.", "#ef4444")

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


class ModelLibraryListView(APIView):
    def get(self, request):
        qs = ModelLibrary.objects.prefetch_related('images').all()
        return Response(ModelLibrarySerializer(qs, many=True, context={'request': request}).data)


class ModelLibraryDetailView(APIView):
    def get(self, request, model_id):
        try:
            obj = ModelLibrary.objects.prefetch_related('images').get(pk=model_id)
        except ModelLibrary.DoesNotExist:
            raise Http404
        return Response(ModelLibrarySerializer(obj, context={'request': request}).data)


class ModelDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, model_id):
        try:
            obj = ModelLibrary.objects.get(pk=model_id)
        except ModelLibrary.DoesNotExist:
            raise Http404

        if obj.download_file and obj.download_file.storage.exists(obj.download_file.name):
            file_handle = obj.download_file.open('rb')
            filename = obj.download_file.name.split('/')[-1]
            response = FileResponse(file_handle, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        if obj.external_link:
            return Response({'type': 'external', 'url': obj.external_link})

        raise Http404


class VideoListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Video.objects.all()
        return Response(VideoSerializer(qs, many=True).data)


class CertificateListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Certificate.objects.filter(is_active=True)
        return Response(CertificateSerializer(qs, many=True, context={'request': request}).data)
