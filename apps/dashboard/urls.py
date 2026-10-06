from django.urls import path

from . import views_catalog as vc, views_core as v, views_orders as vo, views_people as vp, views_settings as vs

app_name = 'dashboard'

urlpatterns = [
    path('login/', v.login_view, name='login'),
    path('logout/', v.logout_view, name='logout'),
    path('', v.overview, name='overview'),
    path('analytics/', v.analytics_view, name='analytics'),

    path('orders/', vo.orders_list, name='orders'),
    path('orders/bulk/', vo.orders_bulk, name='orders_bulk'),
    path('orders/<int:pk>/', vo.order_detail, name='order_detail'),
    path('orders/<int:pk>/invoice/', vo.order_invoice, name='order_invoice'),
    path('orders/<int:pk>/status/', vo.order_quick_status, name='order_status'),
    path('orders/<int:pk>/delete/', vo.order_delete, name='order_delete'),

    path('products/', vc.products_list, name='products'),
    path('products/new/', vc.product_form, name='product_new'),
    path('products/bulk/', vc.products_bulk, name='products_bulk'),
    path('products/<int:pk>/edit/', vc.product_form, name='product_edit'),
    path('products/<int:pk>/quick/', vc.product_quick_update, name='product_quick'),
    path('products/<int:pk>/delete/', vc.product_delete, name='product_delete'),

    path('reviews/', vc.reviews_list, name='reviews'),
    path('reviews/action/', vc.reviews_action, name='reviews_action'),

    path('customers/', vp.customers_list, name='customers'),
    path('customers/<str:key>/', vp.customer_detail, name='customer_detail'),

    path('messages/', vp.messages_list, name='messages'),
    path('messages/action/', vp.messages_action, name='messages_action'),
    path('messages/<int:pk>/', vp.message_detail, name='message_detail'),
    path('subscribers/', vp.subscribers_list, name='subscribers'),
    path('subscribers/<int:pk>/delete/', vp.subscriber_delete, name='subscriber_delete'),

    path('settings/', vs.settings_view, name='settings'),
    path('content/about/', vs.about_view, name='about'),

    path('manage/<str:kind>/', vc.crud_list, name='crud_list'),
    path('manage/<str:kind>/new/', vc.crud_form, name='crud_new'),
    path('manage/<str:kind>/<int:pk>/edit/', vc.crud_form, name='crud_edit'),
    path('manage/<str:kind>/<int:pk>/delete/', vc.crud_delete, name='crud_delete'),
    path('manage/<str:kind>/<int:pk>/toggle/', vc.crud_toggle, name='crud_toggle'),
]
