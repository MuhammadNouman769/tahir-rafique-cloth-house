from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta

from apps.orders.models import Order

from .decorators import staff_required
from .forms import OrderUpdateForm
from .helpers import csv_response, paginate, wa_number


def _filtered_orders(request):
    qs = Order.objects.select_related('customer').annotate(item_count=Sum('items__quantity'))
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    period = request.GET.get('period', '')
    city = request.GET.get('city', '')
    if status in dict(Order.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(order_number__icontains=q) | Q(full_name__icontains=q) |
                       Q(phone__icontains=q) | Q(email__icontains=q) | Q(items__product_name__icontains=q)).distinct()
    if city:
        qs = qs.filter(city=city)
    if period in ('today', '7', '30', '90'):
        now = timezone.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period != 'today':
            start = start - timedelta(days=int(period))
        qs = qs.filter(created_at__gte=start)
    sort = request.GET.get('sort', '-created_at')
    if sort not in ('created_at', '-created_at', 'total', '-total'):
        sort = '-created_at'
    return qs.order_by(sort), status, q, period, city, sort


@staff_required
def orders_list(request):
    qs, status, q, period, city, sort = _filtered_orders(request)
    if request.GET.get('export') == 'csv':
        rows = [[o.order_number, o.created_at.strftime('%Y-%m-%d %H:%M'), o.full_name, o.phone, o.city,
                 o.get_status_display(), o.subtotal, o.delivery_charges, o.total] for o in qs]
        return csv_response('orders.csv', ['Order', 'Date', 'Customer', 'Phone', 'City', 'Status',
                                           'Subtotal', 'Delivery', 'Total'], rows)
    counts = {r['status']: r['n'] for r in Order.objects.values('status').annotate(n=Count('id'))}
    tabs = [{'key': '', 'label': 'All', 'count': sum(counts.values())}] + [
        {'key': k, 'label': l, 'count': counts.get(k, 0)} for k, l in Order.STATUS_CHOICES]
    ctx = {
        'orders': paginate(request, qs, 15), 'status': status, 'q': q, 'period': period, 'city': city,
        'sort': sort, 'tabs': tabs, 'status_choices': Order.STATUS_CHOICES,
        'cities': Order.objects.order_by('city').values_list('city', flat=True).distinct(),
        'result_count': qs.count(), 'page': 'orders',
    }
    return render(request, 'dashboard/orders_list.html', ctx)


def _apply_status(order, new_status):
    """Change status and keep stock honest: cancelling returns items to stock,
    un-cancelling takes them out again."""
    old = order.status
    if old == new_status:
        return
    was_cancelled, now_cancelled = old == Order.STATUS_CANCELLED, new_status == Order.STATUS_CANCELLED
    if now_cancelled != was_cancelled:
        for item in order.items.select_related('product'):
            p = item.product
            if not p:
                continue
            if now_cancelled:
                p.stock_quantity += item.quantity
            else:
                p.stock_quantity = max(0, p.stock_quantity - item.quantity)
            p.save(update_fields=['stock_quantity'])
    order.status = new_status
    order.save(update_fields=['status', 'updated_at'])


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer').prefetch_related('items__product__images'), pk=pk)
    if request.method == 'POST':
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            old_status = Order.objects.get(pk=order.pk).status
            obj = form.save(commit=False)
            obj.status = old_status          # let _apply_status handle the status change + stock
            obj.save()
            _apply_status(obj, new_status)
            messages.success(request, f'Order {order.order_number} updated.')
            return redirect('dashboard:order_detail', pk=order.pk)
    else:
        form = OrderUpdateForm(instance=order)
    flow = [s for s, _ in Order.STATUS_CHOICES if s != Order.STATUS_CANCELLED]
    idx = flow.index(order.status) if order.status in flow else -1
    steps = [{'key': s, 'label': dict(Order.STATUS_CHOICES)[s], 'done': idx >= i} for i, s in enumerate(flow)]
    return render(request, 'dashboard/order_detail.html', {
        'order': order, 'form': form, 'steps': steps, 'cancelled': order.status == Order.STATUS_CANCELLED,
        'whatsapp_url': f"https://wa.me/{wa_number(order.whatsapp or order.phone)}",
        'customer_key': f'u{order.customer_id}' if order.customer_id else '',
        'page': 'orders',
    })


@staff_required
def order_invoice(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    return render(request, 'dashboard/invoice.html', {'order': order})


@staff_required
@require_POST
def order_quick_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new = request.POST.get('status')
    if new in dict(Order.STATUS_CHOICES):
        _apply_status(order, new)
        messages.success(request, f'{order.order_number} → {order.get_status_display()}')
    return redirect(request.POST.get('next') or 'dashboard:orders')


@staff_required
@require_POST
def orders_bulk(request):
    ids = request.POST.getlist('ids')
    new = request.POST.get('status')
    if ids and new in dict(Order.STATUS_CHOICES):
        for o in Order.objects.filter(pk__in=ids):
            _apply_status(o, new)
        messages.success(request, f'{len(ids)} order(s) marked {dict(Order.STATUS_CHOICES)[new]}.')
    else:
        messages.warning(request, 'Select at least one order and a status.')
    return redirect(request.POST.get('next') or 'dashboard:orders')


@staff_required
@require_POST
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != Order.STATUS_CANCELLED:
        _apply_status(order, Order.STATUS_CANCELLED)   # return stock before deleting
    num = order.order_number
    order.delete()
    messages.success(request, f'Order {num} deleted.')
    return redirect('dashboard:orders')
