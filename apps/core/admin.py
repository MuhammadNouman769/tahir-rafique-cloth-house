from django.contrib import admin
from .models import SiteSettings, HeroSlide, PromoBanner, Testimonial, GalleryImage, NewsletterSubscriber


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Store Identity', {'fields': ('store_name', 'tagline', 'logo', 'favicon')}),
        ('Contact & WhatsApp', {'fields': ('whatsapp_number', 'support_phone', 'email', 'address')}),
        ('Social Media', {'fields': ('facebook_url', 'instagram_url', 'tiktok_url')}),
        ('Delivery & Currency', {'fields': ('delivery_charges', 'free_delivery_threshold', 'currency_symbol')}),
        ('Announcement', {'fields': ('announcement_text',)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'active')
    list_editable = ('order', 'active')


@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'active')
    list_editable = ('order', 'active')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'city', 'active', 'created_at')
    list_editable = ('active',)
    list_filter = ('rating', 'active')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('caption', 'order', 'active')
    list_editable = ('order', 'active')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    readonly_fields = ('subscribed_at',)
