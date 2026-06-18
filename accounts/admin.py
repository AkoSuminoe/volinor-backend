from allauth.account.models import EmailAddress
from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.utils.html import format_html, mark_safe

from accounts.models import ModelImage, ModelLibrary, Video

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


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        forms.Widget.__init__(self, attrs)
        self.attrs.setdefault('multiple', True)

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)

    def value_omitted_from_data(self, _data, _files, _name):
        return False


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if isinstance(data, list):
            return [super().clean(f, initial) for f in data if f]
        return []


class ModelLibraryAdminForm(forms.ModelForm):
    multiple_images = MultipleFileField(required=False)

    class Meta:
        model = ModelLibrary
        fields = '__all__'


class ModelImageInline(admin.TabularInline):
    model = ModelImage
    extra = 1
    fields = ('image',)


@admin.register(ModelLibrary)
class ModelLibraryAdmin(admin.ModelAdmin):
    form = ModelLibraryAdminForm
    list_display = ('name', 'thumbnail', 'secure_download_link', 'created_at')
    readonly_fields = ('created_at',)
    inlines = [ModelImageInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for image_file in request.FILES.getlist('multiple_images'):
            ModelImage.objects.create(model=obj, image=image_file)

    @admin.display(description='Önizleme')
    def thumbnail(self, obj):
        first = obj.images.first()
        if first and first.image:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;">', first.image.url)
        return '—'

    @admin.display(description='İndir')
    def secure_download_link(self, obj):
        return format_html(
            '<a href="/api/models/{}/download/" target="_blank">⬇ İndir</a>', obj.pk
        )


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    change_list_template = "admin/accounts/video/change_list.html"
    list_display = ('title', 'id', 'published_at', 'thumbnail_preview')
    search_fields = ('title', 'id')
    ordering = ('-published_at',)
    readonly_fields = ('thumbnail_preview',)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('fetch-videos/', self.admin_site.admin_view(self.fetch_videos_view), name='fetch_youtube_videos'),
        ]
        return custom_urls + urls

    def fetch_videos_view(self, request):
        from django.core.management import call_command
        from django.contrib import messages
        try:
            call_command('fetch_youtube_videos')
            self.message_user(request, "YouTube videoları başarıyla kontrol edildi ve veritabanı güncellendi.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"YouTube videoları çekilirken hata oluştu: {str(e)}", messages.ERROR)
        
        return HttpResponseRedirect("../")

    @admin.display(description='Önizleme')
    def thumbnail_preview(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;">', obj.thumbnail_url)
        return '—'
