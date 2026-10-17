from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Activity, Enrolment


@transaction.atomic
def enrol_participant(*, participant, activity):
    """
    Enrol a participant in an activity.

    Returns:
        tuple[Enrolment, bool]
        The enrolment object and whether a new enrolment was created.
    """

    # Lock the activity row during the transaction.
    activity = (
        Activity.objects
        .select_for_update()
        .get(pk=activity.pk)
    )

    # Only published activities can accept enrolments.
    if activity.status != Activity.Status.PUBLISHED:
        raise ValidationError(
            "This activity is not currently open for enrolment."
        )

    # Participants cannot enrol in activities that have already ended.
    if activity.has_ended:
        raise ValidationError(
            "This activity has already ended."
        )

    # Check whether this participant already has an enrolment.
    enrolment = (
        Enrolment.objects
        .select_for_update()
        .filter(
            participant=participant,
            activity=activity,
        )
        .first()
    )

    # Prevent duplicate active enrolment.
    if enrolment and enrolment.status == Enrolment.Status.ACTIVE:
        raise ValidationError(
            "You are already enrolled in this activity."
        )

    # A completed activity cannot be re-enrolled.
    if enrolment and enrolment.status == Enrolment.Status.COMPLETED:
        raise ValidationError(
            "You have already completed this activity."
        )

    # Check capacity after obtaining the activity lock.
    active_enrolments = (
        Enrolment.objects
        .filter(
            activity=activity,
            status=Enrolment.Status.ACTIVE,
        )
        .count()
    )

    if active_enrolments >= activity.capacity:
        raise ValidationError(
            "This activity is currently full."
        )

    # Reactivate an existing withdrawn enrolment.
    if enrolment and enrolment.status == Enrolment.Status.WITHDRAWN:
        enrolment.status = Enrolment.Status.ACTIVE
        enrolment.withdrawn_at = None
        enrolment.completed_at = None

        enrolment.save(
            update_fields=[
                "status",
                "withdrawn_at",
                "completed_at",
            ]
        )

        return enrolment, False

    # Create a new enrolment.
    enrolment = Enrolment.objects.create(
        participant=participant,
        activity=activity,
        status=Enrolment.Status.ACTIVE,
    )

    return enrolment, True


@transaction.atomic
def withdraw_participant(*, participant, activity):
    """
    Withdraw a participant from an activity.

    Returns:
        Enrolment
    """

    activity = (
        Activity.objects
        .select_for_update()
        .get(pk=activity.pk)
    )

    enrolment = (
        Enrolment.objects
        .select_for_update()
        .filter(
            participant=participant,
            activity=activity,
        )
        .first()
    )

    if not enrolment:
        raise ValidationError(
            "You are not enrolled in this activity."
        )

    if enrolment.status != Enrolment.Status.ACTIVE:
        raise ValidationError(
            "Only an active enrolment can be withdrawn."
        )

    now = timezone.now()

    if now >= activity.withdrawal_cutoff:
        raise ValidationError(
            "The withdrawal deadline for this activity has passed."
        )

    enrolment.status = Enrolment.Status.WITHDRAWN
    enrolment.withdrawn_at = now

    enrolment.save(
        update_fields=[
            "status",
            "withdrawn_at",
        ]
    )

    return enrolment