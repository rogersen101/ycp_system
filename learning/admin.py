from django.contrib import admin

from .models import (
    Activity,
    Attendance,
    DiscussionThread,
    Enrolment,
    Material,
    DiscussionReply,
)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "category",
        "level",
        "modality",
        "facilitator",
        "start_date",
        "capacity",
        "enrolled_count_display",
        "status",
    )

    list_filter = (
        "status",
        "level",
        "modality",
        "category",
        "country",
        "language",
    )

    search_fields = (
        "title",
        "category",
        "description",
        "country",
        "language",
        "facilitator__email",
        "facilitator__full_name",
    )

    prepopulated_fields = {
        "slug": ("title",)
    }

    readonly_fields = (
        "created_at",
        "updated_at",
        "enrolled_count_display",
        "available_spaces_display",
    )

    fieldsets = (
        (
            "Activity Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "level",
                    "description",
                    "learning_outcomes",
                )
            },
        ),
        (
            "Location & Delivery",
            {
                "fields": (
                    "country",
                    "language",
                    "modality",
                    "location",
                )
            },
        ),
        (
            "Schedule & Capacity",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "capacity",
                    "enrolled_count_display",
                    "available_spaces_display",
                )
            },
        ),
        (
            "Management",
            {
                "fields": (
                    "facilitator",
                    "status",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(
        description="Enrolled"
    )
    def enrolled_count_display(self, obj):
        return obj.enrolled_count

    @admin.display(
        description="Available Spaces"
    )
    def available_spaces_display(self, obj):
        return obj.available_spaces


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "activity",
        "material_type",
        "low_bandwidth",
        "downloadable",
        "order",
    )

    list_filter = (
        "material_type",
        "low_bandwidth",
        "downloadable",
    )

    search_fields = (
        "title",
        "description",
        "activity__title",
    )

    ordering = (
        "activity",
        "order",
    )


@admin.register(Enrolment)
class EnrolmentAdmin(admin.ModelAdmin):

    list_display = (
        "participant",
        "activity",
        "status",
        "enrolled_at",
        "withdrawn_at",
        "completed_at",
    )

    list_filter = (
        "status",
        "activity",
    )

    search_fields = (
        "participant__email",
        "participant__full_name",
        "activity__title",
    )

    readonly_fields = (
        "enrolled_at",
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "enrolment",
        "date",
        "status",
        "marked_by",
        "created_at",
    )

    list_filter = (
        "status",
        "date",
    )

    search_fields = (
        "enrolment__participant__email",
        "enrolment__participant__full_name",
        "enrolment__activity__title",
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "activity",
        "author",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "body",
        "activity__title",
        "author__email",
        "author__full_name",
    )

    list_filter = (
        "activity",
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = (
        "thread",
        "author",
        "created_at",
    )

    search_fields = (
        "thread__title",
        "author__email",
        "body",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )