from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.orders.models import Order
from apps.products.models import Product, Review

from . import analytics as an
from .decorators import staff_required


def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:overview')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username', '').strip(),
                            password=request.POST.get('password', ''))
        if user is not None and user.is_staff and user.is_active:
            login(request, user)
            nxt = request.POST.get('next') or request.GET.get('next')
            if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
                return redirect(nxt)
            return redirect('dashboard:overview')
        messages.error(request, 'Invalid credentials, or this account has no dashboard access.')
    return render(request, 'dashboard/login.html', {'next': request.GET.get('next', '')})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('dashboard:login')


@staff_required
def overview(request):
    key, start, end, pstart, pend = an.get_range(request, default='30')
    labels, revenue, counts = an.daily_series(start, end)
    cat = an.category_sales(start, end)
    status = an.status_breakdown(start, end)
    ctx = {
        'range_key': key, 'ranges': an.RANGES,
        'kpis': an.kpis(start, end, pstart, pend),
        'chart_daily': {'labels': labels, 'revenue': revenue, 'orders': counts},
        'chart_status': {'labels': [s['label'] for s in status], 'data': [s['count'] for s in status],
                         'keys': [s['key'] for s in status]},
        'chart_category': {'labels': [c['name'] for c in cat], 'data': [c['revenue'] for c in cat]},
        'status_rows': status,
        'top_products': an.top_products(start, end, 6),
        'recent_orders': Order.objects.select_related('customer')[:8],
        'low_stock': an.low_stock(),
        'pending_reviews': Review.objects.filter(approved=False).select_related('product')[:4],
        'out_of_stock': Product.objects.filter(stock_quantity=0).count(),
        'pending_count': Order.objects.filter(status=Order.STATUS_PENDING).count(),
        'page': 'overview',
    }
    return render(request, 'dashboard/overview.html', ctx)


@staff_required
def analytics_view(request):
    key, start, end, pstart, pend = an.get_range(request, default='90')
    labels, revenue, counts = an.daily_series(start, end)
    m_labels, m_rev, m_orders = an.monthly_series(12)
    weekday, hour = an.weekday_hour_distribution(start, end)
    cat = an.category_sales(start, end)
    cities = an.city_sales(start, end)
    status = an.status_breakdown(start, end)
    directory = an.customer_directory()
    ctx = {
        'range_key': key, 'ranges': an.RANGES,
        'kpis': an.kpis(start, end, pstart, pend),
        'chart_daily': {'labels': labels, 'revenue': revenue, 'orders': counts},
        'chart_monthly': {'labels': m_labels, 'revenue': m_rev, 'orders': m_orders},
        'chart_weekday': weekday, 'chart_hour': hour,
        'chart_category': {'labels': [c['name'] for c in cat], 'data': [c['revenue'] for c in cat]},
        'chart_city': {'labels': [c['city'] for c in cities], 'data': [float(c['revenue']) for c in cities]},
        'chart_status': {'labels': [s['label'] for s in status], 'data': [s['count'] for s in status],
                         'keys': [s['key'] for s in status]},
        'categories': cat, 'cities': cities,
        'top_products': an.top_products(start, end, 10),
        'customer_summary': an.customer_summary(directory),
        'rating_dist': an.rating_distribution(),
        'page': 'analytics',
    }
    return render(request, 'dashboard/analytics.html', ctx)
