from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-sm text-slate-800",
                "placeholder": "dev@company.com",
            }
        ),
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-sm text-slate-800",
                "placeholder": "Mohd Hamza",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["username"]:
            self.fields[field_name].widget.attrs.update(
                {
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-sm text-slate-800",
                    "placeholder": "username",
                }
            )
        for field_name in ["password1", "password2"]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update(
                    {
                        "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-sm text-slate-800",
                        "placeholder": "••••••••",
                    }
                )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-sm text-slate-800",
                "placeholder": "Username",
                "autofocus": True,
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-sm text-slate-800",
                "placeholder": "••••••••",
            }
        )
    )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-sm",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-sm",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-sm",
                }
            ),
        }
