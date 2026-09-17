from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('update/<str:key>/', views.cart_update, name='cart_update'),
    path('remove/<str:key>/', views.cart_remove, name='cart_remove'),
]
