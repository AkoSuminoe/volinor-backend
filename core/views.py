from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

@api_view(['POST'])
@permission_classes([AllowAny])
def send_email_view(request):
    data = request.data
    name = data.get('name', '')
    email = data.get('email', '')
    message = data.get('message', '')
    subject = data.get('subject', '')

    if not name or not email or not message:
        return Response({'error': 'Eksik bilgi: İsim, e-posta ve mesaj alanları zorunludur.'}, status=status.HTTP_400_BAD_REQUEST)

    final_subject = subject if subject else f'Web Sitesinden Yeni Mesaj: {name}'
    
    html_message = f"""
    <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
      <h3 style="color: #333;">Yeni İletişim Formu Mesajı</h3>
      <p><strong>Gönderen:</strong> {name}</p>
      <p><strong>E-posta:</strong> <a href="mailto:{email}">{email}</a></p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 15px 0;" />
      <p><strong>Mesaj:</strong></p>
      <p style="white-space: pre-wrap; color: #555;">{message}</p>
    </div>
    """
    
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=final_subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.SERVER_EMAIL], # admin'e gönderilir
            html_message=html_message,
            fail_silently=False,
        )
        return Response({'message': 'E-posta başarıyla gönderildi!'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'E-posta gönderilirken bir hata oluştu.', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
