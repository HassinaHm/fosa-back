# accounts/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Permission
)
from django.utils import timezone

from fosa.models import Wilaya

# IMPORTANT : ne pas importer directement fosa.models pour éviter les imports circulaires.
FOSA_WILAYA   = "fosa.Wilaya"
FOSA_MOUGHATA = "fosa.Moughataa"
FOSA_COMMUNE  = "fosa.Commune"


class Role(models.Model):
    nom = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(max_length=200, null=True, blank=True)
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
    #fosa field
    email = models.EmailField(unique=True)
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
    # ── Mobile / Rapporteur fields ──
    full_name     = models.CharField(max_length=255, blank=True)
    matricule     = models.CharField(max_length=100, blank=True)
    fosa_code     = models.CharField(max_length=50, blank=True)   # FOSA they report from
    fosa_fk       = models.ForeignKey("fosa.FOSA", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="rapporteurs")
 
    # ── PIN fields ──
    pin_code          = models.CharField(max_length=4, null=True, blank=True, unique=True)
    pin_generated_at  = models.DateTimeField(null=True, blank=True)
    pin_active        = models.BooleanField(default=False)  # False until approved

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


class AccessRequest(models.Model):
    """
    Rapporteur submits this from the mobile app before getting a PIN.
    A gestionnaire local or regional then approves or rejects it.
    """
    STATUS_PENDING  = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
 
    STATUS_CHOICES = [
        (STATUS_PENDING,  "En attente"),
        (STATUS_APPROVED, "Approuvé"),
        (STATUS_REJECTED, "Rejeté"),
    ]
 
    # ── Rapporteur info (submitted from mobile, before account exists) ──
    full_name  = models.CharField(max_length=255)
    matricule  = models.CharField(max_length=100)
    email      = models.EmailField()
 
    # ── Geographic scope ──
    wilaya     = models.ForeignKey("fosa.Wilaya",    null=True, blank=True, on_delete=models.SET_NULL)
    moughataa  = models.ForeignKey("fosa.Moughataa", null=True, blank=True, on_delete=models.SET_NULL)
    fosa_code  = models.CharField(max_length=50, blank=True)
    fosa_fk    = models.ForeignKey("fosa.FOSA",      null=True, blank=True, on_delete=models.SET_NULL)
 
    # ── Status ──
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by   = models.ForeignKey("accounts.User", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="reviewed_requests")
    reviewed_at   = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
 
    # ── Created user after approval ──
    user          = models.OneToOneField("accounts.User", null=True, blank=True,
                                          on_delete=models.SET_NULL, related_name="access_request")
 
    created_at    = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = "Demande d'accès"
        verbose_name_plural = "Demandes d'accès"
        ordering = ["-created_at"]
 
    def __str__(self):
        return f"{self.full_name} ({self.matricule}) — {self.status}"
 

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