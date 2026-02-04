# fosa/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q


class FOSARolePermission(BasePermission):
    """
    Permissions métiers pour FOSA :
    - Admin national : accès complet
    - Gestionnaire régional : accès restreint à ses wilayas (par id ou par nom)
    - Gestionnaire local : accès restreint à sa moughataa et sa wilaya (par id ou nom)
    - Utilisateur public : accès seulement aux FOSA publics (is_public=True)
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return request.method in SAFE_METHODS

        if user.is_superuser:
            return True

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return obj.is_public

        if user.is_superuser:
            return True

        role_name = user.role.nom if getattr(user, "role", None) else None

        # === Admin national ===
        if role_name == "Administrateur national":
            return True

        # === Gestionnaire régional ===
        if role_name == "gestionnaire régional":
            user_wilaya_ids = set(user.wilayas.values_list("id", flat=True))
            user_wilaya_noms = set(user.wilayas.values_list("nom", flat=True))

            return (
                obj.wilaya_fk_id in user_wilaya_ids
                or obj.wilaya in user_wilaya_noms
            )

        # === Gestionnaire local ===
        if role_name == "gestionnaire local":
            user_wilaya_noms = set(user.wilayas.values_list("nom", flat=True))

            # doit appartenir à la moughataa de l’utilisateur
            moughataa_ok = (
                obj.moughataa_fk_id == user.moughataa_fk_id
                or obj.moughataa in [getattr(user.moughataa, "nom", None)]
            )

            # doit appartenir aussi à la wilaya de l’utilisateur
            wilaya_ok = (
                obj.wilaya_fk_id in user.wilayas.values_list("id", flat=True)
                or obj.wilaya in user_wilaya_noms
            )

            if not (moughataa_ok and wilaya_ok):
                return False

            # si une commune est définie pour l’utilisateur, restreindre encore
            # if user.commune_fk_id:
            #     return obj.commune_fk_id == user.commune_fk_id

            return True

        # === Utilisateur public ===
        if role_name == "Utilisateurs publics":
            return obj.is_public

        return False

class CustomModelPermissions(BasePermission):
    """
    Mappe automatiquement GET/POST/PATCH/DELETE vers
    app_label.view/add/change/delete_model via user.has_perm.
    """

    def has_permission(self, request, view):
        user = request.user
        if getattr(user, "is_superuser", False):
            return True

        model = self._get_model(view)
        if model is None:
            return request.method in SAFE_METHODS

        app_label = model._meta.app_label
        model_name = model._meta.model_name

        if request.method in SAFE_METHODS:
            codename = f"{app_label}.view_{model_name}"
        elif request.method == "POST":
            codename = f"{app_label}.add_{model_name}"
        elif request.method in ("PUT", "PATCH"):
            codename = f"{app_label}.change_{model_name}"
        elif request.method == "DELETE":
            codename = f"{app_label}.delete_{model_name}"
        else:
            codename = f"{app_label}.change_{model_name}"

        return user.has_perm(codename)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, "is_superuser", False):
            return True

        model = obj.__class__
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        if request.method in SAFE_METHODS:
            codename = f"{app_label}.view_{model_name}"
        elif request.method == "POST":
            codename = f"{app_label}.add_{model_name}"
        elif request.method in ("PUT", "PATCH"):
            codename = f"{app_label}.change_{model_name}"
        elif request.method == "DELETE":
            codename = f"{app_label}.delete_{model_name}"
        else:
            codename = f"{app_label}.change_{model_name}"

        return user.has_perm(codename)

    def _get_model(self, view):
        # priorité à get_queryset().model s’il existe
        get_qs = getattr(view, "get_queryset", None)
        if callable(get_qs):
            try:
                qs = get_qs()
                if hasattr(qs, "model"):
                    return qs.model
            except Exception:
                pass
        qs = getattr(view, "queryset", None)
        if qs is not None and hasattr(qs, "model"):
            return qs.model
        s = getattr(view, "serializer_class", None)
        if s and hasattr(s, "Meta") and hasattr(s.Meta, "model"):
            return s.Meta.model
        return None
