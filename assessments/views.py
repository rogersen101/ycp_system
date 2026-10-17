from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from learning.models import Activity
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from learning.models import Activity, Enrolment

from .models import (
    Assessment,
    AssessmentAttempt,
    AnswerOption,
    Question,
    SubmittedAnswer,
)

from .forms import (
    AssessmentForm,
    QuestionForm,
    AnswerOptionFormSet,
)
from .models import Assessment, Question

def can_manage_assessment(user, assessment):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or assessment.activity.facilitator_id == user.pk
        )
    )


def require_assessment_management(user, assessment):
    if not can_manage_assessment(user, assessment):
        raise PermissionDenied(
            "You are not authorized to manage this assessment."
        )
@login_required
def assessment_list(request, slug):
    activity = get_object_or_404(
        Activity.objects.select_related("facilitator"),
        slug=slug,
    )

    if not (
        request.user.is_superuser
        or request.user.is_staff
        or activity.facilitator_id == request.user.pk
    ):
        raise PermissionDenied(
            "You cannot manage assessments for this activity."
        )

    assessments = (
        activity.assessments
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "assessments/assessment_list.html",
        {
            "activity": activity,
            "assessments": assessments,
        },
    )
@login_required
def assessment_create(request, slug):
    activity = get_object_or_404(
        Activity.objects.select_related("facilitator"),
        slug=slug,
    )

    if not (
        request.user.is_superuser
        or request.user.is_staff
        or activity.facilitator_id == request.user.pk
    ):
        raise PermissionDenied(
            "You cannot create assessments for this activity."
        )

    if request.method == "POST":
        form = AssessmentForm(request.POST)

        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.activity = activity
            assessment.created_by = request.user
            assessment.status = Assessment.Status.DRAFT
            assessment.save()

            messages.success(
                request,
                "Assessment created as a draft. Add questions before publishing.",
            )

            return redirect(
                "assessments:question_manage",
                assessment_id=assessment.pk,
            )
    else:
        form = AssessmentForm()

    return render(
        request,
        "assessments/assessment_form.html",
        {
            "form": form,
            "activity": activity,
            "page_title": "Create Assessment",
        },
    )
@login_required
def assessment_edit(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=assessment_id,
    )

    require_assessment_management(request.user, assessment)

    if assessment.status != Assessment.Status.DRAFT:
        messages.error(
            request,
            "Only draft assessments can be edited. Close or review published assessments separately.",
        )
        return redirect(
            "assessments:assessment_list",
            slug=assessment.activity.slug,
        )

    if request.method == "POST":
        form = AssessmentForm(
            request.POST,
            instance=assessment,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Assessment updated successfully.",
            )

            return redirect(
                "assessments:question_manage",
                assessment_id=assessment.pk,
            )
    else:
        form = AssessmentForm(instance=assessment)

    return render(
        request,
        "assessments/assessment_form.html",
        {
            "form": form,
            "activity": assessment.activity,
            "assessment": assessment,
            "page_title": "Edit Assessment",
        },
    )
@login_required
def question_manage(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=assessment_id,
    )

    require_assessment_management(request.user, assessment)

    if assessment.status != Assessment.Status.DRAFT:
        messages.error(
            request,
            "Questions can only be changed while the assessment is a draft.",
        )
        return redirect(
            "assessments:assessment_list",
            slug=assessment.activity.slug,
        )

    question_form = QuestionForm()
    option_formset = AnswerOptionFormSet(
        instance=Question(),
        prefix="options",
    )

    if request.method == "POST":
        question_form = QuestionForm(request.POST)

        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.assessment = assessment

            option_formset = AnswerOptionFormSet(
                request.POST,
                instance=question,
                prefix="options",
            )

            if option_formset.is_valid():
                option_data = [
                    item
                    for item in option_formset.cleaned_data
                    if item and not item.get("DELETE", False)
                ]

                question_type = question.question_type

                if question_type in {
                    Question.QuestionType.MCQ,
                    Question.QuestionType.TRUE_FALSE,
                }:
                    if len(option_data) < 2:
                        option_formset._non_form_errors = (
                            option_formset.error_class([
                                "Provide at least two answer options."
                            ])
                        )
                    elif sum(
                        bool(item.get("is_correct"))
                        for item in option_data
                    ) != 1:
                        option_formset._non_form_errors = (
                            option_formset.error_class([
                                "Select exactly one correct answer."
                            ])
                        )
                    else:
                        with transaction.atomic():
                            question.save()
                            option_formset.instance = question
                            option_formset.save()

                        messages.success(
                            request,
                            "Question and answer options saved.",
                        )

                        return redirect(
                            "assessments:question_manage",
                            assessment_id=assessment.pk,
                        )
                else:
                    with transaction.atomic():
                        question.save()
                        option_formset.instance = question
                        option_formset.save()

                    messages.success(
                        request,
                        "Question saved successfully.",
                    )

                    return redirect(
                        "assessments:question_manage",
                        assessment_id=assessment.pk,
                    )

    questions = assessment.questions.prefetch_related("options")

    return render(
        request,
        "assessments/question_manage.html",
        {
            "assessment": assessment,
            "question_form": question_form,
            "option_formset": option_formset,
            "questions": questions,
        },
    )

@login_required
@require_POST
def assessment_publish(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=assessment_id,
    )

    require_assessment_management(request.user, assessment)

    if assessment.status != Assessment.Status.DRAFT:
        messages.error(
            request,
            "Only draft assessments can be published.",
        )
        return redirect(
            "assessments:assessment_list",
            slug=assessment.activity.slug,
        )

    questions = list(assessment.questions.prefetch_related("options"))

    if not questions:
        messages.error(
            request,
            "Add at least one question before publishing.",
        )
        return redirect(
            "assessments:question_manage",
            assessment_id=assessment.pk,
        )

    for question in questions:
        if question.question_type in {
            Question.QuestionType.MCQ,
            Question.QuestionType.TRUE_FALSE,
        }:
            options = list(question.options.all())

            if len(options) < 2 or sum(
                option.is_correct for option in options
            ) != 1:
                messages.error(
                    request,
                    f"Question '{question.text[:60]}' must have at least "
                    "two options and exactly one correct answer.",
                )
                return redirect(
                    "assessments:question_manage",
                    assessment_id=assessment.pk,
                )

    assessment.status = Assessment.Status.PUBLISHED
    assessment.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        "Assessment published successfully.",
    )

    return redirect(
        "assessments:assessment_list",
        slug=assessment.activity.slug,
    )
@login_required
@require_POST
def assessment_close(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=assessment_id,
    )

    require_assessment_management(request.user, assessment)

    if assessment.status != Assessment.Status.PUBLISHED:
        messages.error(
            request,
            "Only published assessments can be closed.",
        )
    else:
        assessment.status = Assessment.Status.CLOSED
        assessment.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            "Assessment closed. New attempts should no longer be allowed.",
        )

    return redirect(
        "assessments:assessment_list",
        slug=assessment.activity.slug,
    )
@login_required
def participant_assessment_dashboard(request):
    """Show published assessments for activities this participant is enrolled in."""
    if getattr(request.user, "role", "") not in ("participant", "team_lead"):
        raise Http404("Assessment page not found.")

    active_activity_ids = Enrolment.objects.filter(
        participant=request.user,
        status=Enrolment.Status.ACTIVE,
        activity__status=Activity.Status.PUBLISHED,
    ).values_list("activity_id", flat=True)

    assessments = list(
        Assessment.objects.filter(
            activity_id__in=active_activity_ids,
            activity__status=Activity.Status.PUBLISHED,
            status=Assessment.Status.PUBLISHED,
        ).select_related("activity").order_by("created_at")
    )

    now = timezone.now()
    for assessment in assessments:
        attempts = assessment.attempts.filter(
            participant=request.user
        ).order_by("-attempt_number")
        assessment.latest_attempt = attempts.first()
        assessment.attempts_used = attempts.count()

        if assessment.available_from and now < assessment.available_from:
            assessment.availability_message = "Not open yet"
            assessment.can_start = False
        elif assessment.available_until and now >= assessment.available_until:
            assessment.availability_message = "Assessment closed"
            assessment.can_start = False
        elif assessment.activity.has_ended:
            assessment.availability_message = "Activity ended"
            assessment.can_start = False
        elif assessment.attempts_used >= assessment.max_attempts:
            assessment.availability_message = "No attempts remaining"
            assessment.can_start = False
        else:
            assessment.availability_message = ""
            assessment.can_start = True

        # Existing attempts must remain resumable even if the maximum count is reached.
        if (assessment.latest_attempt and
                assessment.latest_attempt.status == AssessmentAttempt.Status.IN_PROGRESS):
            assessment.can_start = True

    return render(
        request,
        "assessments/participant_assessment_dashboard.html",
        {"assessments": assessments},
    )


def get_participant_assessment_or_404(user, assessment_id):
    """
    Return an assessment only when the user is enrolled in its activity.
    Facilitators and administrators should use their management views.
    """
    assessment = get_object_or_404(
        Assessment.objects.select_related("activity"),
        pk=assessment_id,
        status=Assessment.Status.PUBLISHED,
    )

    if user.is_staff or user.is_superuser:
        raise Http404("Assessment not found.")

    # Only participant and team-lead accounts may take assessments.
    if getattr(user, "role", "") not in ("participant", "team_lead"):
        raise Http404("Assessment not found.")

    if not assessment.activity.is_published:
        raise Http404("Assessment not found.")

    enrolment_exists = Enrolment.objects.filter(
        participant=user,
        activity=assessment.activity,
        status=Enrolment.Status.ACTIVE,
    ).exists()

    if not enrolment_exists:
        raise Http404("Assessment not found.")

    return assessment


def assessment_availability_error(assessment, now=None):
    """Return a user-friendly error when an assessment cannot be taken."""
    now = now or timezone.now()

    if assessment.status != Assessment.Status.PUBLISHED:
        return "This assessment is not published."

    if (
        assessment.available_from
        and now < assessment.available_from
    ):
        return "This assessment is not available yet."

    if (
        assessment.available_until
        and now > assessment.available_until
    ):
        return "The assessment closing time has passed."

    if assessment.activity.has_ended:
        return "This learning activity has ended."

    return None


@login_required
def participant_assessment_list(request, slug):
    """List published assessments for an enrolled participant."""
    activity = get_object_or_404(Activity, slug=slug)

    if not activity.is_published:
            raise Http404("Activity not found.")
    

    if request.user.is_staff or request.user.is_superuser:
        raise Http404("Activity not found.")

    if getattr(request.user, "role", "") not in (
        "participant",
        "team_lead",
    ):
        raise Http404("Activity not found.")

    enrolled = Enrolment.objects.filter(
        participant=request.user,
        activity=activity,
        status=Enrolment.Status.ACTIVE,
    ).exists()

    if not enrolled:
        raise Http404("Activity not found.")

    assessments = Assessment.objects.filter(
        activity=activity,
        status=Assessment.Status.PUBLISHED,
    ).order_by("created_at")

    return render(
        request,
        "assessments/participant_assessment_list.html",
        {
            "activity": activity,
            "assessments": assessments,
        },
    )


@login_required
def assessment_start(request, assessment_id):
    """Start an attempt, or reopen the participant's existing attempt."""
    assessment = get_participant_assessment_or_404(
        request.user,
        assessment_id,
    )

    error = assessment_availability_error(assessment)
    if error:
        messages.error(request, error)
        return redirect(
            "assessments:participant_assessment_list",
            slug=assessment.activity.slug,
        )

    if not assessment.questions.exists():
        messages.error(
            request,
            "This assessment has no questions yet.",
        )
        return redirect(
            "assessments:participant_assessment_list",
            slug=assessment.activity.slug,
        )

    with transaction.atomic():
        # Serialize attempt creation for this assessment as far as the
        # database backend supports row-level locking.
        locked_assessment = Assessment.objects.select_for_update().get(
            pk=assessment.pk
        )

        existing_attempt = (
            AssessmentAttempt.objects.filter(
                assessment=locked_assessment,
                participant=request.user,
                status=AssessmentAttempt.Status.IN_PROGRESS,
            )
            .order_by("-attempt_number")
            .first()
        )

        if existing_attempt:
            attempt = existing_attempt
        else:
            attempt_count = AssessmentAttempt.objects.filter(
                assessment=locked_assessment,
                participant=request.user,
            ).count()

            if attempt_count >= locked_assessment.max_attempts:
                messages.error(
                    request,
                    "You have used all your attempts for this assessment.",
                )
                return redirect(
                    "assessments:participant_assessment_list",
                    slug=locked_assessment.activity.slug,
                )

            attempt = AssessmentAttempt.objects.create(
                assessment=locked_assessment,
                participant=request.user,
                attempt_number=attempt_count + 1,
                status=AssessmentAttempt.Status.IN_PROGRESS,
                started_at=timezone.now(),
            )

    return redirect(
        "assessments:assessment_take",
        attempt_id=attempt.pk,
    )


@login_required
def assessment_take(request, attempt_id):
    """Display an in-progress assessment without exposing correct answers."""
    attempt = get_object_or_404(
        AssessmentAttempt.objects.select_related(
            "assessment",
            "assessment__activity",
        ),
        pk=attempt_id,
        participant=request.user,
        status=AssessmentAttempt.Status.IN_PROGRESS,
    )

    assessment = get_participant_assessment_or_404(
        request.user,
        attempt.assessment_id,
    )

    now = timezone.now()

    # Enforce the time limit on the server, not just with JavaScript.
    if (
        assessment.time_limit_minutes
        and now >= attempt.started_at
        + timedelta(minutes=assessment.time_limit_minutes)
    ):
        messages.warning(
            request,
            "Your assessment time has expired. Submit your answers now.",
        )

    questions = assessment.questions.prefetch_related(
        "options"
    ).order_by("order", "id")

    if request.method == "POST":
        error = assessment_availability_error(assessment, now)
        # Once started, allow submission after the closing time only if
        # you later choose to support grace-period submissions.
        if error and "closing time" not in error.lower():
            messages.error(request, error)
            return redirect(
                "assessments:participant_assessment_list",
                slug=assessment.activity.slug,
            )

        deadline = (
            attempt.started_at
            + timedelta(minutes=assessment.time_limit_minutes)
            if assessment.time_limit_minutes
            else None
        )

        if deadline and now > deadline:
            messages.error(
                request,
                "The time limit has expired. Your answers were not accepted. "
                "Please contact the facilitator if you need assistance.",
            )
            return redirect(
                "assessments:participant_assessment_list",
                slug=assessment.activity.slug,
            )

        with transaction.atomic():
            locked_attempt = AssessmentAttempt.objects.select_for_update().get(
                pk=attempt.pk,
                participant=request.user,
                status=AssessmentAttempt.Status.IN_PROGRESS,
            )

            score = 0
            total_marks = 0
            needs_manual_grading = False

            for question in questions:
                field_name = f"question_{question.pk}"
                raw_answer = request.POST.get(field_name, "").strip()

                selected_option = None
                text_answer = ""

                if question.question_type in (
                    Question.QuestionType.MCQ,
                    Question.QuestionType.TRUE_FALSE,
                ):
                    if raw_answer:
                        selected_option = AnswerOption.objects.filter(
                            pk=raw_answer,
                            question=question,
                        ).first()

                        if selected_option is None:
                            messages.error(
                                request,
                                "An answer was invalid. Please review your "
                                "responses and try again.",
                            )
                            return redirect(
                                "assessments:assessment_take",
                                attempt_id=attempt.pk,
                            )

                else:
                    text_answer = raw_answer
                    needs_manual_grading = True

                answer, _ = SubmittedAnswer.objects.update_or_create(
                    attempt=locked_attempt,
                    question=question,
                    defaults={
                        "selected_option": selected_option,
                        "text_answer": text_answer,
                        "awarded_marks": 0,
                    },
                )

                total_marks += question.marks

                if question.question_type in (
                    Question.QuestionType.MCQ,
                    Question.QuestionType.TRUE_FALSE,
                ):
                    if selected_option and selected_option.is_correct:
                        answer.awarded_marks = question.marks
                        answer.save(update_fields=["awarded_marks"])
                        score += question.marks

            locked_attempt.status = (
                AssessmentAttempt.Status.SUBMITTED
            )
            locked_attempt.submitted_at = timezone.now()
            locked_attempt.score = score
            locked_attempt.total_marks = total_marks

            # A score/percentage is final only when all questions are
            # automatically gradable. Written answers need manual grading.
            if not needs_manual_grading:
                locked_attempt.percentage = (
                    (score / total_marks) * 100
                    if total_marks
                    else 0
                )
                locked_attempt.passed = (
                    locked_attempt.percentage >= assessment.pass_mark
                )

            locked_attempt.save()

        messages.success(
            request,
            "Your assessment has been submitted successfully.",
        )
        return redirect(
            "assessments:assessment_result",
            attempt_id=attempt.pk,
        )

    return render(
        request,
        "assessments/participant_assessment_take.html",
        {
            "attempt": attempt,
            "assessment": assessment,
            "questions": questions,
            "deadline": (
                attempt.started_at
                + timedelta(minutes=assessment.time_limit_minutes)
                if assessment.time_limit_minutes
                else None
            ),
        },
    )


@login_required
def assessment_result(request, attempt_id):
    attempt = get_object_or_404(
        AssessmentAttempt.objects.select_related(
            "assessment",
            "participant",
        ),
        id=attempt_id,
        participant=request.user,
        status__in=[
            AssessmentAttempt.Status.SUBMITTED,
            AssessmentAttempt.Status.GRADED,
        ],
    )

    return render(
        request,
        "assessments/assessment_result.html",
        {"attempt": attempt},
    )