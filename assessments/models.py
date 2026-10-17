import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Assessment(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    activity = models.ForeignKey(
        "learning.Activity",
        on_delete=models.CASCADE,
        related_name="assessments",
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    instructions = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    pass_mark = models.PositiveSmallIntegerField(default=50)

    time_limit_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Leave blank for an untimed assessment.",
    )

    max_attempts = models.PositiveIntegerField(default=1)

    available_from = models.DateTimeField(
        blank=True,
        null=True,
    )

    available_until = models.DateTimeField(
        blank=True,
        null=True,
    )

    show_results_immediately = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assessments",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if self.pass_mark > 100:
            raise ValidationError({
                "pass_mark": "Pass mark must not exceed 100."
            })

        if self.max_attempts < 1:
            raise ValidationError({
                "max_attempts": "At least one attempt is required."
            })

        if self.available_from and self.available_until:
            if self.available_until <= self.available_from:
                raise ValidationError({
                    "available_until": (
                        "The closing date must be after the opening date."
                    )
                })

    @property
    def is_available(self):
        now = timezone.now()

        if self.status != self.Status.PUBLISHED:
            return False

        if self.available_from and now < self.available_from:
            return False

        if self.available_until and now >= self.available_until:
            return False

        return True


class Question(models.Model):

    class QuestionType(models.TextChoices):
        MCQ = "mcq", "Multiple Choice"
        TRUE_FALSE = "true_false", "True or False"
        SHORT_ANSWER = "short_answer", "Short Answer"
        ESSAY = "essay", "Essay"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    text = models.TextField()

    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )

    marks = models.PositiveIntegerField(default=1)

    order = models.PositiveIntegerField(default=0)

    explanation = models.TextField(
        blank=True,
        help_text="Optional explanation shown after grading.",
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.assessment.title}: {self.text[:70]}"

    def clean(self):
        super().clean()

        if self.marks < 1:
            raise ValidationError({
                "marks": "A question must have at least one mark."
            })


class AnswerOption(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )

    text = models.CharField(max_length=500)

    is_correct = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class AssessmentAttempt(models.Model):

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
    )

    attempt_number = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        db_index=True,
    )

    started_at = models.DateTimeField(auto_now_add=True)

    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )

    total_marks = models.PositiveIntegerField(default=0)

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )

    passed = models.BooleanField(
        blank=True,
        null=True,
    )

    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment",
                    "participant",
                    "attempt_number",
                ],
                name="unique_assessment_participant_attempt",
            )
        ]

    def __str__(self):
        return (
            f"{self.participant.email} - "
            f"{self.assessment.title} - "
            f"Attempt {self.attempt_number}"
        )


class SubmittedAnswer(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="submitted_answers",
    )

    selected_option = models.ForeignKey(
        AnswerOption,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="selections",
    )

    text_answer = models.TextField(blank=True)

    awarded_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )

    marker_feedback = models.TextField(blank=True)

    graded_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_attempt_question_answer",
            )
        ]

    def __str__(self):
        return (
            f"Answer: {self.attempt_id} - "
            f"{self.question_id}"
        )