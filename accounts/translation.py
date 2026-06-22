from modeltranslation.translator import register, TranslationOptions

from accounts.models import Certificate


@register(Certificate)
class CertificateTranslationOptions(TranslationOptions):
    fields = ('name', 'issued_by')
