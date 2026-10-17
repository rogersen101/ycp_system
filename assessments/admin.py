from django.contrib import admin

from .models import (
    AnswerOption,
    Assessment,
    AssessmentAttempt,
    Question,
    SubmittedAnswer,
)


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "activity",
        "status",
        "pass_mark",
        "max_attempts",
        "created_by",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("title", "activity__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "assessment",
        "question_type",
        "marks",
        "order",
    )

    list_filter = ("question_type",)
    search_fields = ("text", "assessment__title")
    inlines = [AnswerOptionInline]


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "question",
        "is_correct",
        "order",
    )

    list_filter = ("is_correct",)


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "assessment",
        "participant",
        "attempt_number",
        "status",
        "score",
        "percentage",
        "passed",
    )

    list_filter = ("status", "passed")
    search_fields = (
        "assessment__title",
        "participant__email",
    )

    readonly_fields = (
        "started_at",
        "submitted_at",
        "score",
        "total_marks",
        "percentage",
        "passed",
    )


@admin.register(SubmittedAnswer)
class SubmittedAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "attempt",
        "question",
        "selected_option",
        "awarded_marks",
        "graded_at",
    )

    readonly_fields = ("graded_at",)