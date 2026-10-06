from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.models import GalleryImage, HeroSlide, PromoBanner, Testimonial
from apps.products.models import Brand, Category, Product, Review, Tag

from .decorators import staff_required
from .forms import (BrandForm, CategoryForm, GalleryImageForm, HeroSlideForm, ProductForm,
                    ProductImageFormSet, PromoBannerForm, TagForm, TestimonialForm)
from .helpers import paginate, recalc_product_rating


# ───────────────────────── Products ─────────────────────────
@staff_required
def products_list(request):
    qs = Product.objects.select_related('category', 'category__parent').prefetch_related('images')
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '')
    stock = request.GET.get('stock', '')
    flag = request.GET.get('flag', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if cat:
        qs = qs.filter(Q(category_id=cat) | Q(category__parent_id=cat))
    if stock == 'low':
        qs = qs.filter(stock_quantity__gt=0, stock_quantity__lte=5)
    elif stock == 'out':
        qs = qs.filter(stock_quantity=0)
    elif stock == 'in':
        qs = qs.filter(stock_quantity__gt=0)
    elif stock == 'hidden':
        qs = qs.filter(available=False)
    if flag in ('featured', 'bestseller', 'new_arrival', 'deal_of_day'):
        qs = qs.filter(**{flag: True})
    sort = request.GET.get('sort', '-created_at')
    if sort not in ('name', '-name', 'price', '-price', 'stock_quantity', '-stock_quantity', '-created_at', '-review_count'):
        sort = '-created_at'
    qs = qs.order_by(sort)
    ctx = {
        'products': paginate(request, qs, 15), 'q': q, 'cat': cat, 'stock': stock, 'flag': flag, 'sort': sort,
        'categories': Category.objects.filter(parent__isnull=True).order_by('order'),
        'stats': {
            'total': Product.objects.count(),
            'live': Product.objects.filter(available=True, stock_quantity__gt=0).count(),
            'low': Product.objects.filter(stock_quantity__gt=0, stock_quantity__lte=5).count(),
            'out': Product.objects.filter(stock_quantity=0).count(),
        },
        'result_count': qs.count(), 'page': 'products',
    }
    return render(request, 'dashboard/products_list.html', ctx)


@staff_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.instance = product
            formset.save()
            imgs = product.images.all()
            if imgs and not imgs.filter(is_primary=True).exists():
                first = imgs.first()
                first.is_primary = True
                first.save(update_fields=['is_primary'])
            messages.success(request, f'Product "{product.name}" saved.')
            return redirect('dashboard:products')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)
    return render(request, 'dashboard/product_form.html',
                  {'form': form, 'formset': formset, 'product': product, 'page': 'products'})


@staff_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()   # order history keeps its own name/price snapshot (FK is SET_NULL)
    messages.success(request, f'"{name}" deleted.')
    return redirect('dashboard:products')


@staff_required
@require_POST
def product_quick_update(request, pk):
    """Inline edit from the product table: stock / price / on-off flags."""
    p = get_object_or_404(Product, pk=pk)
    changed = []
    if 'stock_quantity' in request.POST:
        try:
            p.stock_quantity = max(0, int(request.POST['stock_quantity']))
            changed.append('stock_quantity')
        except ValueError:
            pass
    for flag in ('available', 'featured', 'bestseller', 'new_arrival', 'deal_of_day'):
        if f'toggle_{flag}' in request.POST:
            setattr(p, flag, not getattr(p, flag))
            changed.append(flag)
    if changed:
        p.save(update_fields=changed)
        messages.success(request, f'{p.name} updated.')
    return redirect(request.POST.get('next') or 'dashboard:products')


@staff_required
@require_POST
def products_bulk(request):
    ids = request.POST.getlist('ids')
    action = request.POST.get('action')
    qs = Product.objects.filter(pk__in=ids)
    if not ids:
        messages.warning(request, 'Select at least one product.')
    elif action == 'delete':
        n = qs.count(); qs.delete(); messages.success(request, f'{n} product(s) deleted.')
    elif action in ('show', 'hide'):
        qs.update(available=(action == 'show')); messages.success(request, f'{len(ids)} product(s) updated.')
    elif action in ('feature', 'unfeature'):
        qs.update(featured=(action == 'feature')); messages.success(request, f'{len(ids)} product(s) updated.')
    return redirect(request.POST.get('next') or 'dashboard:products')


# ───────────────────────── Reviews ─────────────────────────
@staff_required
def reviews_list(request):
    qs = Review.objects.select_related('product')
    status, rating, q = request.GET.get('status', ''), request.GET.get('rating', ''), request.GET.get('q', '').strip()
    if status == 'pending':
        qs = qs.filter(approved=False)
    elif status == 'approved':
        qs = qs.filter(approved=True)
    if rating.isdigit():
        qs = qs.filter(rating=int(rating))
    if q:
        qs = qs.filter(Q(customer_name__icontains=q) | Q(comment__icontains=q) | Q(product__name__icontains=q))
    from . import analytics as an
    ctx = {
        'reviews': paginate(request, qs, 12), 'status': status, 'rating': rating, 'q': q,
        'dist': an.rating_distribution(),
        'total': Review.objects.count(),
        'pending': Review.objects.filter(approved=False).count(),
        'result_count': qs.count(), 'page': 'reviews',
    }
    from django.db.models import Avg
    ctx['avg'] = round(Review.objects.filter(approved=True).aggregate(a=Avg('rating'))['a'] or 0, 2)
    return render(request, 'dashboard/reviews_list.html', ctx)


@staff_required
@require_POST
def reviews_action(request):
    ids = request.POST.getlist('ids') or ([request.POST['id']] if request.POST.get('id') else [])
    action = request.POST.get('action')
    qs = Review.objects.filter(pk__in=ids)
    product_ids = set(qs.values_list('product_id', flat=True))
    if not ids:
        messages.warning(request, 'Select at least one review.')
    elif action in ('approve', 'unapprove'):
        qs.update(approved=(action == 'approve'))
        messages.success(request, f'{len(ids)} review(s) {"approved" if action == "approve" else "hidden"}.')
    elif action == 'delete':
        qs.delete()
        messages.success(request, f'{len(ids)} review(s) deleted.')
    for p in Product.objects.filter(pk__in=product_ids):
        recalc_product_rating(p)
    return redirect(request.POST.get('next') or 'dashboard:reviews')


# ───────────────────────── Generic CRUD (categories, banners, ...) ─────────────────────────
CRUD = {
    'categories': dict(model=Category, form=CategoryForm, title='Categories', singular='Category', icon='tag',
                       columns=[('Image', 'image', 'image'), ('Name', '__str__', 'text'), ('Order', 'order', 'text'),
                                ('Active', 'active', 'bool')], order=['parent_id', 'order', 'name']),
    'brands': dict(model=Brand, form=BrandForm, title='Brands', singular='Brand',
                   columns=[('Name', 'name', 'text')], order=['name']),
    'tags': dict(model=Tag, form=TagForm, title='Tags', singular='Tag',
                 columns=[('Name', 'name', 'text')], order=['name']),
    'hero': dict(model=HeroSlide, form=HeroSlideForm, title='Hero Slides', singular='Hero slide',
                 columns=[('Image', 'image', 'image'), ('Title', 'title', 'text'), ('Subtitle', 'subtitle', 'text'),
                          ('Order', 'order', 'text'), ('Active', 'active', 'bool')], order=['order']),
    'banners': dict(model=PromoBanner, form=PromoBannerForm, title='Announcement Banners', singular='Banner',
                    columns=[('Text', 'text', 'text'), ('Order', 'order', 'text'), ('Active', 'active', 'bool')],
                    order=['order']),
    'testimonials': dict(model=Testimonial, form=TestimonialForm, title='Testimonials', singular='Testimonial',
                         columns=[('Customer', 'customer_name', 'text'), ('City', 'city', 'text'),
                                  ('Rating', 'rating', 'rating'), ('Comment', 'comment', 'text'),
                                  ('Active', 'active', 'bool')], order=['-created_at']),
    'gallery': dict(model=GalleryImage, form=GalleryImageForm, title='Gallery', singular='Gallery image',
                    columns=[('Image', 'image', 'image'), ('Caption', 'caption', 'text'), ('Order', 'order', 'text'),
                             ('Active', 'active', 'bool')], order=['order']),
}


def _cfg(kind):
    if kind not in CRUD:
        from django.http import Http404
        raise Http404
    return CRUD[kind]


@staff_required
def crud_list(request, kind):
    cfg = _cfg(kind)
    rows = cfg['model'].objects.all().order_by(*cfg['order'])
    if kind == 'categories':
        rows = rows.select_related('parent').annotate(product_total=Count('products'))
    return render(request, 'dashboard/crud_list.html', {
        'kind': kind, 'cfg': cfg, 'rows': rows, 'page': 'content' if kind not in ('categories', 'brands', 'tags') else 'catalog',
        'section': 'catalog' if kind in ('categories', 'brands', 'tags') else 'content',
    })


@staff_required
def crud_form(request, kind, pk=None):
    cfg = _cfg(kind)
    obj = get_object_or_404(cfg['model'], pk=pk) if pk else None
    form = cfg['form'](request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{cfg["singular"]} saved.')
        return redirect('dashboard:crud_list', kind=kind)
    return render(request, 'dashboard/crud_form.html', {
        'kind': kind, 'cfg': cfg, 'form': form, 'obj': obj,
        'page': 'content' if kind not in ('categories', 'brands', 'tags') else 'catalog',
    })


@staff_required
@require_POST
def crud_delete(request, kind, pk):
    cfg = _cfg(kind)
    obj = get_object_or_404(cfg['model'], pk=pk)
    try:
        obj.delete()
        messages.success(request, f'{cfg["singular"]} deleted.')
    except ProtectedError:
        messages.error(request, 'Cannot delete: products still use this. Move or delete those products first.')
    return redirect('dashboard:crud_list', kind=kind)


@staff_required
@require_POST
def crud_toggle(request, kind, pk):
    cfg = _cfg(kind)
    obj = get_object_or_404(cfg['model'], pk=pk)
    if hasattr(obj, 'active'):
        obj.active = not obj.active
        obj.save(update_fields=['active'])
    return redirect('dashboard:crud_list', kind=kind)
