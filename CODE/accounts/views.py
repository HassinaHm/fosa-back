from django.utils import timezone 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, RoleSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.core.mail import send_mail
from django.conf import settings

from .models import User, EmailVerification
from .serializers import (
    RegisterSerializer,
    EmailVerificationSerializer,
    UserProfileSerializer,
    ForgotPasswordSerializer,
    VerifyResetCodeSerializer,
    ResetPasswordSerializer,AccessRequestCreateSerializer,
    AccessRequestAdminSerializer
)
import random


from rest_framework import viewsets, permissions, decorators, response, status
from django.contrib.auth import get_user_model
from .models import Role
from .serializers import  UserListSerializer, UserCreateUpdateSerializer
from accounts.permissions import CustomModelPermissions, FOSARolePermission  # ta RBAC générique


from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions
from .serializers import PermissionSerializer

from django.db.models import Q

ALLOWED_PERM_APPS = {"fosa", "accounts"}           
ALLOWED_PERM_MODELS = {"fosa", "fosahistory", "user"}  
ALLOWED_PREFIXES = ("view_", "add_", "change_", "delete_")  

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Permission.objects.select_related("content_type").all()


        qs = qs.filter(content_type__app_label__in=ALLOWED_PERM_APPS)

        qs = qs.filter(content_type__model__in=ALLOWED_PERM_MODELS)

        cond = Q()
        for p in ALLOWED_PREFIXES:
            cond |= Q(codename__startswith=p)
        qs = qs.filter(cond)

        # tri stable
        return qs.order_by("content_type__app_label", "content_type__model", "codename")


User = get_user_model()

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by("nom")
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated ]

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated ,CustomModelPermissions, FOSARolePermission]

    def get_queryset(self):
        qs = User.objects.all().order_by("email")
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        if getattr(user, "is_superuser", False):
            return qs

        role = getattr(getattr(user, "role", None), "nom", None)


        if role == "Administrateur national":
            return qs


        if role == "gestionnaire régional":
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))
            wilaya_noms = list(user.wilayas.values_list("nom", flat=True))

            return qs.filter(
                Q(wilayas__id__in=wilaya_ids) |
                Q(wilayas__nom__in=wilaya_noms)
            ).distinct()

        # --- Gestionnaire local ---
        if role == "gestionnaire local":
            wilaya_noms = list(user.wilayas.values_list("nom", flat=True))

            q = qs.filter(
                Q(moughataa_fk_id=user.moughataa_fk_id) |
                Q(moughataa_fk__nom=getattr(user.moughataa_fk, "nom", None), wilayas__nom__in=wilaya_noms)
            )

            if user.commune_fk_id:
                q = q.filter(commune_fk_id=user.commune_fk_id)

            return q.distinct()

        return qs.none()  # pas de visibilité sur les autres comptes

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return UserListSerializer
        return UserCreateUpdateSerializer

    @decorators.action(detail=True, methods=["post"])
    def set_password(self, request, pk=None):
        user = self.get_object()
        pwd = request.data.get("password")
        if not pwd:
            return response.Response({"detail": "password requis"}, status=400)
        user.set_password(pwd)
        user.save()
        return response.Response({"detail": "Mot de passe mis à jour"}, status=200)





def generate_verification_code():
    """Generate a 4-digit PIN not used by any active user"""
    from accounts.models import User
    for _ in range(100):
        code = str(random.randint(1000, 9999))
        if not User.objects.filter(pin_code=code, pin_active=True).exists():
            return code
    raise Exception("Impossible de générer un PIN unique")
 
class AccessRequestViewSet(viewsets.ModelViewSet):
    """
    list/retrieve/approve/reject for gestionnaires
    create for mobile (no auth)
    """
 
    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]
 
    def get_serializer_class(self):
        from accounts.serializers import AccessRequestCreateSerializer, AccessRequestAdminSerializer
        if self.action == "create":
            return AccessRequestCreateSerializer
        return AccessRequestAdminSerializer
 
    def get_queryset(self):
        from accounts.models import AccessRequest
        qs = AccessRequest.objects.select_related(
            "wilaya", "moughataa", "reviewed_by", "user"
        ).all()
 
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser:
            return qs
 
        role = getattr(getattr(user, "role", None), "nom", None)
 
        if role == "Administrateur national":
            return qs
 
        if role == "gestionnaire régional":
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))
            return qs.filter(wilaya_id__in=wilaya_ids)
 
        if role == "gestionnaire local":
            return qs.filter(moughataa_id=user.moughataa_fk_id)
 
        # ✅ FIXED: rapporteur sees only their own access request
        if role == "rapporteur":
            return qs.filter(email=user.email)
 
        return qs.none()

    def perform_create(self, serializer):
        fosa_code = serializer.validated_data.get("fosa_code", "").strip()
        fosa_fk = None
 
        if fosa_code:
            try:
                from fosa.models import FOSA
                # ✅ FOSA uses code_etablissement as PK — look up by that
                fosa_fk = FOSA.objects.get(code_etablissement=fosa_code)
            except FOSA.DoesNotExist:
                fosa_fk = None  # Don't fail — just save without FK
 
        serializer.save(
            fosa_fk=fosa_fk,
            fosa_code=fosa_code,  # ✅ also save the raw string
        )
 
 
    # ── POST /api/access-requests/{id}/approve/ ──────────────────────
    @decorators.action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        from accounts.models import AccessRequest, User, Role
        req = self.get_object()
 
        if req.status != AccessRequest.STATUS_PENDING:
            return Response(
                {"detail": "Cette demande a déjà été traitée."},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        email = req.email
 
        # ✅ get_or_create the user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": req.full_name,
                "matricule": req.matricule,
                # ✅ fosa_code is a CharField — store code_etablissement string
                "fosa_code": req.fosa_code or (
                    req.fosa_fk.code_etablissement if req.fosa_fk else ""
                ),
                "is_active": True,
            }
        )
 
        if not created:
            # Update existing user fields if already exists
            user.full_name = req.full_name
            user.matricule = req.matricule
            user.fosa_code = req.fosa_code or (
                req.fosa_fk.code_etablissement if req.fosa_fk else ""
            )
 
        # Assign rapporteur role
        try:
            rapporteur_role = Role.objects.get(nom="rapporteur")
            user.role = rapporteur_role
        except Role.DoesNotExist:
            pass  # Role not created yet — warn admin
 
        # Assign geographic scope
        if req.wilaya:
            user.wilayas.add(req.wilaya)
        if req.moughataa:
            user.moughataa_fk = req.moughataa
 
        # ✅ Link fosa_fk properly using code_etablissement PK
        if req.fosa_fk:
            user.fosa_fk = req.fosa_fk
        elif req.fosa_code:
            try:
                from fosa.models import FOSA
                user.fosa_fk = FOSA.objects.get(code_etablissement=req.fosa_code)
                user.fosa_code = req.fosa_code
            except FOSA.DoesNotExist:
                pass
 
        # Generate unique PIN
        pin = generate_verification_code()
        user.pin_code         = pin
        user.pin_generated_at = timezone.now()
        user.pin_active       = True
        user.save()
 
        # Update access request
        req.status      = AccessRequest.STATUS_APPROVED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.user        = user
        req.save()
 
        return Response({
            "detail":   "Demande approuvée. Compte rapporteur créé.",
            "pin_code": pin,
            "user_id":  user.id,
            "email":    user.email,
            "fosa":     user.fosa_code,
        }, status=status.HTTP_200_OK)

 

@api_view(["POST"])
@permission_classes([AllowAny])
def verify_pin_view(request):
    from accounts.models import User
    from datetime import timedelta
 
    pin_code = request.data.get("pin_code", "").strip()
 
    if not pin_code or len(pin_code) != 4:
        return Response({"detail": "Code PIN invalide (4 chiffres requis)"}, status=400)
 
    try:
        user = User.objects.select_related(
            "role", "moughataa_fk", "fosa_fk"
        ).get(
            pin_code=pin_code,
            pin_active=True,
            is_active=True,
        )
    except User.DoesNotExist:
        return Response({"detail": "Code incorrect ou accès révoqué"}, status=401)
 
    # Expire after 90 days
    if user.pin_generated_at:
        if timezone.now() - user.pin_generated_at > timedelta(days=90):
            return Response(
                {"detail": "Code expiré. Contactez votre gestionnaire."},
                status=401
            )
 
    refresh = RefreshToken.for_user(user)
 
    # ✅ fosa_code is a CharField — read directly
    # fosa_fk.code_etablissement is the PK string if FK is set
    fosa_code = (
        user.fosa_code
        or (user.fosa_fk.code_etablissement if user.fosa_fk else "")
    )
 
    return Response({
        "access":    str(refresh.access_token),
        "refresh":   str(refresh),
        "full_name": user.full_name or user.email,
        "email":     user.email,
        "role":      getattr(getattr(user, "role", None), "nom", "rapporteur"),
        "wilaya":    user.wilayas.first().nom if user.wilayas.exists() else "",
        "moughataa": getattr(user.moughataa_fk, "nom", "") or "",
        "fosa_code": fosa_code,
    }, status=200)


 
 
def send_verification_email(email, code):
    subject = 'Votre code de vérification'
    message = f'Votre code de vérification est : {code}'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        if User.objects.filter(email=email).exists():
            return Response({"error": "Cette adresse email est déjà enregistrée"}, status=400)

        user = User.objects.create_user(email=email, password=password)
        code = generate_verification_code()
        EmailVerification.objects.create(email=email, code=code)

        send_verification_email(email, code)

        return Response({"message": "Utilisateur créé. Code de vérification envoyé par email."}, status=201)
    return Response(serializer.errors, status=400)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_view(request):
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            verification = EmailVerification.objects.filter(email=email, code=code).latest('created_at')
        except EmailVerification.DoesNotExist:
            return Response({"error": "Code de vérification invalide ou expiré"}, status=400)

        try:
            user = User.objects.get(email=email)
            user.email_verified = True
            user.save()
            return Response({"message": "Email vérifié avec succès"})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=404)

    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"detail": "Déconnexion réussie"}, status=status.HTTP_205_RESET_CONTENT)

    except KeyError:
        return Response({"error": "Token de rafraîchissement manquant"}, status=status.HTTP_400_BAD_REQUEST)
    except TokenError:
        return Response({"error": "Token invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def home(request):
    return Response({"message": "Email vérifié avec succès"})

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        if not User.objects.filter(email=email).exists():
            return Response({"error": "Cette adresse email n'existe pas."}, status=404)
        
        code = generate_verification_code()
        EmailVerification.objects.create(email=email, code=code)
        send_verification_email(email, code)

        return Response({"message": "Code de réinitialisation envoyé par email."})
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code_view(request):
    serializer = VerifyResetCodeSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        if EmailVerification.objects.filter(email=email, code=code).exists():
            return Response({"message": "Code de vérification validé."})
        return Response({"error": "Code invalide."}, status=400)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            verification = EmailVerification.objects.filter(email=email, code=code).latest('created_at')
        except EmailVerification.DoesNotExist:
            return Response({"error": "Code de vérification invalide."}, status=400)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Mot de passe réinitialisé avec succès."})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=404)

    return Response(serializer.errors, status=400)



from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": "✅ Tâche reçue et enregistrée avec succès !",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)