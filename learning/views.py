from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render,redirect

from .models import Activity, Enrolment,Material
from django.contrib import messages
from django.core.exceptions import ValidationError,PermissionDenied
from django.utils import timezone
from .forms import DiscussionReplyForm, DiscussionThreadForm, MaterialForm
from .models import ( Activity,DiscussionReply,DiscussionThread,Enrolment,Material,)
from django.http import FileResponse, Http404
from pathlib import Path
from django.views.decorators.http import require_POST

from .forms import MaterialForm

from .services import enrol_participant, withdraw_participant

def can_access_activity(user, activity):
    """
    Allow access to enrolled participants, the activity facilitator,
    and authorized staff.
    """

    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    if activity.facilitator_id == user.pk:
        return True

    return Enrolment.objects.filter(
        participant=user,
        activity=activity,
        status__in=[
            Enrolment.Status.ACTIVE,
            Enrolment.Status.COMPLETED,
        ],
    ).exists()

def can_access_activity(user, activity):
    """
    Allow access to enrolled participants, the activity facilitator,
    and authorized staff.
    """

    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    if activity.facilitator_id == user.pk:
        return True

    return Enrolment.objects.filter(
        participant=user,
        activity=activity,
        status__in=[
            Enrolment.Status.ACTIVE,
            Enrolment.Status.COMPLETED,
        ],
    ).exists()

@login_required
def activity_list(request):
    """
    Participant activity catalogue.

    Only published activities are displayed.
    Supports searching and filtering.
    """

    activities = (
        Activity.objects
        .filter(status=Activity.Status.PUBLISHED)
        .select_related("facilitator")
        .prefetch_related("materials")
    )

    # Search
    query = request.GET.get("q", "").strip()

    if query:
        activities = activities.filter(
            Q(title__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query)
            | Q(learning_outcomes__icontains=query)
            | Q(country__icontains=query)
            | Q(language__icontains=query)
        )

    # Filters
    category = request.GET.get("category", "").strip()
    level = request.GET.get("level", "").strip()
    country = request.GET.get("country", "").strip()
    language = request.GET.get("language", "").strip()
    modality = request.GET.get("modality", "").strip()

    if category:
        activities = activities.filter(category=category)

    if level:
        activities = activities.filter(level=level)

    if country:
        activities = activities.filter(country=country)

    if language:
        activities = activities.filter(language=language)

    if modality:
        activities = activities.filter(modality=modality)

    # Remove duplicate rows and order
    activities = activities.distinct().order_by("start_date")

    # Filter options
    published_activities = Activity.objects.filter(
        status=Activity.Status.PUBLISHED
    )

    categories = (
        published_activities
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    countries = (
        published_activities
        .values_list("country", flat=True)
        .exclude(country="")
        .distinct()
        .order_by("country")
    )

    languages = (
        published_activities
        .values_list("language", flat=True)
        .distinct()
        .order_by("language")
    )

    # Pagination
    paginator = Paginator(activities, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "activities": page_obj.object_list,
        "categories": categories,
        "countries": countries,
        "languages": languages,
        "levels": Activity.Level.choices,
        "modalities": Activity.Modality.choices,
        "query": query,
        "selected_category": category,
        "selected_level": level,
        "selected_country": country,
        "selected_language": language,
        "selected_modality": modality,
    }

    return render(
        request,
        "learning/activity_list.html",
        context,
    )


@login_required
def activity_detail(request, slug):
    activity = get_object_or_404(
        Activity.objects.select_related("facilitator"),
        slug=slug,
        status=Activity.Status.PUBLISHED,
    )

    materials = activity.materials.all()

    discussion_threads = (
        activity.discussion_threads
        .select_related("author")
    )

    enrolment = (
        Enrolment.objects
        .filter(
            participant=request.user,
            activity=activity,
        )
        .first()
    )

    context = {
        "activity": activity,
        "materials": materials,
        "discussion_threads": discussion_threads,
        "enrolment": enrolment,
        "now": timezone.now(),
    }

    return render(
        request,
        "learning/activity_detail.html",
        context,
    )

@login_required
def enrol_activity(request, slug):
    if request.method != "POST":
        return redirect(
            "learning:activity_detail",
            slug=slug,
        )

    activity = get_object_or_404(
        Activity,
        slug=slug,
    )

    try:
        enrolment, created = enrol_participant(
            participant=request.user,
            activity=activity,
        )

        if created:
            messages.success(
                request,
                f"You have successfully enrolled in "
                f"'{activity.title}'.",
            )
        else:
            messages.success(
                request,
                f"You have been re-enrolled in "
                f"'{activity.title}'.",
            )

    except ValidationError as error:
        messages.error(
            request,
            error.message,
        )

    return redirect(
        "learning:activity_detail",
        slug=activity.slug,
    )
@login_required
def withdraw_activity(request, slug):
    if request.method != "POST":
        return redirect(
            "learning:activity_detail",
            slug=slug,
        )

    activity = get_object_or_404(
        Activity,
        slug=slug,
    )

    try:
        withdraw_participant(
            participant=request.user,
            activity=activity,
        )

        messages.success(
            request,
            f"You have withdrawn from "
            f"'{activity.title}'.",
        )

    except ValidationError as error:
        messages.error(
            request,
            error.message,
        )

    return redirect(
        "learning:activity_detail",
        slug=activity.slug,
    )
@login_required
def my_enrolments(request):
    enrolments = (
        Enrolment.objects
        .filter(participant=request.user)
        .select_related(
            "activity",
            "activity__facilitator",
        )
        .order_by("-enrolled_at")
    )

    active_enrolments = enrolments.filter(
        status=Enrolment.Status.ACTIVE
    )

    completed_enrolments = enrolments.filter(
        status=Enrolment.Status.COMPLETED
    )

    withdrawn_enrolments = enrolments.filter(
        status=Enrolment.Status.WITHDRAWN
    )

    context = {
        "enrolments": enrolments,
        "active_enrolments": active_enrolments,
        "completed_enrolments": completed_enrolments,
        "withdrawn_enrolments": withdrawn_enrolments,
    }

    return render(
        request,
        "learning/my_enrolments.html",
        context,
    )

@login_required
def material_detail(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=material_id,
    )

    if not can_access_activity(request.user, material.activity):
        raise PermissionDenied(
            "You must be enrolled in this activity to access its materials."
        )

    if material.activity.status != Activity.Status.PUBLISHED:
        if not (
            request.user.is_superuser
            or request.user.is_staff
            or material.activity.facilitator_id == request.user.pk
        ):
            raise PermissionDenied(
                "This activity is not currently available."
            )

    return render(
        request,
        "learning/material_detail.html",
        {
            "material": material,
            "activity": material.activity,
        },
    )
@login_required
def material_detail(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=material_id,
    )

    if not can_access_activity(request.user, material.activity):
        raise PermissionDenied(
            "You must be enrolled in this activity to access its materials."
        )

    if material.activity.status != Activity.Status.PUBLISHED:
        if not (
            request.user.is_superuser
            or request.user.is_staff
            or material.activity.facilitator_id == request.user.pk
        ):
            raise PermissionDenied(
                "This activity is not currently available."
            )

    return render(
        request,
        "learning/material_detail.html",
        {
            "material": material,
            "activity": material.activity,
        },
    )
@login_required
def create_discussion(request, slug):
    activity = get_object_or_404(
        Activity,
        slug=slug,
        status=Activity.Status.PUBLISHED,
    )

    if not can_access_activity(request.user, activity):
        raise PermissionDenied(
            "You must be enrolled in this activity to start a discussion."
        )

    if request.method == "POST":
        form = DiscussionThreadForm(request.POST)

        if form.is_valid():
            thread = form.save(commit=False)
            thread.activity = activity
            thread.author = request.user
            thread.save()

            messages.success(
                request,
                "Your discussion topic has been posted.",
            )

            return redirect(
                "learning:discussion_detail",
                thread_id=thread.pk,
            )
    else:
        form = DiscussionThreadForm()

    return render(
        request,
        "learning/create_discussion.html",
        {
            "activity": activity,
            "form": form,
        },
    )

@login_required
def discussion_detail(request, thread_id):
    thread = get_object_or_404(
        DiscussionThread.objects.select_related(
            "activity",
            "author",
            "activity__facilitator",
        ),
        pk=thread_id,
    )

    # Only authorized users can access this discussion.
    if not can_access_activity(request.user, thread.activity):
        raise PermissionDenied(
            "You are not authorized to view this discussion."
        )

    replies = thread.replies.select_related("author")

    if request.method == "POST":
        form = DiscussionReplyForm(request.POST)

        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()

            messages.success(
                request,
                "Your reply has been posted.",
            )

            return redirect(
                "learning:discussion_detail",
                thread_id=thread.pk,
            )
    else:
        form = DiscussionReplyForm()

    return render(
        request,
        "learning/discussion_detail.html",
        {
            "thread": thread,
            "replies": replies,
            "form": form,
        },
    )
def can_manage_activity(user, activity):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or activity.facilitator_id == user.pk
        )
    )
@login_required
def manage_materials(request, slug):
    activity = get_object_or_404(Activity, slug=slug)

    if not can_manage_activity(request.user, activity):
        raise PermissionDenied(
            "You are not authorized to manage these materials."
        )

    materials = activity.materials.all().order_by("order", "created_at")

    return render(
        request,
        "learning/manage_materials.html",
        {
            "activity": activity,
            "materials": materials,
        },
    )


@login_required
def create_material(request, slug):
    activity = get_object_or_404(Activity, slug=slug)

    if not can_manage_activity(request.user, activity):
        raise PermissionDenied(
            "You are not authorized to add materials to this activity."
        )

    if request.method == "POST":
        form = MaterialForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            material = form.save(commit=False)
            material.activity = activity
            material.save()

            messages.success(
                request,
                "Learning material created successfully.",
            )

            return redirect(
                "learning:manage_materials",
                slug=activity.slug,
            )
    else:
        form = MaterialForm()

    return render(
        request,
        "learning/material_form.html",
        {
            "activity": activity,
            "form": form,
            "page_title": "Add learning material",
        },
    )


@login_required
def edit_material(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related("activity"),
        pk=material_id,
    )

    activity = material.activity

    if not can_manage_activity(request.user, activity):
        raise PermissionDenied(
            "You are not authorized to edit this material."
        )

    if request.method == "POST":
        form = MaterialForm(
            request.POST,
            request.FILES,
            instance=material,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Learning material updated successfully.",
            )

            return redirect(
                "learning:manage_materials",
                slug=activity.slug,
            )
    else:
        form = MaterialForm(instance=material)

    return render(
        request,
        "learning/material_form.html",
        {
            "activity": activity,
            "material": material,
            "form": form,
            "page_title": "Edit learning material",
        },
    )


@login_required
def delete_material(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related("activity"),
        pk=material_id,
    )

    activity = material.activity

    if not can_manage_activity(request.user, activity):
        raise PermissionDenied(
            "You are not authorized to delete this material."
        )

    if request.method == "POST":
        material.delete()

        messages.success(
            request,
            "Learning material deleted successfully.",
        )

        return redirect(
            "learning:manage_materials",
            slug=activity.slug,
        )

    return render(
        request,
        "learning/material_confirm_delete.html",
        {
            "activity": activity,
            "material": material,
        },
    )
@login_required
def download_material(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=material_id,
    )

    activity = material.activity

    if not can_access_activity(request.user, activity):
        raise PermissionDenied(
            "You are not authorized to access this material."
        )

    if activity.status != Activity.Status.PUBLISHED:
        if not can_manage_activity(request.user, activity):
            raise PermissionDenied(
                "This activity is not currently available."
            )

    if not material.file:
        raise Http404("No uploaded file exists for this material.")

    try:
        file_handle = material.file.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("The requested file could not be found.")

    filename = Path(material.file.name).name

    response = FileResponse(
        file_handle,
        as_attachment=material.downloadable,
        filename=filename,
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"

    return response

def can_manage_activity(user, activity):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or activity.facilitator_id == user.pk
        )
    )


def require_activity_management(user, activity):
    if not can_manage_activity(user, activity):
        raise PermissionDenied(
            "You are not authorized to manage this activity."
        )

@login_required
def manage_materials(request, slug):
    activity = get_object_or_404(
        Activity,
        slug=slug,
    )

    require_activity_management(request.user, activity)

    materials = activity.materials.all()

    return render(
        request,
        "learning/manage_materials.html",
        {
            "activity": activity,
            "materials": materials,
        },
    )
@login_required
def material_create(request, slug):
    activity = get_object_or_404(
        Activity,
        slug=slug,
    )

    require_activity_management(request.user, activity)

    if request.method == "POST":
        form = MaterialForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            material = form.save(commit=False)
            material.activity = activity
            material.save()

            messages.success(
                request,
                "Learning material created successfully.",
            )

            return redirect(
                "learning:manage_materials",
                slug=activity.slug,
            )
    else:
        form = MaterialForm()

    return render(
        request,
        "learning/material_form.html",
        {
            "activity": activity,
            "form": form,
            "page_title": "Add Learning Material",
        },
    )
@login_required
def material_edit(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related("activity"),
        pk=material_id,
    )

    require_activity_management(
        request.user,
        material.activity,
    )

    if request.method == "POST":
        form = MaterialForm(
            request.POST,
            request.FILES,
            instance=material,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Learning material updated successfully.",
            )

            return redirect(
                "learning:manage_materials",
                slug=material.activity.slug,
            )
    else:
        form = MaterialForm(instance=material)

    return render(
        request,
        "learning/material_form.html",
        {
            "activity": material.activity,
            "material": material,
            "form": form,
            "page_title": "Edit Learning Material",
        },
    )
@login_required
def material_delete(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related("activity"),
        pk=material_id,
    )

    require_activity_management(
        request.user,
        material.activity,
    )

    if request.method == "POST":
        activity_slug = material.activity.slug
        material.delete()

        messages.success(
            request,
            "Learning material deleted successfully.",
        )

        return redirect(
            "learning:manage_materials",
            slug=activity_slug,
        )

    return render(
        request,
        "learning/material_confirm_delete.html",
        {"material": material},
    )


@login_required
def download_material(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related(
            "activity",
            "activity__facilitator",
        ),
        pk=material_id,
    )

    activity = material.activity

    if not can_access_activity(request.user, activity):
        raise Http404

    if activity.status != Activity.Status.PUBLISHED:
        if not can_manage_activity(request.user, activity):
            raise Http404

    if not material.file:
        raise Http404

    if not material.file.storage.exists(material.file.name):
        raise Http404

    filename = Path(material.file.name).name

    response = FileResponse(
        material.file.open("rb"),
        as_attachment=True,
        filename=filename,
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"

    return response
