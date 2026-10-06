from django.contrib import messages
from django.shortcuts import redirect, render

from apps.core.models import SiteSettings
from apps.pages.models import AboutContent

from .decorators import staff_required
from .forms import AboutContentForm, SiteSettingsForm


@staff_required
def settings_view(request):
    obj = SiteSettings.load()
    form = SiteSettingsForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Store settings saved.')
        return redirect('dashboard:settings')
    return render(request, 'dashboard/settings.html', {'form': form, 'page': 'settings'})


@staff_required
def about_view(request):
    obj = AboutContent.load()
    form = AboutContentForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'About page saved.')
        return redirect('dashboard:about')
    return render(request, 'dashboard/about.html', {'form': form, 'page': 'content'})
