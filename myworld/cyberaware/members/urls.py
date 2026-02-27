from django.urls import path
from . import views

urlpatterns = [
    path("", views.members, name="members"),
    path("login/", views.login_view, name="login"),
    path("courses/", views.courses_view, name="courses"),
    path("courses/<slug:course_id>/", views.course_lectures_view, name="course_lectures"),
    path(
        "courses/<slug:course_id>/lecture/<int:lecture_id>/quiz/",
        views.submit_lecture_quiz_view,
        name="submit_lecture_quiz",
    ),
    path("profile/", views.profile_view, name="profile"),
    path("profile/update/", views.update_profile_view, name="update_profile"),
    path("settings/", views.settings_view, name="settings"),
    path("settings/change-password/", views.change_password_view, name="change_password"),
    path("settings/logout-all/", views.logout_all_devices_view, name="logout_all_devices"),
    path("settings/logout-session/", views.logout_session_view, name="logout_session"),
    path("settings/toggle-2fa/", views.toggle_2fa_view, name="toggle_2fa"),
    path("settings/notifications/", views.save_notifications_view, name="save_notifications"),
    path("settings/appearance/", views.save_appearance_view, name="save_appearance"),
    path("settings/privacy/", views.save_privacy_view, name="save_privacy"),
    path("settings/export-data/", views.export_data_view, name="export_data"),
    path("settings/delete-account/", views.delete_account_view, name="delete_account"),
    path("achievements/", views.achievements_view, name="achievements"),
    path("logout/", views.logout_view, name="logout"),
]
