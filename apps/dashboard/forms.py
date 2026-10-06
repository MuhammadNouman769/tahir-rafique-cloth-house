from django import forms
from django.forms import inlineformset_factory, modelform_factory

from apps.contact.models import ContactMessage
from apps.core.models import GalleryImage, HeroSlide, PromoBanner, SiteSettings, Testimonial
from apps.orders.models import Order
from apps.pages.models import AboutContent
from apps.products.models import Brand, Category, Product, ProductImage, Tag


class StyledMixin:
    """Gives every widget the dashboard's CSS classes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs['class'] = 'check'
            elif isinstance(w, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                w.attrs['class'] = 'check-group'
            elif isinstance(w, forms.FileInput):
                w.attrs['class'] = 'input file'
            elif isinstance(w, forms.SelectMultiple):
                w.attrs['class'] = 'input multi'
            elif isinstance(w, forms.Select):
                w.attrs['class'] = 'input'
            elif isinstance(w, forms.Textarea):
                w.attrs.update({'class': 'input', 'rows': w.attrs.get('rows', 4)})
            elif isinstance(w, forms.TextInput) and getattr(w, 'input_type', '') == 'color':
                w.attrs['class'] = 'input color'
            else:
                w.attrs['class'] = 'input'


class DashModelForm(StyledMixin, forms.ModelForm):
    pass


class ProductForm(DashModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'brand', 'tags', 'short_description', 'description',
                  'material', 'care_instructions', 'price', 'sale_price', 'stock_quantity',
                  'available', 'featured', 'bestseller', 'new_arrival', 'deal_of_day',
                  'sizes', 'colors']
        widgets = {
            'sizes': forms.CheckboxSelectMultiple, 'colors': forms.CheckboxSelectMultiple,
            'tags': forms.SelectMultiple, 'description': forms.Textarea(attrs={'rows': 6}),
            'care_instructions': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        data = super().clean()
        price, sale = data.get('price'), data.get('sale_price')
        if price is not None and sale is not None and sale >= price:
            self.add_error('sale_price', 'Sale price must be lower than the regular price (or leave it empty).')
        return data


class ProductImageForm(DashModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'order']


ProductImageFormSet = inlineformset_factory(Product, ProductImage, form=ProductImageForm,
                                            extra=2, can_delete=True)


class CategoryForm(DashModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent', 'image', 'description', 'order', 'active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Category.objects.filter(parent__isnull=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields['parent'].queryset = qs
        self.fields['parent'].required = False


class BrandForm(DashModelForm):
    class Meta:
        model = Brand
        fields = ['name']


class TagForm(DashModelForm):
    class Meta:
        model = Tag
        fields = ['name']


class HeroSlideForm(DashModelForm):
    class Meta:
        model = HeroSlide
        fields = '__all__'


class PromoBannerForm(DashModelForm):
    class Meta:
        model = PromoBanner
        fields = '__all__'


class TestimonialForm(DashModelForm):
    class Meta:
        model = Testimonial
        fields = ['customer_name', 'city', 'rating', 'comment', 'photo', 'active']


class GalleryImageForm(DashModelForm):
    class Meta:
        model = GalleryImage
        fields = '__all__'


class SiteSettingsForm(DashModelForm):
    class Meta:
        model = SiteSettings
        exclude = ['updated_at']


class AboutContentForm(DashModelForm):
    class Meta:
        model = AboutContent
        fields = '__all__'


class OrderUpdateForm(DashModelForm):
    class Meta:
        model = Order
        fields = ['status', 'full_name', 'phone', 'whatsapp', 'email', 'city', 'area',
                  'address', 'postal_code', 'notes']
        widgets = {'address': forms.Textarea(attrs={'rows': 2}), 'notes': forms.Textarea(attrs={'rows': 2})}
