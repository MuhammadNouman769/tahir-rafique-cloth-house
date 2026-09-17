from .models import SiteSettings, PromoBanner


def site_settings(request):
    settings_obj = SiteSettings.load()
    announcement = PromoBanner.objects.filter(active=True).first()
    return {
        'site_settings': settings_obj,
        'announcement_banner': announcement,
    }
