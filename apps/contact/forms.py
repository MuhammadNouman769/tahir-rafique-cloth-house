from django import forms
from .models import ContactMessage

INPUT_CLASS = 'w-full border border-line px-4 py-3 rounded outline-none focus:border-golddark'


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name', 'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email', 'class': INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number (optional)', 'class': INPUT_CLASS}),
            'subject': forms.TextInput(attrs={'placeholder': 'Subject', 'class': INPUT_CLASS}),
            'message': forms.Textarea(attrs={'placeholder': 'Your Message', 'rows': 5, 'class': INPUT_CLASS}),
        }
