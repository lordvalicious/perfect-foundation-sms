from django.urls import path

from .views import (
    ActiveInstitutionView,
    CurrentUserView,
    LoginFailedView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RoleListView,
    UserProfileView,
    csrf_token,
)

urlpatterns = [
    path("csrf/", csrf_token, name="csrf-token"),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "login/failed/",
        LoginFailedView.as_view(),
        name="login-failed",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path(
        "active-institution/",
        ActiveInstitutionView.as_view(),
        name="active-institution",
    ),
    path(
        "users/<int:pk>/",
        UserProfileView.as_view(),
        name="user-profile",
    ),
    path("roles/", RoleListView.as_view(), name="role-list"),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
