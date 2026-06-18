import logging
import threading

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, PasswordResetConfirmSerializer, PasswordResetSerializer
from rest_framework import serializers

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password) and not user.is_active:
                    raise serializers.ValidationError(
                        {'non_field_errors': ['Hesabınız yönetici onayı beklemektedir.']}
                    )
            except User.DoesNotExist:
                pass
        return super().validate(attrs)


class EmailOnlyRegisterSerializer(RegisterSerializer):
    username = None

    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
        }


class CustomPasswordResetSerializer(PasswordResetSerializer):
    def validate_email(self, value):
        return value

    def save(self):
        request = self.context.get('request')
        email = self.validated_data['email']

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        ctx = {'password_reset_url': reset_url, 'user': user, 'request': request}
        subject = render_to_string('registration/password_reset_subject.txt', ctx).strip()
        html_body = render_to_string('registration/password_reset_email.html', ctx)

        def _send():
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=reset_url,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                msg.attach_alternative(html_body, 'text/html')
                msg.send()
            except Exception as exc:
                logger.error("Password reset email failed | to=%s error=%s", email, exc)

        threading.Thread(target=_send, daemon=True).start()


class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'uid': ['Geçersiz veya süresi dolmuş bağlantı.']})

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError(
                {'token': ['Bu şifre sıfırlama bağlantısı geçersiz veya süresi dolmuş.']}
            )

        self.set_password_form = SetPasswordForm(user=self.user, data=attrs)
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        self.set_password_form.save()
