from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from apps.core.utils import is_ajax
from .models import Product, Category, Size, Color, Review
from .filters import ProductFilter

PAGE_SIZE = 12
SORT_OPTIONS = {
    'newest': '-created_at',
    'price_low': 'price',
    'price_high': '-price',
    'popular': '-review_count',
    'discount': '-created_at',  # further refined in view
}


def _base_queryset():
    return Product.objects.filter(available=True).select_related('category', 'brand') \
        .prefetch_related('images', 'sizes', 'colors')


def _apply_sort(qs, sort_key):
    if sort_key == 'discount':
        return sorted(qs, key=lambda p: p.discount_percentage, reverse=True)
    return qs.order_by(SORT_OPTIONS.get(sort_key, '-created_at'))


def _paginate(request, qs):
    paginator = Paginator(qs, PAGE_SIZE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def _filter_context(request):
    return {
        'all_categories': Category.objects.filter(active=True, parent__isnull=True).prefetch_related('children'),
        'all_sizes': Size.objects.all(),
        'all_colors': Color.objects.all(),
        'selected_categories': request.GET.getlist('category'),
        'selected_sizes': request.GET.getlist('size'),
        'selected_colors': request.GET.getlist('color'),
        'min_price': request.GET.get('min_price', ''),
        'max_price': request.GET.get('max_price', ''),
        'availability': request.GET.get('availability', ''),
        'sort': request.GET.get('sort', 'newest'),
    }


def _render_listing(request, full_template, context):
    """Renders just the product-grid partial for AJAX filter/sort/page
    requests (so the page never reloads), or the full page otherwise."""
    if is_ajax(request):
        return render(request, 'products/_product_grid.html', context)
    return render(request, full_template, context)


def shop(request):
    qs = _base_queryset()
    f = ProductFilter(request.GET, queryset=qs)
    qs = f.qs
    sort_key = request.GET.get('sort', 'newest')
    qs = _apply_sort(qs, sort_key)
    page_obj = _paginate(request, qs)
    context = {
        'page_obj': page_obj,
        'total_count': len(qs) if isinstance(qs, list) else qs.count(),
        'page_title': 'All Products',
        **_filter_context(request),
    }
    return _render_listing(request, 'products/shop.html', context)


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, active=True)
    descendant_ids = [category.id] + list(category.children.values_list('id', flat=True))
    qs = _base_queryset().filter(category_id__in=descendant_ids)
    f = ProductFilter(request.GET, queryset=qs)
    qs = f.qs
    sort_key = request.GET.get('sort', 'newest')
    qs = _apply_sort(qs, sort_key)
    page_obj = _paginate(request, qs)
    context = {
        'page_obj': page_obj,
        'total_count': len(qs) if isinstance(qs, list) else qs.count(),
        'category': category,
        'page_title': category.name,
        **_filter_context(request),
    }
    return _render_listing(request, 'products/shop.html', context)


def deals(request):
    qs = _base_queryset().filter(deal_of_day=True) | _base_queryset().filter(sale_price__isnull=False)
    qs = qs.distinct()
    f = ProductFilter(request.GET, queryset=qs)
    qs = f.qs
    sort_key = request.GET.get('sort', 'discount')
    qs = _apply_sort(qs, sort_key)
    page_obj = _paginate(request, qs)
    context = {
        'page_obj': page_obj,
        'total_count': len(qs) if isinstance(qs, list) else qs.count(),
        'page_title': 'Deals & Sale',
        'is_deals_page': True,
        **_filter_context(request),
    }
    return _render_listing(request, 'products/shop.html', context)


def search(request):
    query = request.GET.get('q', '').strip()
    qs = _base_queryset()
    if query:
        qs = qs.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) |
            Q(description__icontains=query) | Q(category__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    else:
        qs = qs.none()
    sort_key = request.GET.get('sort', 'newest')
    qs = _apply_sort(qs, sort_key)
    page_obj = _paginate(request, qs)
    context = {
        'page_obj': page_obj,
        'total_count': len(qs) if isinstance(qs, list) else qs.count(),
        'query': query,
        'page_title': f'Search results for "{query}"' if query else 'Search',
        **_filter_context(request),
    }
    return _render_listing(request, 'products/search.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related(
            'images', 'sizes', 'colors', 'tags', 'reviews'),
        slug=slug)

    related = Product.objects.filter(category=product.category, available=True) \
        .exclude(pk=product.pk).select_related('category').prefetch_related('images')[:4]

    reviews = product.reviews.filter(approved=True)

    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = Product.objects.filter(pk__in=recently_viewed_ids).exclude(pk=product.pk) \
        .prefetch_related('images')[:4]

    recently_viewed_ids = [pid for pid in recently_viewed_ids if pid != product.pk]
    recently_viewed_ids.insert(0, product.pk)
    request.session['recently_viewed'] = recently_viewed_ids[:8]

    context = {
        'product': product,
        'related_products': related,
        'reviews': reviews,
        'recently_viewed': recently_viewed,
    }
    return render(request, 'products/detail.html', context)
