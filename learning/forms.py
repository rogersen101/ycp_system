from django import forms

from .models import Activity, DiscussionThread, Material, DiscussionReply


class ActivityForm(forms.ModelForm):

    class Meta:
        model = Activity

        fields = [
            "title",
            "slug",
            "category",
            "level",
            "description",
            "learning_outcomes",
            "country",
            "language",
            "modality",
            "location",
            "start_date",
            "end_date",
            "capacity",
            "facilitator",
            "status",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter activity title",
                }
            ),

            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "activity-slug",
                }
            ),

            "category": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Digital Skills"
                    ),
                }
            ),

            "level": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": (
                        "Describe the learning activity..."
                    ),
                }
            ),

            "learning_outcomes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "What will participants learn?"
                    ),
                }
            ),

            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Uganda",
                }
            ),

            "language": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: English",
                }
            ),

            "modality": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Physical location or online platform"
                    ),
                }
            ),

            "start_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),

            "end_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),

            "capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "facilitator": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")

        if capacity is None:
            return capacity

        if capacity < 1:
            raise forms.ValidationError(
                "Activity capacity must be at least 1."
            )

        return capacity

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:

            if end_date <= start_date:
                raise forms.ValidationError(
                    "The activity end date must be after "
                    "the start date."
                )

        return cleaned_data


class MaterialForm(forms.ModelForm):

    class Meta:
        model = Material

        fields = [
            "title",
            "material_type",
            "description",
            "content",
            "file",
            "external_url",
            "downloadable",
            "low_bandwidth",
            "order",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Material title",
                }
            ),

            "material_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Brief description of the material"
                    ),
                }
            ),

            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": (
                        "Enter text-first learning content..."
                    ),
                }
            ),

            "file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "external_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "https://example.com/resource"
                    ),
                }
            ),

            "downloadable": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "low_bandwidth": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        material_type = cleaned_data.get(
            "material_type"
        )

        content = cleaned_data.get("content")
        file = cleaned_data.get("file")
        external_url = cleaned_data.get(
            "external_url"
        )

        if material_type == Material.MaterialType.TEXT:
            if not content:
                self.add_error(
                    "content",
                    "Text materials must contain content.",
                )

        if material_type == Material.MaterialType.DOCUMENT:
            if not file:
                self.add_error(
                    "file",
                    "Please upload a document.",
                )

        if material_type == Material.MaterialType.IMAGE:
            if not file:
                self.add_error(
                    "file",
                    "Please upload an image.",
                )

        if material_type == Material.MaterialType.VIDEO:
            if not file and not external_url:
                self.add_error(
                    "file",
                    "Please upload a video or provide "
                    "an external video URL.",
                )

        if material_type == Material.MaterialType.LINK:
            if not external_url:
                self.add_error(
                    "external_url",
                    "Please provide the external URL.",
                )

        return cleaned_data
    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if not uploaded_file:
            return uploaded_file

    # Maximum upload size: 10 MB.
        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "The file must not exceed 10 MB."
            )

        allowed_types = {
            ".pdf": {"application/pdf"},
            ".png": {"image/png"},
            ".jpg": {"image/jpeg"},
            ".jpeg": {"image/jpeg"},
            ".webp": {"image/webp"},
            ".mp4": {"video/mp4"},
            ".txt": {"text/plain"},
            ".docx": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            },
        }

        import os

        extension = os.path.splitext(uploaded_file.name)[1].lower()
        allowed_mime_types = allowed_types.get(extension)

        if not allowed_mime_types:
            raise forms.ValidationError(
                "Unsupported file type. Allowed: PDF, PNG, JPG, WebP, "
                "MP4, TXT and DOCX."
            )

        if uploaded_file.content_type not in allowed_mime_types:
            raise forms.ValidationError(
                "The file type does not match its filename."
            )

        return uploaded_file


class DiscussionThreadForm(
    forms.ModelForm
):

    class Meta:
        model = DiscussionThread

        fields = [
            "title",
            "body",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Discussion title"
                    ),
                }
            ),

            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": (
                        "Start the discussion..."
                    ),
                }
            ),
        }

class DiscussionReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = ["body"]

        widgets = {
            "body": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Write your reply...",
            }),
        }