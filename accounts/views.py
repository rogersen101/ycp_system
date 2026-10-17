from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .utils import send_verification_email
from .models import EmailVerificationToken, User,Profile
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .profile_forms import ProfileForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            send_verification_email(
                request,
                user,
            )

            messages.success(
                request,
                "Your account has been created successfully. "
                "Please check your email and verify your account "
                "before logging in.",
            )

            return redirect("accounts:login")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )
def verification_required(request):
    return render(
        request,
        "accounts/verification_required.html",
    )


def verify_email(request, token):
    try:
        verification_token = EmailVerificationToken.objects.select_related(
            "user"
        ).get(token=token)

    except EmailVerificationToken.DoesNotExist:
        messages.error(
            request,
            "The verification link is invalid.",
        )

        return redirect("accounts:login")

    if not verification_token.is_valid():

        if verification_token.used_at is not None:
            messages.info(
                request,
                "This email verification link has already been used.",
            )

        else:
            messages.error(
                request,
                "This verification link has expired. "
                "Please request a new verification email.",
            )

        return redirect(
            "accounts:resend_verification"
        )

    user = verification_token.user

    user.email_verified = True
    user.save(update_fields=["email_verified"])

    verification_token.mark_used()

    messages.success(
        request,
        "Your email address has been verified successfully. "
        "You can now log in.",
    )

    return redirect("accounts:login")

def resend_verification(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        email = request.POST.get(
            "email",
            "",
        ).strip().lower()

        if not email:
            messages.error(
                request,
                "Please enter your email address.",
            )

            return render(
                request,
                "accounts/resend_verification.html",
            )

        try:
            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:
            messages.error(
                request,
                "No account was found with that email address.",
            )

            return render(
                request,
                "accounts/resend_verification.html",
            )

        if user.email_verified:
            messages.info(
                request,
                "This email address has already been verified.",
            )

            return redirect(
                "accounts:login"
            )

        send_verification_email(
            request,
            user,
        )

        messages.success(
            request,
            "A new verification email has been sent.",
        )

        return redirect(
            "accounts:login"
        )

    return render(
        request,
        "accounts/resend_verification.html",
    )

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=email,
            password=password,
        )

        if user is not None:

            if not user.is_active:
                messages.error(
                    request,
                    "Your account is inactive. "
                    "Please contact the administrator.",
                )

                return redirect("accounts:login")

            if not user.email_verified:
                messages.warning(
                    request,
                    "Please verify your email address before logging in.",
                )

                return redirect(
                    "accounts:verification_required"
                )

            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.full_name}.",
            )

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid email address or password.",
        )

    return render(
        request,
        "accounts/login.html",
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)

        messages.success(
            request,
            "You have been logged out successfully.",
        )

        return redirect("accounts:login")

    return redirect("dashboard")

def development_password_reset(request):
    """
    Development-only password reset helper.

    Generates a password reset URL directly instead of requiring
    email delivery.
    """

    if not settings.DEBUG:
        return redirect("accounts:password_reset")

    reset_link = None

    if request.method == "POST":

        form = PasswordResetForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"]

            try:
                user = User.objects.get(
                    email__iexact=email,
                    is_active=True,
                )

            except User.DoesNotExist:
                messages.error(
                    request,
                    "No active account was found with that email address.",
                )

            else:

                if not user.has_usable_password():
                    messages.error(
                        request,
                        "This account does not have a usable password.",
                    )

                else:

                    uid = urlsafe_base64_encode(
                        force_bytes(user.pk)
                    )

                    token = default_token_generator.make_token(
                        user
                    )

                    reset_link = request.build_absolute_uri(
                        f"/accounts/reset/{uid}/{token}/"
                    )

    else:
        form = PasswordResetForm()

    return render(
        request,
        "accounts/development_password_reset.html",
        {
            "form": form,
            "reset_link": reset_link,
        },
    )
@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
        },
    )


@login_required
def edit_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():

            profile = form.save()

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect(
                "accounts:profile"
            )

    else:
        form = ProfileForm(
            instance=profile
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )