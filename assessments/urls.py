from django.urls import path

from . import views


app_name = "assessments"


urlpatterns = [
    path(
        "my-assessments/",
        views.participant_assessment_dashboard,
        name="participant_assessment_dashboard",
    ),
    path(
        "activity/<slug:slug>/take/",
        views.participant_assessment_list,
        name="participant_assessment_list",
    ),
    path(
        "take/<uuid:assessment_id>/start/",
        views.assessment_start,
        name="assessment_start",
    ),
    path(
        "attempt/<uuid:attempt_id>/",
        views.assessment_take,
        name="assessment_take",
    ),
    path(
        "attempt/<uuid:attempt_id>/result/",
        views.assessment_result,
        name="assessment_result",
    ),
    path(
        "activity/<slug:slug>/",
        views.assessment_list,
        name="assessment_list",
    ),

    path(
        "activity/<slug:slug>/create/",
        views.assessment_create,
        name="assessment_create",
    ),

    path(
        "<uuid:assessment_id>/edit/",
        views.assessment_edit,
        name="assessment_edit",
    ),

    path(
        "<uuid:assessment_id>/questions/",
        views.question_manage,
        name="question_manage",
    ),

    path(
        "<uuid:assessment_id>/publish/",
        views.assessment_publish,
        name="assessment_publish",
    ),

    path(
        "<uuid:assessment_id>/close/",
        views.assessment_close,
        name="assessment_close",
    ),
]