# accounts/models.py
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Permission
)
from django.utils import timezone
from django.conf import settings

from fosa.models import Wilaya

# IMPORTANT : ne pas importer directement fosa.models pour éviter les imports circulaires.
FOSA_WILAYA   = "fosa.Wilaya"
FOSA_MOUGHATA = "fosa.Moughataa"
FOSA_COMMUNE  = "fosa.Commune"


class Role(models.Model):
    nom = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(max_length=200, null=True, blank=True)
    # Table M2M standard vers Permission (AUCUN 'through' personnalisé)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est requise")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        if role:
            role_obj = role if isinstance(role, Role) else Role.objects.get(pk=role)
            user.role = role_obj
            user.save(update_fields=["role"])
            user.sync_role_permissions()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    #========================mobile===========================
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nom complet")
    matricule = models.CharField(max_length=10, blank=True, null=True, unique=True,verbose_name="Matricule")
    status = models.CharField(max_length=20, choices=[
        ("pending",  "En attente"),
        ("approved", "Approuvé"),
        ("refused",  "Refusé"),
    ],default="pending",verbose_name="Statut du compte")
    pin_code = models.CharField(max_length=4, blank=True, null=True, verbose_name="Code PIN")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone")
    fosa_mobile = models.ForeignKey("fosa.FOSA", on_delete=models.SET_NULL, null=True, blank=True,
    related_name="rapporteurs", verbose_name="FOSA mobile")
    fcm_token = models.CharField(max_length=500, blank=True, null=True, verbose_name="FCM Token")
    #==============================================================================
    # Rôle dynamique (RBAC)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")

    extra_permissions = models.ManyToManyField(
        Permission, blank=True, related_name="users_extra_permissions"
    )
    # Rattachement géographique (pour scoper FOSA)
    wilayas = models.ManyToManyField(Wilaya, blank=True, related_name="users")
    moughataa_fk = models.ForeignKey(FOSA_MOUGHATA, null=True, blank=True, on_delete=models.SET_NULL, related_name="users_moughataa")
    commune_fk   = models.ForeignKey(FOSA_COMMUNE,  null=True, blank=True, on_delete=models.SET_NULL, related_name="users_commune")

    # Flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["email"]

    def __str__(self):
        return self.email
    # @property
    # def wilaya (self):
    #     return self.wilaya_fk.nom
    
    @property
    def moughataa (self):
        return self.moughataa_fk.nom
    @property
    def commune (self):
        return self.commune_fk.nom
    
    
    def sync_role_permissions(self):
        """Recalcule user.user_permissions = perms(role) U extra_permissions"""
        role_qs = self.role.permissions.all() if self.role else Permission.objects.none()
        extra_qs = self.extra_permissions.all()
        self.user_permissions.set((role_qs | extra_qs).distinct())

    def has_module_perms(self, app_label):
        # Autorise l'accès au module admin si is_staff
        return self.is_staff

#============================mobile=============================
class AccessRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("approved", "Approuvé"),
        ("refused", "Refusé"),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom")
    matricule = models.CharField(max_length=10, verbose_name="Matricule")
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    wilaya = models.ForeignKey("fosa.Wilaya", on_delete=models.CASCADE)
    moughataa = models.ForeignKey("fosa.Moughataa", on_delete=models.CASCADE)
    fosa = models.ForeignKey("fosa.FOSA", on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_requests"
    )
    generated_pin = models.CharField(max_length=4, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.matricule}) - {self.status}"

    def approve(self, admin_user):
        import random
        import string
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        from django.core.mail import send_mail
        from django.conf import settings

        User = get_user_model()
        pin = "".join(random.choices(string.digits, k=4))

        self.generated_pin = pin
        self.status = "approved"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

        user, _ = User.objects.get_or_create(
            matricule=self.matricule,
            defaults={
                "name": self.name,
                "email": self.email or f"{self.matricule}@gmail.com",
                "phone_number": self.phone_number,
            }
        )
        user.name = self.name
        user.status = "approved"
        user.pin_code = pin
        user.fosa_mobile = self.fosa
        user.phone_number = self.phone_number
        user.moughataa_fk = self.moughataa
        user.set_unusable_password()
        user.save()
        user.wilayas.add(self.wilaya)

      
        if self.email:
            try:
                send_mail(
                    subject="Votre code PIN — Suivi Épidémiologique",
                    message=(
                        f"Bonjour {self.name},\n\n"
                        f"Votre code PIN est : {pin}\n\n"
                        f"Ministère de la Santé"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"[EMAIL] Erreur: {e}")

        if self.phone_number:
            print(f"[SMS] PIN {pin} → {self.phone_number}")  

        return pin

    def refuse(self, admin_user):
        from django.utils import timezone
        self.status = "refused"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(
        max_length=20,
        choices=[
            ("alert", "Alerte épidémique"),
            ("validation", "Validation"),
            ("info", "Information"),
        ],
        default="alert",
    )
    data = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

#========================================================================

class EmailVerification(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vérification email"
        verbose_name_plural = "Vérifications email"

    def __str__(self):
        return f"{self.email} - {self.code}"


class Task(models.Model):
    name = models.CharField(max_length=255)
    desc = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name