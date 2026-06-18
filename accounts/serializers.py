from django.conf import settings
from dj_rest_auth.serializers import PasswordResetSerializer


class CustomPasswordResetSerializer(PasswordResetSerializer):

    def get_email_options(self):
        return {
            'extra_email_context': {
                'frontend_base_url': settings.FRONTEND_URL,
            },
        }
