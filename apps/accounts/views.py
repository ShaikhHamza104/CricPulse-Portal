from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import LoginForm, ProfileUpdateForm, RegisterForm


def signup_view(request):
    """Register a new developer account and automatically issue an initial API key."""
    if request.user.is_authenticated:
        return redirect("portal:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to CricPulse, {user.username}! Your Developer API key has been automatically generated below.",
            )
            return redirect("portal:dashboard")
        else:
            messages.error(request, "Please correct the errors below to create your account.")
    else:
        form = RegisterForm()

    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    """Authenticate registered developers with open-redirect defenses."""
    if request.user.is_authenticated:
        return redirect("portal:dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get("next") or request.POST.get("next")

            # Open Redirect Defense: Strictly allow only local/relative safe URLs
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("portal:dashboard")
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    """Terminate the current session securely."""
    username = request.user.username
    logout(request)
    messages.info(request, f"You have been signed out, {username}. See you next time!")
    return redirect("portal:home")


@login_required
def profile_view(request):
    """View and update developer profile details."""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details were updated successfully.")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Could not update profile. Please verify your inputs.")
    else:
        form = ProfileUpdateForm(instance=request.user)

    api_keys = request.user.api_keys.all()
    active_keys_count = api_keys.filter(is_active=True).count()

    context = {
        "form": form,
        "api_keys": api_keys,
        "active_keys_count": active_keys_count,
    }
    return render(request, "accounts/profile.html", context)
