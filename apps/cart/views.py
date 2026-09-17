from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from apps.products.models import Product
from apps.core.utils import is_ajax
from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if not product.in_stock:
        msg = "Sorry, this product is out of stock."
        if is_ajax(request):
            return JsonResponse({'ok': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'products:shop'))

    size = request.POST.get('size', '')
    color = request.POST.get('color', '')
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1

    cart.add(product=product, quantity=quantity, size=size, color=color)
    msg = f'"{product.name}" added to your cart.'

    if is_ajax(request):
        return JsonResponse({
            'ok': True,
            'message': msg,
            'cart_count': len(cart),
            'redirect': request.POST.get('next') if request.POST.get('redirect_after') else None,
        })

    messages.success(request, msg)
    return redirect(request.POST.get('next') or 'cart:cart_detail')


def _cart_fragment(request, cart):
    return render_to_string('cart/_cart_body.html', {'cart': cart}, request=request)


@require_POST
def cart_update(request, key):
    cart = Cart(request)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    cart.update(key, quantity)

    if is_ajax(request):
        return JsonResponse({
            'ok': True,
            'cart_count': len(cart),
            'html': _cart_fragment(request, cart),
        })
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, key):
    cart = Cart(request)
    cart.remove(key)

    if is_ajax(request):
        return JsonResponse({
            'ok': True,
            'cart_count': len(cart),
            'html': _cart_fragment(request, cart),
        })
    messages.info(request, "Item removed from cart.")
    return redirect('cart:cart_detail')
