from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'size', 'color')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'phone', 'total', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'full_name', 'phone', 'email')
    readonly_fields = ('order_number', 'subtotal', 'discount', 'delivery_charges', 'total',
                        'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order', {'fields': ('order_number', 'customer', 'status')}),
        ('Customer', {'fields': ('full_name', 'phone', 'whatsapp', 'email')}),
        ('Delivery Address', {'fields': ('city', 'area', 'address', 'postal_code', 'notes')}),
        ('Totals', {'fields': ('subtotal', 'discount', 'delivery_charges', 'total')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
