"""Business logic kept out of views/templates: order creation and WhatsApp
message generation."""
from urllib.parse import quote
from decimal import Decimal
from django.db import transaction
from apps.core.models import SiteSettings
from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(cart, form_data, user=None):
    """Creates an Order + OrderItems (with price snapshots) from the session cart."""
    settings_obj = SiteSettings.load()
    subtotal = cart.get_subtotal()
    delivery = Decimal('0') if subtotal >= settings_obj.free_delivery_threshold else settings_obj.delivery_charges
    total = subtotal + delivery

    order = Order.objects.create(
        customer=user if (user and user.is_authenticated) else None,
        full_name=form_data['full_name'],
        phone=form_data['phone'],
        whatsapp=form_data.get('whatsapp') or form_data['phone'],
        email=form_data.get('email', ''),
        city=form_data['city'],
        area=form_data.get('area', ''),
        address=form_data['address'],
        postal_code=form_data.get('postal_code', ''),
        notes=form_data.get('notes', ''),
        subtotal=subtotal,
        discount=Decimal('0'),
        delivery_charges=delivery,
        total=total,
    )

    for line in cart:
        OrderItem.objects.create(
            order=order,
            product=line['product'],
            product_name=line['product'].name,
            price=line['price'],
            quantity=line['quantity'],
            size=line['size'],
            color=line['color'],
        )
        # Decrease stock defensively
        product = line['product']
        product.stock_quantity = max(0, product.stock_quantity - line['quantity'])
        product.save(update_fields=['stock_quantity'])

    return order


def build_whatsapp_message(order):
    settings_obj = SiteSettings.load()
    currency = settings_obj.currency_symbol
    lines = [
        "Hello, I want to place an order.",
        "",
        f"Order #{order.order_number}",
        "",
        "Customer:",
        order.full_name,
        "",
        "Phone:",
        order.phone,
        "",
        "Address:",
        f"{order.address}, {order.area + ', ' if order.area else ''}{order.city}, Pakistan",
        "",
        "Products:",
        "",
    ]
    for idx, item in enumerate(order.items.all(), start=1):
        lines.append(f"{idx}. {item.product_name}")
        if item.size:
            lines.append(f"   Size: {item.size}")
        if item.color:
            lines.append(f"   Color: {item.color}")
        lines.append(f"   Qty: {item.quantity}")
        lines.append(f"   Price: {currency} {item.subtotal:,.0f}")
        lines.append("")

    lines.append(f"Subtotal: {currency} {order.subtotal:,.0f}")
    lines.append(f"Delivery: {currency} {order.delivery_charges:,.0f}")
    lines.append(f"Total: {currency} {order.total:,.0f}")
    lines.append("")
    lines.append("Please confirm my order.")

    return "\n".join(lines)


def build_whatsapp_url(order):
    settings_obj = SiteSettings.load()
    number = settings_obj.whatsapp_international
    message = build_whatsapp_message(order)
    encoded_message = quote(message)
    return f"https://wa.me/{number}?text={encoded_message}"
