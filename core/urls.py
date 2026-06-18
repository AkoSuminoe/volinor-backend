from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from accounts.views import GoogleLogin
from core.views import send_email_view


def health(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/send-email/', send_email_view, name='send_email'),
]
