from django import forms
from .models import NewsletterSubscriber


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email address',
                'class': 'flex-1 border border-line px-4 py-3 rounded outline-none focus:border-golddark',
                'required': True,
            }),
        }
