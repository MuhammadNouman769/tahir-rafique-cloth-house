from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.cart.cart import Cart
from .forms import CheckoutForm
from .models import Order
from . import services


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty. Add some products before checking out.")
        return redirect('products:shop')

    initial = {}
    if request.user.is_authenticated:
        initial = {'full_name': request.user.get_full_name(), 'email': request.user.email}

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = services.create_order_from_cart(cart, form.cleaned_data, user=request.user)
            whatsapp_url = services.build_whatsapp_url(order)
            cart.clear()
            request.session['last_order_whatsapp_url'] = whatsapp_url
            return redirect('orders:confirmation', order_number=order.order_number)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.html', {'form': form, 'cart': cart})


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    whatsapp_url = request.session.pop('last_order_whatsapp_url', None) or services.build_whatsapp_url(order)
    return render(request, 'orders/confirmation.html', {'order': order, 'whatsapp_url': whatsapp_url})


@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related('items')
    return render(request, 'orders/history.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    whatsapp_url = services.build_whatsapp_url(order)
    return render(request, 'orders/order_detail.html', {'order': order, 'whatsapp_url': whatsapp_url})
