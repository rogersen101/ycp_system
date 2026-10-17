import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from .storage import PrivateMediaStorage


class Activity(models.Model):

    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class Modality(models.TextChoices):
        ONLINE = "online", "Online"
        IN_PERSON = "in_person", "In Person"
        HYBRID = "hybrid", "Hybrid"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    title = models.CharField(
        max_length=200,
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
    )

    category = models.CharField(
        max_length=100,
        db_index=True,
    )

    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.BEGINNER,
        db_index=True,
    )

    description = models.TextField()

    learning_outcomes = models.TextField(
        help_text=(
            "Describe what participants should "
            "be able to do after completing the activity."
        ),
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    language = models.CharField(
        max_length=100,
        default="English",
        db_index=True,
    )

    modality = models.CharField(
        max_length=20,
        choices=Modality.choices,
        default=Modality.ONLINE,
    )

    location = models.CharField(
        max_length=255,
        blank=True,
    )

    start_date = models.DateTimeField(
        db_index=True,
    )

    end_date = models.DateTimeField()
    withdrawal_deadline = models.DateTimeField(
    blank=True,
    null=True,
    help_text="Last date and time a participant can withdraw. If blank, the activity start date is used."
    )

    capacity = models.PositiveIntegerField(
        default=30,
    )

    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="facilitated_activities",
        limit_choices_to={
            "role": "facilitator",
        },
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    

    class Meta:
        ordering = (
            "-start_date",
        )
        indexes = [
            models.Index(
                fields=["status", "start_date"]
            ),
            models.Index(
                fields=["category", "level"]
            ),
            models.Index(
                fields=["country", "language"]
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
     super().clean()

    # Validate activity dates.
     if (
            self.start_date is not None
        and self.end_date is not None
        and self.end_date <= self.start_date
    ):
        raise ValidationError({
            "end_date": "The activity end date must be after the start date."
        })

    # Validate capacity.
     if self.capacity is not None and self.capacity < 1:
        raise ValidationError({
            "capacity": "Activity capacity must be at least 1."
        })

    # Validate withdrawal deadline only when provided.
     if self.withdrawal_deadline is not None:

        if (
            self.start_date is not None
            and self.withdrawal_deadline > self.start_date
        ):
            raise ValidationError({
                "withdrawal_deadline": (
                    "The withdrawal deadline cannot be after "
                    "the activity start date."
                )
            })

        if (
            self.end_date is not None
            and self.withdrawal_deadline > self.end_date
        ):
            raise ValidationError({
                "withdrawal_deadline": (
                    "The withdrawal deadline cannot be after "
                    "the activity end date."
                )
            })

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def is_archived(self):
        return self.status == self.Status.ARCHIVED

    @property
    def enrolled_count(self):
        return self.enrolments.filter(
            status=Enrolment.Status.ACTIVE
        ).count()

    @property
    def available_spaces(self):
        return max(
            self.capacity - self.enrolled_count,
            0,
        )

    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity

    @property
    def has_started(self):
        return timezone.now() >= self.start_date

    @property
    def has_ended(self):
        return timezone.now() > self.end_date
    @property
    def withdrawal_cutoff(self):
        return self.withdrawal_deadline or self.start_date
    


class Material(models.Model):

    class MaterialType(models.TextChoices):
        TEXT = "text", "Text"
        DOCUMENT = "document", "Document"
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        LINK = "link", "External Link"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="materials",
    )

    title = models.CharField(
        max_length=200,
    )

    material_type = models.CharField(
        max_length=20,
        choices=MaterialType.choices,
        default=MaterialType.TEXT,
    )

    description = models.TextField(
        blank=True,
    )

    content = models.TextField(
        blank=True,
        help_text="Text-first learning content.",
    )

    file = models.FileField(
    upload_to="learning/materials/",
    storage=PrivateMediaStorage(),
    blank=True,
    null=True,
)


    external_url = models.URLField(
        blank=True,
    )

    downloadable = models.BooleanField(
        default=False,
    )

    low_bandwidth = models.BooleanField(
        default=True,
        help_text=(
            "Suitable for low-bandwidth participants."
        ),
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "order",
            "created_at",
        )

    def __str__(self):
        return f"{self.activity.title} - {self.title}"


class Enrolment(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        WITHDRAWN = "withdrawn", "Withdrawn"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrolments",
    )

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="enrolments",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True,
    )

    withdrawn_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = (
            "-enrolled_at",
        )
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "participant",
                    "activity",
                ],
                name="unique_participant_activity",
            )
        ]
        indexes = [
            models.Index(
                fields=[
                    "participant",
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "activity",
                    "status",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.participant.email} - "
            f"{self.activity.title}"
        )


class Attendance(models.Model):

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        EXCUSED = "excused", "Excused"

    enrolment = models.ForeignKey(
        Enrolment,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    notes = models.CharField(
        max_length=500,
        blank=True,
    )

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="attendance_marked",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = (
            "-date",
        )
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "enrolment",
                    "date",
                ],
                name="unique_enrolment_attendance_date",
            )
        ]

    def __str__(self):
        return (
            f"{self.enrolment.participant.full_name} - "
            f"{self.date} - {self.status}"
        )


class DiscussionThread(models.Model):

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="discussion_threads",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_discussions",
    )

    title = models.CharField(
        max_length=200,
    )

    body = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-created_at",
        )

    def __str__(self):
        return self.title
class DiscussionReply(models.Model):
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name="replies",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_discussion_replies",
    )

    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"Reply by {self.author.email} "
            f"to {self.thread.title}"
        )
    
    