from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
]
