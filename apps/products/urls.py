from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.shop, name='shop'),
    path('search/', views.search, name='search'),
    path('deals/', views.deals, name='deals'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('<slug:slug>/', views.product_detail, name='detail'),
]
