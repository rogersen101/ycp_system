from datetime import date

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import User
from .models import Profile, Skill


class RegistrationForm(forms.ModelForm):
    """
    Registration form for new YCP participants.
    """

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter a strong password",
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
            "country",
            "date_of_birth",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your full name",
                    "autocomplete": "name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                    "autocomplete": "email",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your country",
                    "autocomplete": "country-name",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "An account with this email address already exists."
            )

        return email

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]

        if not date_of_birth:
            raise ValidationError("Date of birth is required.")

        today = date.today()

        age = (
            today.year
            - date_of_birth.year
            - (
                (today.month, today.day)
                < (date_of_birth.month, date_of_birth.day)
            )
        )

        if age < 18 or age > 35:
            raise ValidationError(
                "YCP participants must be between 18 and 35 years old."
            )

        return date_of_birth

    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        if password:
            password_validation.validate_password(password)

        return password

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error(
                "password2",
                "The two passwords do not match.",
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]
        user.role = User.Role.PARTICIPANT
        user.email_verified = False

        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user
class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email address",
                "autocomplete": "email",
            }
        ),
    )

class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile

        fields = [
            "profile_photo",
            "biography",
            "discipline",
            "languages",
            "digital_literacy_level",
            "availability",
            "interests",
            "education",
            "location",
            "skills",
            "visibility",
        ]

        widgets = {
            "profile_photo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),

            "biography": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Tell other participants about yourself..."
                    ),
                }
            ),

            "discipline": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Information Technology",
                }
            ),

            "languages": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: English, Luganda, Swahili"
                    ),
                }
            ),

            "digital_literacy_level": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "availability": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Weekdays, evenings, weekends"
                    ),
                }
            ),

            "interests": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Describe your interests..."
                    ),
                }
            ),

            "education": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Describe your education and qualifications..."
                    ),
                }
            ),

            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Kampala, Uganda"
                    ),
                }
            ),

            "skills": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 6,
                }
            ),

            "visibility": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")

        if photo:
            max_size = 2 * 1024 * 1024

            if photo.size > max_size:
                raise forms.ValidationError(
                    "Profile photograph must not exceed 2 MB."
                )

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            if photo.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Only JPG, PNG and WebP images are allowed."
                )

        return photo