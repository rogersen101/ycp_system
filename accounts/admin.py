from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailVerificationToken, User
from .models import (
    EmailVerificationToken,
    Profile,
    Skill,
    User,
)


@admin.register(User)
class YCPUserAdmin(UserAdmin):
    """
    Administration interface for YCP users.
    """

    # --------------------------------------------------------
    # List page
    # --------------------------------------------------------

    list_display = (
        "email",
        "full_name",
        "role",
        "country",
        "email_verified",
        "is_active",
        "is_staff",
        "created_at",
    )

    list_filter = (
        "role",
        "email_verified",
        "is_active",
        "is_staff",
        "country",
    )

    search_fields = (
        "email",
        "full_name",
        "country",
    )

    ordering = (
        "-created_at",
    )

    # --------------------------------------------------------
    # Detail / Edit page
    # --------------------------------------------------------

    fieldsets = (
        (
            "Account Information",
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "full_name",
                    "date_of_birth",
                    "country",
                )
            },
        ),
        (
            "YCP Role",
            {
                "fields": (
                    "role",
                    "email_verified",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "last_login",
        "date_joined",
        "created_at",
        "updated_at",
    )

    # --------------------------------------------------------
    # Add user page
    # --------------------------------------------------------

    add_fieldsets = (
        (
            "Create YCP User",
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                    "role",
                    "country",
                    "date_of_birth",
                    "email_verified",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )
@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "token",
        "created_at",
        "used_at",
    )

    search_fields = (
        "user__email",
        "user__full_name",
    )

    list_filter = (
        "created_at",
        "used_at",
    )

    readonly_fields = (
        "token",
        "created_at",
        "used_at",
    )

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "discipline",
        "location",
        "digital_literacy_level",
        "visibility",
        "profile_completion",
        "updated_at",
    )

    list_filter = (
        "digital_literacy_level",
        "visibility",
    )

    search_fields = (
        "user__email",
        "user__full_name",
        "discipline",
        "location",
    )

    filter_horizontal = (
        "skills",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "profile_completion",
    )

    fieldsets = (
        (
            "Participant",
            {
                "fields": (
                    "user",
                    "profile_photo",
                )
            },
        ),
        (
            "Profile Information",
            {
                "fields": (
                    "biography",
                    "discipline",
                    "languages",
                    "digital_literacy_level",
                    "availability",
                    "interests",
                    "education",
                    "location",
                )
            },
        ),
        (
            "Skills",
            {
                "fields": (
                    "skills",
                )
            },
        ),
        (
            "Privacy",
            {
                "fields": (
                    "visibility",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "profile_completion",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(
        description="Completion"
    )
    def profile_completion(self, obj):
        return f"{obj.completion_percentage}%"