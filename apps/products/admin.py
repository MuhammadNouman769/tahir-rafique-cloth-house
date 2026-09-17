from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Tag, Brand, Size, Color, Product, ProductImage, Review


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'preview', 'alt_text', 'is_primary', 'order')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', obj.image.url)
        return "-"
    preview.short_description = "Preview"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'active')
    list_editable = ('order', 'active')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('active', 'parent')
    search_fields = ('name',)  # required for autocomplete_fields on ProductAdmin


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)  # required for autocomplete_fields on ProductAdmin


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code', 'swatch')

    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;border-radius:50%;'
            'background:{};border:1px solid #ccc;"></span>', obj.hex_code)
    swatch.short_description = "Swatch"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'sale_price', 'discount_badge',
                     'stock_quantity', 'available', 'featured', 'bestseller', 'new_arrival', 'deal_of_day')
    list_editable = ('price', 'sale_price', 'stock_quantity', 'available',
                      'featured', 'bestseller', 'new_arrival', 'deal_of_day')
    list_filter = ('category', 'available', 'featured', 'bestseller', 'new_arrival', 'deal_of_day', 'brand')
    search_fields = ('name', 'sku', 'description', 'tags__name')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('tags', 'sizes', 'colors')
    inlines = [ProductImageInline]
    autocomplete_fields = ['category', 'brand']
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'sku', 'category', 'brand', 'tags')}),
        ('Description', {'fields': ('short_description', 'description', 'material', 'care_instructions')}),
        ('Pricing & Stock', {'fields': ('price', 'sale_price', 'stock_quantity', 'available')}),
        ('Flags', {'fields': ('featured', 'bestseller', 'new_arrival', 'deal_of_day')}),
        ('Variants', {'fields': ('sizes', 'colors')}),
        ('Rating', {'fields': ('rating', 'review_count')}),
    )

    def discount_badge(self, obj):
        if obj.is_on_sale:
            return format_html('<b style="color:#c0392b">{}% OFF</b>', obj.discount_percentage)
        return "-"
    discount_badge.short_description = "Discount"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer_name', 'rating', 'approved', 'created_at')
    list_editable = ('approved',)
    list_filter = ('approved', 'rating')
