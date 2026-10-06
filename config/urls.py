from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.products.sitemaps import ProductSitemap, CategorySitemap
from django.views.generic import RedirectView, TemplateView

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('dashboard/', include('apps.dashboard.urls')),
    path('admin/', RedirectView.as_view(pattern_name='dashboard:overview', permanent=False)),
    path('', include('apps.pages.urls')),
    path('', include('apps.core.urls')),
    path('products/', include('apps.products.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('account/', include('apps.accounts.urls')),
    path('contact/', include('apps.contact.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
