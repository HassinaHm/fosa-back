# accounts/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PermissionViewSet, RoleViewSet, TaskViewSet, UserViewSet
from . import views


router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"users", UserViewSet, basename="user")
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r'tasks', TaskViewSet ,basename="tasks")

from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    VerifyPinView,
    MeView,
    AccessRequestView,
    ApproveRequestView,
    RefuseRequestView,
    MaladieReportView,
    NotificationView,
    MarkNotificationReadView,
    WilayaStatsView,
)
urlpatterns = router.urls + [
    path("register/", views.register_view, name="register"),
    path("verify-email/", views.verify_email_view, name="verify-email"),
    path("login/", views.CustomTokenObtainPairView.as_view(), name="login"),
    path("profile/", views.user_profile_view, name="profile"),
    path("logout/", views.logout, name="logout"),
    path("forgot-password/", views.forgot_password_view, name="forgot-password"),
    path("verify-reset-code/", views.verify_reset_code_view, name="verify-reset-code"),
    path("reset-password/", views.reset_password_view, name="reset-password"),
    # path("tasks/", views.TaskViewSet, name="reset-password"),
    #===============================mobile================================
    path("verify-pin/", VerifyPinView.as_view(), name="verify-pin"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("access-requests/", AccessRequestView.as_view(), name="access-requests"),
    path("access-requests/<int:pk>/approve/", ApproveRequestView.as_view(), name="access-requests-approve"),
    path("access-requests/<int:pk>/refuse/", RefuseRequestView.as_view(), name="access-requests-refuse"),
    path("maladie-reports/", MaladieReportView.as_view(), name="maladie-reports"),
    path("notifications/", NotificationView.as_view(), name="notifications"),
    path("notifications/<int:pk>/mark-read/", MarkNotificationReadView.as_view(), name="notification-mark-read"),
    path("wilaya-stats/", WilayaStatsView.as_view(), name="wilaya-stats"),
]
