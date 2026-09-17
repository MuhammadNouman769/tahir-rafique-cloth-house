from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

INPUT_CLASS = 'w-full border border-line px-4 py-3 rounded outline-none focus:border-golddark'


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': INPUT_CLASS}))
    first_name = forms.CharField(required=True, max_length=100, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    last_name = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('username', 'password1', 'password2'):
            self.fields[field].widget.attrs.update({'class': INPUT_CLASS})


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': INPUT_CLASS}))

    class Meta:
        model = Profile
        fields = ['phone', 'whatsapp', 'address', 'city']
        widgets = {
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'whatsapp': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'address': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
            'city': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        profile.user.email = self.cleaned_data['email']
        if commit:
            profile.user.save()
            profile.save()
        return profile
