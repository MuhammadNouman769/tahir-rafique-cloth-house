import re
from django.db import models
from django.core.validators import MinValueValidator


class SiteSettings(models.Model):
    """Singleton model holding store-wide, admin-editable configuration."""
    store_name = models.CharField(max_length=150, default="Tahir Rafique Cloth House")
    tagline = models.CharField(max_length=200, default="Premium Fashion For Every Occasion")
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)

    whatsapp_number = models.CharField(
        max_length=20, default="032857948",
        help_text="Local Pakistani number, e.g. 032857948. Converted automatically for WhatsApp links."
    )
    support_phone = models.CharField(max_length=20, default="032857948")
    email = models.EmailField(default="info@tahirrafiqueclothhouse.com")
    address = models.CharField(max_length=255, default="Blue Area, Islamabad, Pakistan")

    facebook_url = models.URLField(blank=True, default="https://facebook.com")
    instagram_url = models.URLField(blank=True, default="https://instagram.com")
    tiktok_url = models.URLField(blank=True, default="https://tiktok.com")

    delivery_charges = models.DecimalField(max_digits=8, decimal_places=2, default=250,
                                            validators=[MinValueValidator(0)])
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5000,
                                                    validators=[MinValueValidator(0)])
    currency_symbol = models.CharField(max_length=10, default="Rs.")

    announcement_text = models.CharField(
        max_length=255, blank=True,
        default="Free Delivery on Orders Above Rs. 5,000"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.store_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_international(self):
        """Convert a local Pakistani number (03XXXXXXXXX) into international
        format for wa.me links, e.g. 032857948 -> 923285794 8 -> 9232857948."""
        digits = re.sub(r'\D', '', self.whatsapp_number or '')
        if digits.startswith('0'):
            digits = digits[1:]
        if not digits.startswith('92'):
            digits = '92' + digits
        return digits


class HeroSlide(models.Model):
    """Configurable homepage hero banners."""
    title = models.CharField(max_length=150, default="Discover Your Style")
    subtitle = models.CharField(max_length=250, default="Premium Fashion For Every Occasion")
    image = models.ImageField(upload_to='hero/')
    primary_button_text = models.CharField(max_length=50, default="Shop Men")
    primary_button_link = models.CharField(max_length=200, default="/products/men/")
    secondary_button_text = models.CharField(max_length=50, default="Shop Women", blank=True)
    secondary_button_link = models.CharField(max_length=200, default="/products/women/", blank=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class PromoBanner(models.Model):
    text = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_name} ({self.rating}★)"


class GalleryImage(models.Model):
    """Instagram-style visual gallery on homepage."""
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=150, blank=True)
    link = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.caption or f"Gallery Image {self.pk}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email
