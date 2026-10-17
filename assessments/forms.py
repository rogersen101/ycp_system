from django import forms
from django.forms import inlineformset_factory

from .models import (
    AnswerOption,
    Assessment,
    Question,
)


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = [
            "title",
            "description",
            "instructions",
            "pass_mark",
            "time_limit_minutes",
            "max_attempts",
            "available_from",
            "available_until",
            "show_results_immediately",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "instructions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
            }),
            "pass_mark": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "max": 100,
            }),
            "time_limit_minutes": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
            }),
            "max_attempts": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
            }),
            "available_from": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "available_until": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "show_results_immediately": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_pass_mark(self):
        value = self.cleaned_data["pass_mark"]

        if not 0 <= value <= 100:
            raise forms.ValidationError(
                "Pass mark must be between 0 and 100."
            )

        return value

    def clean_max_attempts(self):
        value = self.cleaned_data["max_attempts"]

        if value < 1:
            raise forms.ValidationError(
                "Allow at least one attempt."
            )

        return value

    def clean_time_limit_minutes(self):
        value = self.cleaned_data.get("time_limit_minutes")

        if value is not None and value < 1:
            raise forms.ValidationError(
                "Time limit must be at least one minute."
            )

        return value


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            "text",
            "question_type",
            "marks",
            "order",
            "explanation",
        ]

        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "question_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
            }),
            "explanation": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
            }),
        }

    def clean_marks(self):
        marks = self.cleaned_data["marks"]

        if marks < 1:
            raise forms.ValidationError(
                "Each question must have at least one mark."
            )

        return marks


class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = [
            "text",
            "is_correct",
            "order",
        ]

        widgets = {
            "text": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "is_correct": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
            }),
        }


AnswerOptionFormSet = inlineformset_factory(
    Question,
    AnswerOption,
    form=AnswerOptionForm,
    extra=4,
    min_num=2,
    validate_min=True,
    can_delete=True,
)