from django.urls import path
from . import views

urlpatterns = [
    path("", views.members, name="members"),
    path("login/", views.login_view, name="login"),
    path("courses/", views.courses_view, name="courses"),
    path("courses/<slug:course_id>/", views.course_lectures_view, name="course_lectures"),
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
]


