from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from accounts.views import AdminManageUserView, GoogleLogin, ModelDownloadView, ModelLibraryDetailView, ModelLibraryListView
from core.views import send_email_view


def health(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/manage-user/<str:token>/', AdminManageUserView.as_view(), name='admin_manage_user'),
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/send-email/', send_email_view, name='send_email'),
    path('api/models/', ModelLibraryListView.as_view(), name='model_list'),
    path('api/models/<uuid:model_id>/', ModelLibraryDetailView.as_view(), name='model_detail'),
    path('api/models/<uuid:model_id>/download/', ModelDownloadView.as_view(), name='model_download'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
