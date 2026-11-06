from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from apps.analytics.views import _get_client_ip
from .forms import LoginForm, ProfileUpdateForm, RegisterForm

# Brute-force throttling constants
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 900  # 15 minutes
SIGNUP_MAX_ATTEMPTS = 5
SIGNUP_WINDOW_SECONDS = 900  # 15 minutes


def signup_view(request):
    """Register a new developer account with IP-based anti-abuse throttling."""
    if request.user.is_authenticated:
        return redirect("portal:dashboard")

    client_ip = _get_client_ip(request)
    signup_throttle_key = f"throttle:signup:ip:{client_ip}"

    if request.method == "POST":
        signup_count = cache.get(signup_throttle_key, 0)
        if signup_count >= SIGNUP_MAX_ATTEMPTS:
            messages.error(
                request,
                "Too many account creation attempts from your IP address. Please wait a few minutes before trying again.",
            )
            return render(request, "accounts/signup.html", {"form": RegisterForm(request.POST)}, status=429)

        form = RegisterForm(request.POST)
        if form.is_valid():
            # Track signup attempt
            cache.set(signup_throttle_key, signup_count + 1, timeout=SIGNUP_WINDOW_SECONDS)
            user = form.save()
            login(request, user, backend="apps.accounts.backends.EmailOrUsernameBackend")
            messages.success(
                request,
                f"Welcome to CricPulse, {user.username}! Your Developer API key has been automatically generated below.",
            )
            return redirect("portal:dashboard")
        else:
            cache.set(signup_throttle_key, signup_count + 1, timeout=SIGNUP_WINDOW_SECONDS)
            messages.error(request, "Please correct the errors below to create your account.")
    else:
        form = RegisterForm()

    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    """Authenticate registered developers with brute-force throttling and open-redirect defenses."""
    if request.user.is_authenticated:
        return redirect("portal:dashboard")

    client_ip = _get_client_ip(request)
    username = request.POST.get("username", "").strip().lower() if request.method == "POST" else ""

    ip_throttle_key = f"throttle:login:ip:{client_ip}"
    user_throttle_key = f"throttle:login:user:{username}" if username else None

    if request.method == "POST":
        ip_attempts = cache.get(ip_throttle_key, 0)
        user_attempts = cache.get(user_throttle_key, 0) if user_throttle_key else 0

        if ip_attempts >= LOGIN_MAX_ATTEMPTS or user_attempts >= LOGIN_MAX_ATTEMPTS:
            messages.error(
                request,
                "Too many failed login attempts. For your security, access has been temporarily restricted. Please try again in 15 minutes.",
            )
            return render(request, "accounts/login.html", {"form": LoginForm(request, data=request.POST)}, status=429)

        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            # Clear failed login attempts upon successful authentication
            cache.delete(ip_throttle_key)
            if user_throttle_key:
                cache.delete(user_throttle_key)

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
            # Increment failed attempt counters
            cache.set(ip_throttle_key, ip_attempts + 1, timeout=LOGIN_LOCKOUT_SECONDS)
            if user_throttle_key:
                cache.set(user_throttle_key, user_attempts + 1, timeout=LOGIN_LOCKOUT_SECONDS)
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    """Terminate the current session securely via POST to prevent CSRF logout attacks."""
    username = request.user.username if request.user.is_authenticated else ""
    logout(request)
    if username:
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
