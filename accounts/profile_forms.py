from django import forms

from .models import Profile, Skill


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