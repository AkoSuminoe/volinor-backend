from allauth.account.models import EmailAddress
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html, mark_safe

User = get_user_model()

_CARD_CSS = (
    "width:100%;box-sizing:border-box;background:#1e1e2f;"
    "border-left:4px solid #00c4e8;border-radius:8px;"
    "padding:14px 20px;color:#8b97b8;font-size:13px;line-height:1.8;margin-bottom:8px;"
)
_CARD_TEXT = (
    "ℹ️ Volinor Kapı Kontrol Merkezi. "
    "Pasif kullanıcılar e-postalarını doğrulamış olup onayınızı beklemektedir. "
    "Active kutucuğunu işaretleyin veya ana tablodan toplu onay verin."
)


@admin.action(description="✓ Seçili Kullanıcıları VIP Onayla")
def approve_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    for user in queryset:
        EmailAddress.objects.update_or_create(
            user=user,
            email=user.email,
            defaults={"verified": True, "primary": True},
        )
    modeladmin.message_user(request, f"{updated} kullanıcı aktifleştirildi.", messages.SUCCESS)


@admin.action(description="✕ Seçili İstekleri Reddet ve Sil")
def reject_users(modeladmin, request, queryset):
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f"{count} kullanıcı silindi.", messages.WARNING)


admin.site.site_header = ""
admin.site.site_title = "Volinor"
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "status_badge", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "date_joined")
    ordering = ("-date_joined",)
    search_fields = ("email",)
    actions = [approve_users, reject_users]
    readonly_fields = ("info_card", "date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("info_card",)}),
        ("Kimlik Bilgileri", {"fields": ("email", "password")}),
        ("Kapı Durumu", {"fields": ("is_active",)}),
        ("Yönetim Yetkileri", {"fields": ("is_staff", "is_superuser")}),
        ("Denetim", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser"),
        }),
    )

    @admin.display(description="Durum", ordering="is_active")
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe(
                '<span class="badge bg-success" style="letter-spacing:.5px;font-size:11px;">VIP AKTİF</span>'
            )
        return mark_safe(
            '<span class="badge bg-warning text-dark" style="letter-spacing:.5px;font-size:11px;">ONAY BEKLİYOR</span>'
        )

    @admin.display(description="")
    def info_card(self, obj):
        return format_html('<div style="{}">{}</div>', _CARD_CSS, _CARD_TEXT)
