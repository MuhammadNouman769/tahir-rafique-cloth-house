from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import NewsletterForm
from .utils import is_ajax
from django.http import JsonResponse
from .models import NewsletterSubscriber



def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    email = request.POST.get('email', '').strip().lower()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if form.is_valid() or NewsletterSubscriber.objects.filter(email=email).exists():
        sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if not created and not sub.is_active:
            sub.is_active = True          # dobara subscribe
            sub.save(update_fields=['is_active'])
        msg = "Thank you for subscribing! You'll be the first to know about new arrivals."
        ok = True
    else:
        msg, ok = "Please enter a valid email address.", False

    if is_ajax:
        return JsonResponse({'ok': ok, 'message': msg}, status=200 if ok else 400)
    (messages.success if ok else messages.error)(request, msg)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def newsletter_unsubscribe(request, token):
    sub = get_object_or_404(NewsletterSubscriber, token=token)
    sub.is_active = False
    sub.save(update_fields=['is_active'])
    return render(request, 'core/unsubscribed.html')