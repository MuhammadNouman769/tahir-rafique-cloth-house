from django.shortcuts import render
from apps.products.models import Product, Category
from apps.core.models import HeroSlide, PromoBanner, Testimonial, GalleryImage
from apps.core.forms import NewsletterForm
from .models import AboutContent


def home(request):
    hero_slides = HeroSlide.objects.filter(active=True)
    top_categories = Category.objects.filter(active=True, parent__isnull=True)[:4]

    base = Product.objects.filter(available=True).prefetch_related('images')

    context = {
        'hero_slides': hero_slides,
        'top_categories': top_categories,
        'deal_products': base.filter(deal_of_day=True)[:8],
        'new_arrivals': base.filter(new_arrival=True)[:8],
        'bestsellers': base.filter(bestseller=True)[:8],
        'trending_products': base.filter(featured=True)[:8],
        'women_products': base.filter(category__parent__slug='women')[:4] or
                           base.filter(category__slug='women')[:4],
        'men_products': base.filter(category__parent__slug='men')[:4] or
                         base.filter(category__slug='men')[:4],
        'abaya_products': base.filter(category__parent__slug='abaya')[:4] or
                           base.filter(category__slug='abaya')[:4],
        'children_products': base.filter(category__parent__slug='children')[:4] or
                              base.filter(category__slug='children')[:4],
        'promo_banner': PromoBanner.objects.filter(active=True).first(),
        'testimonials': Testimonial.objects.filter(active=True)[:6],
        'gallery_images': GalleryImage.objects.filter(active=True)[:8],
        'newsletter_form': NewsletterForm(),
    }
    return render(request, 'home/home.html', context)


def about(request):
    content = AboutContent.load()
    return render(request, 'pages/about.html', {'content': content})
