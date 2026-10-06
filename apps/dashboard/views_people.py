from datetime import datetime, timezone as dt_timezone

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.contact.models import ContactMessage
from apps.core.models import NewsletterSubscriber
from apps.orders.models import Order
from apps.products.models import Review

from . import analytics as an
from .decorators import staff_required
from .helpers import csv_response, paginate, wa_number


@staff_required
def customers_list(request):
    directory = an.customer_directory()
    summary = an.customer_summary(directory)
    q = request.GET.get('q', '').strip().lower()
    seg = request.GET.get('segment', '')
    sort = request.GET.get('sort', '-spent')
    if q:
        directory = [c for c in directory if q in (c['name'] or '').lower() or q in (c['phone'] or '').lower()
                     or q in (c['email'] or '').lower() or q in (c['city'] or '').lower()]
    if seg:
        directory = [c for c in directory if c['segment'] == seg]
    keymap = {'spent': 'spent', 'orders': 'orders', 'name': 'name', 'last': 'last', 'first': 'first'}
    field = sort.lstrip('-')
    if field in keymap:
        floor_dt = datetime.min.replace(tzinfo=dt_timezone.utc)
        directory.sort(key=lambda c: (c[field] or floor_dt) if field in ('last', 'first')
                       else (c[field].lower() if field == 'name' else c[field]), reverse=sort.startswith('-'))
    if request.GET.get('export') == 'csv':
        rows = [[c['name'], c['phone'], c['email'], c['city'], c['orders'], c['spent'], c['segment'],
                 'Yes' if c['registered'] else 'Guest'] for c in directory]
        return csv_response('customers.csv', ['Name', 'Phone', 'Email', 'City', 'Orders', 'Total spent',
                                              'Segment', 'Account'], rows)
    return render(request, 'dashboard/customers_list.html', {
        'customers': paginate(request, directory, 15), 'summary': summary, 'q': request.GET.get('q', ''),
        'segment': seg, 'sort': sort, 'segments': ['VIP', 'Returning', 'New', 'Lead'],
        'result_count': len(directory), 'page': 'customers',
    })


@staff_required
def customer_detail(request, key):
    if key.startswith('u') and key[1:].isdigit():
        orders = Order.objects.filter(customer_id=int(key[1:]))
        user = User.objects.filter(pk=int(key[1:])).select_related('profile').first()
        if not user and not orders.exists():
            raise Http404
    elif key.startswith('g') and key[1:].isdigit():
        user = None
        orders = Order.objects.filter(customer__isnull=True)
        orders = [o for o in orders if ''.join(c for c in o.phone if c.isdigit()) == key[1:]]
        if not orders:
            raise Http404
        orders = Order.objects.filter(pk__in=[o.pk for o in orders])
    else:
        raise Http404
    orders = orders.prefetch_related('items')
    good = [o for o in orders if o.status != Order.STATUS_CANCELLED]
    last = orders.first()
    spent = sum(o.total for o in good)
    prof = getattr(user, 'profile', None) if user else None
    info = {
        'name': (user.get_full_name() or user.username) if user else (last.full_name if last else ''),
        'email': (user.email if user else '') or (last.email if last else ''),
        'phone': (prof.phone if prof and prof.phone else '') or (last.phone if last else ''),
        'city': (prof.city if prof and prof.city else '') or (last.city if last else ''),
        'address': (prof.address if prof and prof.address else '') or (last.address if last else ''),
        'joined': user.date_joined if user else (orders.last().created_at if orders else None),
        'registered': bool(user),
    }
    fav = {}
    for o in good:
        for it in o.items.all():
            fav[it.product_name] = fav.get(it.product_name, 0) + it.quantity
    return render(request, 'dashboard/customer_detail.html', {
        'info': info, 'orders': orders, 'spent': spent, 'order_count': len(orders),
        'aov': (spent / len(good)) if good else 0,
        'favorites': sorted(fav.items(), key=lambda x: -x[1])[:5],
        'whatsapp': wa_number(info['phone']) if info['phone'] else '',
        'page': 'customers',
    })


# ───────────── Contact messages ─────────────
@staff_required
def messages_list(request):
    qs = ContactMessage.objects.all()
    status, q = request.GET.get('status', ''), request.GET.get('q', '').strip()
    if status == 'unread':
        qs = qs.filter(is_read=False)
    elif status == 'read':
        qs = qs.filter(is_read=True)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(subject__icontains=q) | Q(message__icontains=q))
    return render(request, 'dashboard/messages_list.html', {
        'items': paginate(request, qs, 15), 'status': status, 'q': q,
        'unread': ContactMessage.objects.filter(is_read=False).count(),
        'total': ContactMessage.objects.count(), 'page': 'messages',
    })


@staff_required
def message_detail(request, pk):
    m = get_object_or_404(ContactMessage, pk=pk)
    if not m.is_read:
        m.is_read = True
        m.save(update_fields=['is_read'])
    return render(request, 'dashboard/message_detail.html', {
        'm': m, 'whatsapp': wa_number(m.phone) if m.phone else '', 'page': 'messages'})


@staff_required
@require_POST
def messages_action(request):
    ids = request.POST.getlist('ids') or ([request.POST['id']] if request.POST.get('id') else [])
    action = request.POST.get('action')
    qs = ContactMessage.objects.filter(pk__in=ids)
    if action == 'read':
        qs.update(is_read=True)
    elif action == 'unread':
        qs.update(is_read=False)
    elif action == 'delete':
        qs.delete()
        messages.success(request, 'Deleted.')
    return redirect(request.POST.get('next') or 'dashboard:messages')


# ───────────── Newsletter ─────────────
@staff_required
def subscribers_list(request):
    qs = NewsletterSubscriber.objects.all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(email__icontains=q)
    if request.GET.get('export') == 'csv':
        return csv_response('subscribers.csv', ['Email', 'Subscribed'],
                            [[s.email, s.subscribed_at.strftime('%Y-%m-%d')] for s in qs])
    return render(request, 'dashboard/subscribers_list.html', {
        'items': paginate(request, qs, 20), 'q': q, 'total': NewsletterSubscriber.objects.count(), 'page': 'subscribers'})


@staff_required
@require_POST
def subscriber_delete(request, pk):
    get_object_or_404(NewsletterSubscriber, pk=pk).delete()
    messages.success(request, 'Subscriber removed.')
    return redirect('dashboard:subscribers')
