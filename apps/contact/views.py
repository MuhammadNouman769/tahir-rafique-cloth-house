from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Your message has been sent. We'll get back to you soon.")
            return redirect('contact:contact')
    else:
        form = ContactForm()
    return render(request, 'contact/contact.html', {'form': form})
