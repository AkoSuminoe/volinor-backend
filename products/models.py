from django.db import models
from django.utils.text import slugify

class Product(models.Model):
    title = models.CharField(max_length=255, verbose_name="Ürün Adı")
    slug = models.SlugField(unique=True, blank=True, verbose_name="URL İsmi (Slug)")
    description = models.TextField(verbose_name="Açıklama")
    image = models.ImageField(upload_to='products/images/', verbose_name="Resim")
    model_file = models.FileField(upload_to='products/models/', blank=True, null=True, verbose_name="3D Model Dosyası (.glb/.gltf)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ürün'
        verbose_name_plural = 'Ürünler'

    def __str__(self):
        return self.title
