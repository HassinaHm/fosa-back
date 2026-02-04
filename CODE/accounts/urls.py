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

]
