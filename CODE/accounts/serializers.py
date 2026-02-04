# accounts/serializers.py
from django.contrib.auth import get_user_model
from fosa.models import Wilaya
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import Permission
from .models import EmailVerification
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Role




from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth.models import Permission

VERBES_FR = {
    "add": "Créer",
    "change": "Modifier",
    "delete": "Supprimer",
    "view": "Voir",
}

MODELS_FR = {
    "user": "Utilisateur",
    "role": "Rôle",
    "fosa": "Formation Sanitaire (FOSA)",
    "fosahistory": "Historique FOSA",
}

class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source="content_type.app_label", read_only=True)
    model = serializers.CharField(source="content_type.model", read_only=True)
    libelle_fr = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "codename", "app_label", "model", "libelle_fr"]

    def get_libelle_fr(self, obj):
        # décoder le codename en parties
        parts = obj.codename.split("_", 1)  
        if len(parts) == 2:
            action, model = parts
            action_fr = VERBES_FR.get(action, action)
            model_fr = MODELS_FR.get(model, model)
            return f"{action_fr} {model_fr}"
        return obj.name  



User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "nom"]



class WilayaMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wilaya
        fields = ["id", "nom"]

class UserListSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    wilayas = WilayaMiniSerializer(many=True, read_only=True) 
    moughataa = serializers.SerializerMethodField()
    commune = serializers.SerializerMethodField()
    extra_permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        source="extra_permissions"  )

    class Meta:
        model = User
        fields = [
            "id", "email", "is_active", "is_staff",
            "role",
            "wilayas",
            "moughataa", "commune", "extra_permission_ids",
        ]

    def get_moughataa(self, obj):
        return {"id": obj.moughataa_fk_id, "nom": getattr(obj.moughataa_fk, "nom", None)} if obj.moughataa_fk_id else None

    def get_commune(self, obj):
        return {"id": obj.commune_fk_id, "nom": getattr(obj.commune_fk, "nom", None)} if obj.commune_fk_id else None



class UserCreateUpdateSerializer(serializers.ModelSerializer):

    role_id = serializers.PrimaryKeyRelatedField(
        source="role", queryset=Role.objects.all(), required=False, allow_null=True
    )

    wilaya_ids = serializers.PrimaryKeyRelatedField(
        source="wilayas", queryset=Wilaya.objects.all(), many=True, required=False
    )
    extra_permission_ids = serializers.PrimaryKeyRelatedField(
        source="extra_permissions", queryset=Permission.objects.all(), many=True, required=False
    )

    class Meta:
        model = User
        fields = [
            "email", "password", "is_active", "is_staff",
            "role_id",
            "wilaya_ids",
            "moughataa_fk", "commune_fk",
            "extra_permission_ids",   # <<< IMPORTANT
        ]
        extra_kwargs = {"password": {"write_only": True, "required": False}}

    def create(self, validated_data):
        # Extraire les M2M avant instanciation
        wilayas = validated_data.pop("wilayas", [])
        extra_perms = validated_data.pop("extra_permissions", [])
        password = validated_data.pop("password", None)

        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()

        # M2M
        if wilayas is not None:
            user.wilayas.set(wilayas)
        if extra_perms is not None:
            user.extra_permissions.set(extra_perms)

        # Recalcule la somme (rôle + extra)
        user.sync_role_permissions()
        return user

    def update(self, instance, validated_data):
        wilayas = validated_data.pop("wilayas", None)             # None => ne pas toucher
        extra_perms = validated_data.pop("extra_permissions", None)  # None => ne pas toucher
        password = validated_data.pop("password", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()

        # M2M (si fourni)
        if wilayas is not None:
            instance.wilayas.set(wilayas)
        if extra_perms is not None:
            instance.extra_permissions.set(extra_perms)

        instance.sync_role_permissions()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User(email=validated_data["email"])
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Étend le payload du token avec des infos user JSON-sérialisables.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        role_obj = getattr(self.user, "role", None)

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "role": (
                {"id": role_obj.id, "nom": role_obj.nom}
                if role_obj else None
            ),
            "email_verified": getattr(self.user, "email_verified", False),
        }
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Profil allégé et sûr (n’affiche pas password, permissions, etc.)
    """
    role = serializers.SerializerMethodField()
    wilaya = serializers.SerializerMethodField()
    moughataa = serializers.SerializerMethodField()
    commune = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "email_verified", "is_active", "is_staff",
            "role", "wilaya", "moughataa", "commune",
        ]
        read_only_fields = fields  # profil en lecture seule ici

    def get_role(self, obj):
        return {"id": obj.role.id, "nom": obj.role.nom} if obj.role else None

    def get_wilaya(self, obj):
        return {"id": obj.wilaya_fk_id, "nom": getattr(obj.wilaya_fk, "nom", None)} if obj.wilaya_fk_id else None

    def get_moughataa(self, obj):
        return {"id": obj.moughataa_fk_id, "nom": getattr(obj.moughataa_fk, "nom", None)} if obj.moughataa_fk_id else None

    def get_commune(self, obj):
        return {"id": obj.commune_fk_id, "nom": getattr(obj.commune_fk, "nom", None)} if obj.commune_fk_id else None


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyResetCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField(write_only=True)


from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'















