import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Superuser must have is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "Superuser must have is_superuser=True."
            )

        return self.create_user(
            email=email,
            password=password,
            **extra_fields
        )


class User(AbstractUser):

    class Role(models.TextChoices):
        PARTICIPANT = "participant", "Participant"
        TEAM_LEAD = "team_lead", "Team Lead"
        FACILITATOR = "facilitator", "Facilitator"
        MENTOR = "mentor", "Mentor"
        STAKEHOLDER = "stakeholder", "Stakeholder / Validator"
        ADMIN = "admin", "Administrator"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    username = None

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    full_name = models.CharField(
        max_length=150
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PARTICIPANT,
        db_index=True,
    )

    country = models.CharField(
        max_length=100,
        blank=True,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    email_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "full_name"
    ]

    objects = UserManager()

    def __str__(self):
        return self.email


class EmailVerificationToken(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = (
            "-created_at",
        )

    def is_expired(self):
        return timezone.now() > (
            self.created_at + timedelta(hours=24)
        )

    def is_valid(self):
        return (
            self.used_at is None
            and not self.is_expired()
        )

    def mark_used(self):
        self.used_at = timezone.now()

        self.save(
            update_fields=[
                "used_at"
            ]
        )

    def __str__(self):
        return (
            f"Email verification for "
            f"{self.user.email}"
        )


class Skill(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = (
            "name",
        )

    def __str__(self):
        return self.name


class Profile(models.Model):

    class DigitalLiteracyLevel(models.TextChoices):
        BEGINNER = (
            "beginner",
            "Beginner"
        )

        INTERMEDIATE = (
            "intermediate",
            "Intermediate"
        )

        ADVANCED = (
            "advanced",
            "Advanced"
        )

    class Visibility(models.TextChoices):
        TEAMMATES = (
            "teammates",
            "Teammates Only"
        )

        EVERYONE = (
            "everyone",
            "Everyone"
        )

        PRIVATE = (
            "private",
            "Private"
        )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    profile_photo = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    biography = models.TextField(
        blank=True,
        max_length=2000,
    )

    discipline = models.CharField(
        max_length=150,
        blank=True,
    )

    languages = models.CharField(
        max_length=500,
        blank=True,
        help_text=(
            "Example: English, Luganda, Swahili"
        ),
    )

    digital_literacy_level = models.CharField(
        max_length=20,
        choices=DigitalLiteracyLevel.choices,
        blank=True,
    )

    availability = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Example: Weekdays, evenings, weekends"
        ),
    )

    interests = models.TextField(
        blank=True,
        max_length=1000,
    )

    education = models.TextField(
        blank=True,
        max_length=1500,
        help_text=(
            "Describe your education and qualifications."
        ),
    )

    location = models.CharField(
        max_length=150,
        blank=True,
    )

    skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="profiles",
    )

    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.TEAMMATES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = (
            "user__full_name",
        )

    def __str__(self):
        return (
            f"{self.user.full_name} Profile"
        )

    @property
    def completion_percentage(self):

        fields = [
            self.user.full_name,
            self.user.email,
            self.user.country,
            self.user.date_of_birth,
            self.biography,
            self.discipline,
            self.languages,
            self.digital_literacy_level,
            self.availability,
            self.interests,
            self.education,
            self.location,
            self.profile_photo,
        ]

        completed = sum(
            1
            for field in fields
            if field
        )

        return round(
            (completed / len(fields)) * 100
        )