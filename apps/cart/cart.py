"""Session-based shopping cart. Works for guests and authenticated users alike,
since it is keyed off the request session (Django keeps sessions per-user)."""
from decimal import Decimal
from django.conf import settings
from apps.products.models import Product


def _line_key(product_id, size, color):
    return f"{product_id}::{size or ''}::{color or ''}"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, size='', color='', update_quantity=False):
        key = _line_key(product.id, size, color)
        if key not in self.cart:
            self.cart[key] = {
                'product_id': product.id,
                'quantity': 0,
                'size': size,
                'color': color,
                'price': str(product.current_price),
            }
        if update_quantity:
            self.cart[key]['quantity'] = quantity
        else:
            self.cart[key]['quantity'] += quantity
        max_qty = max(product.stock_quantity, 1)
        self.cart[key]['quantity'] = max(1, min(self.cart[key]['quantity'], max_qty))
        self.save()

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def update(self, key, quantity):
        if key in self.cart and quantity > 0:
            self.cart[key]['quantity'] = quantity
            self.save()
        elif key in self.cart and quantity <= 0:
            self.remove(key)

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = Product.objects.filter(id__in=product_ids).prefetch_related('images')
        products_map = {p.id: p for p in products}
        for key, item in self.cart.items():
            product = products_map.get(item['product_id'])
            if not product:
                continue
            line = item.copy()
            line['key'] = key
            line['product'] = product
            line['price'] = Decimal(item['price'])
            line['subtotal'] = line['price'] * item['quantity']
            yield line

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal(self):
        return sum((Decimal(item['price']) * item['quantity'] for item in self.cart.values()), Decimal('0'))
