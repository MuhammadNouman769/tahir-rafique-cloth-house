"""All dashboard numbers are computed here, in the database, so views stay thin.

"Revenue" always means orders that are NOT cancelled.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce, ExtractHour, ExtractWeekDay, TruncDate, TruncMonth
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.products.models import Category, Product, Review

RANGES = [('7', 'Last 7 days'), ('30', 'Last 30 days'), ('90', 'Last 90 days'),
          ('365', 'Last 12 months'), ('all', 'All time')]


def valid_orders():
    return Order.objects.exclude(status=Order.STATUS_CANCELLED)


def get_range(request, default='30'):
    """Returns (key, start_datetime or None, end_datetime, prev_start, prev_end)."""
    key = request.GET.get('range', default)
    if key not in dict(RANGES):
        key = default
    now = timezone.now()
    if key == 'all':
        return key, None, now, None, None
    days = int(key)
    start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    prev_end = start
    prev_start = start - timedelta(days=days)
    return key, start, now, prev_start, prev_end


def _between(qs, start, end, field='created_at'):
    if start is not None:
        qs = qs.filter(**{f'{field}__gte': start})
    if end is not None:
        qs = qs.filter(**{f'{field}__lte': end})
    return qs


def _pct_change(current, previous):
    current, previous = float(current or 0), float(previous or 0)
    if previous == 0:
        return None if current == 0 else 100.0
    return round((current - previous) / previous * 100, 1)


def _period_stats(start, end):
    orders = _between(Order.objects.all(), start, end)
    good = orders.exclude(status=Order.STATUS_CANCELLED)
    agg = good.aggregate(revenue=Coalesce(Sum('total'), Decimal('0')), count=Count('id'),
                         aov=Coalesce(Avg('total'), Decimal('0')))
    units = _between(OrderItem.objects.exclude(order__status=Order.STATUS_CANCELLED),
                     start, end, 'order__created_at').aggregate(u=Coalesce(Sum('quantity'), 0))['u']
    total_orders = orders.count()
    cancelled = orders.filter(status=Order.STATUS_CANCELLED).count()
    new_customers = _between(User.objects.filter(is_staff=False), start, end, 'date_joined').count()
    return {
        'revenue': agg['revenue'], 'orders': agg['count'], 'aov': agg['aov'], 'units': units,
        'cancel_rate': round(cancelled / total_orders * 100, 1) if total_orders else 0,
        'new_customers': new_customers, 'all_orders': total_orders,
    }


def kpis(start, end, prev_start, prev_end):
    cur = _period_stats(start, end)
    prev = _period_stats(prev_start, prev_end) if prev_start else None
    cards = []
    for key, label, kind in [('revenue', 'Revenue', 'money'), ('orders', 'Orders', 'int'),
                             ('aov', 'Avg. order value', 'money'), ('units', 'Items sold', 'int'),
                             ('new_customers', 'New customers', 'int'),
                             ('cancel_rate', 'Cancellation rate', 'pct')]:
        cards.append({
            'key': key, 'label': label, 'kind': kind, 'value': cur[key],
            'change': _pct_change(cur[key], prev[key]) if prev else None,
            # for cancel rate, a rise is bad
            'inverse': key == 'cancel_rate',
        })
    return cards


def daily_series(start, end):
    """Revenue + order count per day, with zero-filled gaps."""
    qs = _between(valid_orders(), start, end)
    rows = (qs.annotate(d=TruncDate('created_at'))
              .values('d').annotate(rev=Sum('total'), n=Count('id')).order_by('d'))
    data = {r['d']: r for r in rows}
    if not data:
        return [], [], []
    first = start.date() if start else min(data)
    last = end.date()
    labels, revenue, counts = [], [], []
    d = first
    while d <= last:
        r = data.get(d)
        labels.append(d.strftime('%d %b'))
        revenue.append(float(r['rev']) if r else 0)
        counts.append(r['n'] if r else 0)
        d += timedelta(days=1)
    return labels, revenue, counts


def monthly_series(months=12):
    now = timezone.now()
    start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
             - timedelta(days=31 * (months - 1))).replace(day=1)
    rows = (valid_orders().filter(created_at__gte=start)
            .annotate(m=TruncMonth('created_at')).values('m')
            .annotate(rev=Sum('total'), n=Count('id')).order_by('m'))
    return ([r['m'].strftime('%b %Y') for r in rows],
            [float(r['rev']) for r in rows], [r['n'] for r in rows])


def status_breakdown(start, end):
    qs = _between(Order.objects.all(), start, end)
    counts = {r['status']: r['n'] for r in qs.values('status').annotate(n=Count('id'))}
    return [{'key': k, 'label': label, 'count': counts.get(k, 0)} for k, label in Order.STATUS_CHOICES]


def top_products(start, end, limit=8):
    items = _between(OrderItem.objects.exclude(order__status=Order.STATUS_CANCELLED),
                     start, end, 'order__created_at')
    line_total = ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField(max_digits=14, decimal_places=2))
    rows = (items.exclude(product__isnull=True).values('product_id', 'product_name')
            .annotate(units=Sum('quantity'), revenue=Sum(line_total))
            .order_by('-revenue')[:limit])
    rows = list(rows)
    imgs = {p.id: p for p in Product.objects.filter(id__in=[r['product_id'] for r in rows])
            .prefetch_related('images')}
    for r in rows:
        r['product'] = imgs.get(r['product_id'])
    return rows


def category_sales(start, end):
    """Revenue per top-level category (children rolled up into their parent)."""
    items = _between(OrderItem.objects.exclude(order__status=Order.STATUS_CANCELLED),
                     start, end, 'order__created_at').exclude(product__isnull=True)
    line_total = ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField(max_digits=14, decimal_places=2))
    rows = items.values('product__category__name', 'product__category__parent__name') \
                .annotate(revenue=Sum(line_total), units=Sum('quantity'))
    agg = {}
    for r in rows:
        name = r['product__category__parent__name'] or r['product__category__name']
        a = agg.setdefault(name, {'name': name, 'revenue': 0.0, 'units': 0})
        a['revenue'] += float(r['revenue'])
        a['units'] += r['units']
    return sorted(agg.values(), key=lambda x: -x['revenue'])


def city_sales(start, end, limit=8):
    qs = _between(valid_orders(), start, end)
    return list(qs.values('city').annotate(revenue=Sum('total'), n=Count('id')).order_by('-revenue')[:limit])


def weekday_hour_distribution(start, end):
    qs = _between(valid_orders(), start, end)
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    wd = {r['w']: r['n'] for r in qs.annotate(w=ExtractWeekDay('created_at')).values('w').annotate(n=Count('id'))}
    hr = {r['h']: r['n'] for r in qs.annotate(h=ExtractHour('created_at')).values('h').annotate(n=Count('id'))}
    # Django weekday: 1=Sunday..7=Saturday
    return ({'labels': days, 'data': [wd.get(i + 1, 0) for i in range(7)]},
            {'labels': [f"{h:02d}:00" for h in range(24)], 'data': [hr.get(h, 0) for h in range(24)]})


def low_stock(threshold=5, limit=8):
    return (Product.objects.filter(stock_quantity__lte=threshold).order_by('stock_quantity', 'name')[:limit])


def rating_distribution():
    counts = {r['rating']: r['n'] for r in Review.objects.values('rating').annotate(n=Count('id'))}
    total = sum(counts.values())
    return [{'stars': s, 'count': counts.get(s, 0),
             'pct': round(counts.get(s, 0) / total * 100) if total else 0} for s in range(5, 0, -1)]


def customer_directory():
    """Unified customer list. Registered users are keyed by user id; guest buyers are
    grouped by phone number, so a returning guest is counted once."""
    rows = {}
    for o in Order.objects.all().order_by('created_at'):
        key = f"u{o.customer_id}" if o.customer_id else f"g{''.join(ch for ch in o.phone if ch.isdigit())}"
        c = rows.setdefault(key, {
            'key': key, 'name': o.full_name, 'phone': o.phone, 'email': o.email, 'city': o.city,
            'registered': bool(o.customer_id), 'user_id': o.customer_id,
            'orders': 0, 'spent': Decimal('0'), 'first': o.created_at, 'last': o.created_at,
        })
        c['name'], c['city'] = o.full_name, o.city
        c['email'] = o.email or c['email']
        c['last'] = o.created_at
        c['orders'] += 1
        if o.status != Order.STATUS_CANCELLED:
            c['spent'] += o.total
    # registered users that never ordered
    ordered_ids = {c['user_id'] for c in rows.values() if c['user_id']}
    for u in User.objects.filter(is_staff=False).exclude(id__in=ordered_ids).select_related('profile'):
        prof = getattr(u, 'profile', None)
        rows[f"u{u.id}"] = {
            'key': f"u{u.id}", 'name': u.get_full_name() or u.username, 'phone': prof.phone if prof else '',
            'email': u.email, 'city': prof.city if prof else '', 'registered': True, 'user_id': u.id,
            'orders': 0, 'spent': Decimal('0'), 'first': u.date_joined, 'last': None,
        }
    for c in rows.values():
        c['aov'] = (c['spent'] / c['orders']) if c['orders'] else Decimal('0')
        c['segment'] = segment(c)
    return list(rows.values())


def segment(c):
    if c['orders'] == 0:
        return 'Lead'
    if c['spent'] >= 30000 or c['orders'] >= 5:
        return 'VIP'
    if c['orders'] >= 2:
        return 'Returning'
    return 'New'


def customer_summary(directory):
    total = len(directory)
    repeat = sum(1 for c in directory if c['orders'] >= 2)
    buyers = sum(1 for c in directory if c['orders'] >= 1)
    return {
        'total': total, 'buyers': buyers, 'repeat': repeat,
        'repeat_rate': round(repeat / buyers * 100) if buyers else 0,
        'vip': sum(1 for c in directory if c['segment'] == 'VIP'),
        'registered': sum(1 for c in directory if c['registered']),
    }
