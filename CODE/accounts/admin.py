from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Task, User, Role

admin.site.register(Task)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("nom", "description", "created_at", "updated_at")
    search_fields = ("nom", "description")
    filter_horizontal = ("permissions",)  
    ordering = ("nom",)


class CustomUserAdmin(BaseUserAdmin):
    """Admin personnalisé pour User basé sur AbstractBaseUser + PermissionsMixin"""

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Rôle et permissions"), {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Localisation"), {"fields": ("wilayas", "moughataa_fk", "commune_fk")}),
        (_("Infos supplémentaires"), {"fields": ("email_verified",)}),
        (_("Dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_active", "is_staff", "is_superuser"),
        }),
    )

    list_display = ("email", "role", "is_active", "is_staff", "is_superuser")
    list_filter = ("is_active", "is_staff", "is_superuser", "role", "wilayas", "moughataa_fk", "commune_fk")
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")  # widgets multi-sélection
    readonly_fields = ("last_login",)

    # Quand on sauvegarde un user, on resynchronise ses permissions
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.sync_role_permissions()


admin.site.register(User, CustomUserAdmin)