from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, PasswordResetSerializer
from rest_framework import serializers

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
    pass
