from django.urls import path

from . import views


app_name = "learning"


urlpatterns = [
    # Activity catalogue
    path(
        "",
        views.activity_list,
        name="activity_list",
    ),

    # Participant enrolments
    path(
        "my-enrolments/",
        views.my_enrolments,
        name="my_enrolments",
    ),
    path(
    "materials/<uuid:material_id>/download/",
    views.download_material,
    name="download_material",
),

    # Learning materials
    path(
        "materials/<uuid:material_id>/",
        views.material_detail,
        name="material_detail",
    ),
    

    # Discussion creation and replies
    path(
        "discussions/new/<slug:slug>/",
        views.create_discussion,
        name="create_discussion",
    ),

    path(
        "discussions/<int:thread_id>/",
        views.discussion_detail,
        name="discussion_detail",
    ),

    # Enrolment actions
    path(
        "<slug:slug>/enrol/",
        views.enrol_activity,
        name="enrol_activity",
    ),

    path(
        "<slug:slug>/withdraw/",
        views.withdraw_activity,
        name="withdraw_activity",
    ),
    path(
    "activities/<slug:slug>/materials/manage/",
    views.manage_materials,
    name="manage_materials",
),

path(
    "activities/<slug:slug>/materials/create/",
    views.material_create,
    name="material_create",
),

path(
    "materials/<uuid:material_id>/edit/",
    views.material_edit,
    name="material_edit",
),

path(
    "materials/<uuid:material_id>/delete/",
    views.material_delete,
    name="material_delete",
),
   
    # Activity detail — keep this last
    path(
        "<slug:slug>/",
        views.activity_detail,
        name="activity_detail",
    ),
    
]