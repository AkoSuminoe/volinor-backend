import uuid

from django.db import models


class ModelLibrary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    download_file = models.FileField(upload_to='models/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '3D Model'
        verbose_name_plural = '3D Modeller'

    def __str__(self):
        return self.name


class ModelImage(models.Model):
    model = models.ForeignKey(ModelLibrary, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='model_gallery/')

    class Meta:
        verbose_name = 'Galeri Resmi'
        verbose_name_plural = 'Galeri Resimleri'


class Video(models.Model):
    id = models.CharField(max_length=255, primary_key=True, help_text="YouTube Video ID")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    thumbnail_url = models.URLField(max_length=500)
    published_at = models.DateTimeField()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Video'
        verbose_name_plural = 'Videolar'

    def __str__(self):
        return self.title


class Certificate(models.Model):
    name = models.CharField(max_length=255, verbose_name='Sertifika Adı')
    issued_by = models.CharField(max_length=255, verbose_name='Veren Kurum')
    issue_date = models.DateField(verbose_name='Veriliş Tarihi')
    document = models.FileField(upload_to='certificates/', verbose_name='Belge / Görsel')
    verification_link = models.URLField(blank=True, null=True, verbose_name='Doğrulama Linki')
    is_active = models.BooleanField(default=True, verbose_name='Sitede Görünür')

    class Meta:
        ordering = ['-issue_date']
        verbose_name = 'Sertifika'
        verbose_name_plural = 'Sertifikalar'

    def __str__(self):
        return self.name
