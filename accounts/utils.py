from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .models import EmailVerificationToken


def create_email_verification_token(user):
    """
    Create a new email verification token for a user.
    """

    return EmailVerificationToken.objects.create(
        user=user
    )


def send_verification_email(request, user):
    """
    Create a verification token and send the verification email.
    """

    token = create_email_verification_token(user)

    verification_path = reverse(
        "accounts:verify_email",
        kwargs={
            "token": token.token,
        },
    )

    verification_url = request.build_absolute_uri(
        verification_path
    )

    subject = "Verify your YouthConnect account"

    message = f"""
Hello {user.full_name},

Welcome to the YouthConnect Platform.

Please verify your email address by clicking the link below:

{verification_url}

This verification link will expire after 24 hours.

If you did not create a YouthConnect account, you can ignore this email.

Regards,

YouthConnect Platform
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return token