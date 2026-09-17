import django_filters
from django import forms
from django.db.models import Q
from .models import Product, Category, Size, Color


class ProductFilter(django_filters.FilterSet):
    category = django_filters.ModelMultipleChoiceFilter(
        field_name='category__slug', to_field_name='slug',
        queryset=Category.objects.filter(active=True))
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    size = django_filters.ModelMultipleChoiceFilter(
        field_name='sizes__name', to_field_name='name', queryset=Size.objects.all())
    color = django_filters.ModelMultipleChoiceFilter(
        field_name='colors__name', to_field_name='name', queryset=Color.objects.all())
    availability = django_filters.ChoiceFilter(
        method='filter_availability',
        choices=(('in_stock', 'In Stock'), ('out_of_stock', 'Out of Stock')),
        widget=forms.RadioSelect)

    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price', 'size', 'color']

    def filter_availability(self, queryset, name, value):
        if value == 'in_stock':
            return queryset.filter(available=True, stock_quantity__gt=0)
        if value == 'out_of_stock':
            return queryset.filter(Q(available=False) | Q(stock_quantity=0))
        return queryset
