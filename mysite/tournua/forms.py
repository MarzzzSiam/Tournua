from django import forms
from .models import UserAccount

class SignupForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ["full_name", "email", "password"]
        widgets = {
            "password": forms.PasswordInput(attrs={"placeholder": "Password (Min. 8 characters)"}),
        }

    # extra validation
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if UserAccount.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password
