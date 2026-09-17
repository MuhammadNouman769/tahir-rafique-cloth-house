from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import NewsletterForm
from .utils import is_ajax


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        msg = "Thanks for subscribing! Watch your inbox for exclusive deals."
        if is_ajax(request):
            return JsonResponse({'ok': True, 'message': msg})
        messages.success(request, msg)
    else:
        msg = "Please enter a valid email address."
        if is_ajax(request):
            return JsonResponse({'ok': False, 'message': msg}, status=400)
        messages.error(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'pages:home'))
