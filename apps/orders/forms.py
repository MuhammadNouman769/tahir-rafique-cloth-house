from django import forms
from .models import Order

INPUT_CLASS = 'w-full border border-line px-4 py-3 rounded outline-none focus:border-golddark'


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'whatsapp', 'email', 'city', 'area',
                  'address', 'postal_code', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name', 'class': INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': INPUT_CLASS}),
            'whatsapp': forms.TextInput(attrs={'placeholder': 'WhatsApp Number (if different)', 'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': INPUT_CLASS}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': INPUT_CLASS}),
            'area': forms.TextInput(attrs={'placeholder': 'Area / Neighbourhood', 'class': INPUT_CLASS}),
            'address': forms.Textarea(attrs={'placeholder': 'Complete Address', 'rows': 3, 'class': INPUT_CLASS}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal Code', 'class': INPUT_CLASS}),
            'notes': forms.Textarea(attrs={'placeholder': 'Additional Notes (optional)', 'rows': 2, 'class': INPUT_CLASS}),
        }

    def clean_whatsapp(self):
        return self.cleaned_data.get('whatsapp') or self.cleaned_data.get('phone', '')
