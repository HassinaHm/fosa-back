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

from .models import User, EmailVerification, AccessRequest, Notification
from .serializers import (
    RegisterSerializer,
    EmailVerificationSerializer,
    UserProfileSerializer,
    ForgotPasswordSerializer,
    VerifyResetCodeSerializer,
    ResetPasswordSerializer
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
from rest_framework.views import APIView
from datetime import date, timedelta, datetime
import traceback
from fosa.models import Maladie, MaladieReport, FOSA

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
    return str(random.randint(100000, 999999))

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
    
#===========================mobile==========================
from datetime import date, timedelta, datetime
from collections import defaultdict
import traceback

from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import AccessRequest, Notification
from fosa.models import MaladieReport, Maladie, FOSA, Wilaya, Moughataa
# ============================================================
# AUTH MOBILE (PIN)
# ============================================================

class VerifyPinView(APIView):
    permission_classes = []

    def post(self, request):
        User = get_user_model()
        matricule = request.data.get("matricule")
        pin = request.data.get("pin_code")

        if not matricule or not pin or len(str(pin)) != 4:
            return Response(
                {"error": "Matricule et PIN (4 chiffres) requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(matricule=matricule, status="approved")
        except User.DoesNotExist:
            return Response(
                {"error": "Matricule inconnu ou compte non approuvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.pin_code != str(pin):
            return Response(
                {"error": "Code PIN incorrect"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response(self._profile_payload(user, refresh))

    @staticmethod
    def _profile_payload(user, refresh=None):
        wilaya_obj = user.wilayas.first()
        moughataa_obj = getattr(user, 'moughataa_fk', None)
        fosa_obj = getattr(user, 'fosa_mobile', None)

        payload = {
            "full_name": getattr(user, 'name', '') or user.email,
            "matricule": user.matricule,
            "email": user.email,
            "role": getattr(user.role, 'nom', None),
            "status": getattr(user, 'status', None),
            "wilaya": getattr(wilaya_obj, 'nom', ''),
            "moughataa": getattr(moughataa_obj, 'nom', ''),
            "fosa": (getattr(fosa_obj, 'nom_fr', '') or getattr(fosa_obj, 'structure', '') or ''),
            "wilaya_id": getattr(wilaya_obj, 'id', None),
            "moughataa_id": getattr(moughataa_obj, 'id', None),
            "fosa_id": getattr(fosa_obj, 'code_etablissement', None),
        }
        if refresh is not None:
            payload["access"] = str(refresh.access_token)
            payload["refresh"] = str(refresh)
        return payload


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(VerifyPinView._profile_payload(request.user))


# ============================================================
# ACCESS REQUESTS
# ============================================================

class AccessRequestView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return []  
        return [permissions.IsAuthenticated()]

    def post(self, request):
        data = request.data

        required = ["name", "matricule", "wilaya", "moughataa", "fosa"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return Response({"error": f"Champs manquants: {missing}"}, status=400)

        if AccessRequest.objects.filter(matricule=data["matricule"], status="pending").exists():
            return Response({"error": "Une demande en attente existe déjà"}, status=400)

        if not Wilaya.objects.filter(id=data["wilaya"]).exists():
            return Response({"error": "Wilaya invalide"}, status=400)
        if not Moughataa.objects.filter(id=data["moughataa"]).exists():
            return Response({"error": "Moughataa invalide"}, status=400)
        if not FOSA.objects.filter(code_etablissement=data["fosa"]).exists():
            return Response({"error": "FOSA invalide"}, status=400)

        req = AccessRequest.objects.create(
            name=data["name"],
            matricule=data["matricule"],
            email=data.get("email", ""),
            phone_number=data.get("phone_number", ""),
            wilaya_id=data["wilaya"],
            moughataa_id=data["moughataa"],
            fosa_id=data["fosa"],
        )

        User = get_user_model()

        responsables_wilaya = User.objects.filter(
            role__nom="Surveillance",
            status="approved",
            wilayas__id=data["wilaya"],
        ).distinct()

        for resp in responsables_wilaya:
            Notification.objects.create(
                user=resp,
                title="📋 Nouvelle demande d'accès",
                message=(
                    f"{data['name']} ({data['matricule']}) demande "
                    f"l'accès à la structure {req.fosa}."
                ),
                type="info",
            )

            if resp.email and "@mobile" not in resp.email:
                try:
                    send_mail(
                        subject="Nouvelle demande d'accès mobile",
                        message=(
                            f"Bonjour,\n\n"
                            f"L'agent {data['name']} ({data['matricule']}) "
                            f"a soumis une demande d'accès à l'application mobile "
                            f"pour la structure {req.fosa}.\n\n"
                            f"Connectez-vous pour approuver ou refuser cette demande.\n\n"
                            f"Ministère de la Santé"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[resp.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"[DEMANDE] Erreur email: {e}")

        return Response({"id": req.id, "status": req.status}, status=201)


class ApproveRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            req = AccessRequest.objects.get(pk=pk, status="pending")
        except AccessRequest.DoesNotExist:
            return Response({"error": "Demande introuvable ou déjà traitée"}, status=404)

        pin = req.approve(request.user)
        return Response({"message": "Demande approuvée", "pin": pin}, status=200)


class RefuseRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            req = AccessRequest.objects.get(pk=pk, status="pending")
        except AccessRequest.DoesNotExist:
            return Response({"error": "Demande introuvable"}, status=404)

        req.refuse(request.user)
        return Response({"message": "Demande refusée"}, status=200)


# ============================================================
# RAPPORTS MALADIE (mobile)
# ============================================================

class MaladieReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = MaladieReport.objects.filter(submitted_by=request.user)
        period = request.query_params.get("period")

        if period == "week":
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            qs = qs.filter(date__range=(week_start, week_end))

        by_date = defaultdict(list)
        for r in qs:
            by_date[str(r.date)].append(r.status)

        result = []
        for date_str, statuses in by_date.items():
            if "alert" in statuses:
                day_status = "alert"
            elif "sent" in statuses:
                day_status = "sent"
            elif "validated" in statuses:
                day_status = "validated"
            else:
                day_status = "pending"
            result.append({"date": date_str, "status": day_status})

        return Response(result)

    def post(self, request):
        if getattr(request.user, 'status', None) != 'approved':
            return Response({"error": "Compte non approuvé"}, status=403)

        user_fosa = getattr(request.user, 'fosa_mobile', None)
        user_wilaya = request.user.wilayas.first()
        user_moughataa = getattr(request.user, 'moughataa_fk', None)

        if not user_fosa or not user_wilaya or not user_moughataa:
            return Response(
                {"error": "Profil incomplet (FOSA/wilaya/moughataa manquant)"},
                status=400
            )

        cases = request.data.get("cases", [])
        created = []
        updated = []
        errors = []
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        for i, case in enumerate(cases):
            try:
                maladie_id = case.get("maladie")
                if not maladie_id:
                    errors.append({"cas": i, "error": "maladie_id manquant"})
                    continue

                date_str = case.get("date", str(today))
                date_rapport = datetime.strptime(date_str, "%Y-%m-%d").date()

                vals = dict(
                    cas_suspects=case.get("cas_suspects") or None,
                    cas_testes=case.get("cas_testes") or None,
                    cas_preleves=case.get("cas_preleves") or None,
                    cas_confirmes=case.get("cas_confirmes") or None,
                    deces=case.get("deces") or None,
                )

                existing = MaladieReport.objects.filter(
                    fosa_id=user_fosa.code_etablissement,
                    maladie_id=maladie_id,
                    date__gte=week_start,
                    date__lte=week_start + timedelta(days=6),
                ).first()

                if existing:
                    for field, value in vals.items():
                        setattr(existing, field, value)
                    existing.date = date_rapport
                    existing.submitted_by = request.user
                    if hasattr(existing, 'status') and existing.status != 'validated':
                        existing.status = 'sent'
                    existing.save()
                    updated.append(existing.id)
                    report = existing
                else:
                    report = MaladieReport.objects.create(
                        maladie_id=maladie_id,
                        wilaya_id=user_wilaya.id,
                        moughataa_id=user_moughataa.id,
                        fosa_id=user_fosa.code_etablissement,
                        date=date_rapport,
                        submitted_by=request.user,
                        status="sent",
                        **vals
                    )
                    created.append(report.id)

                _check_alert(report)

            except Exception as e:
                print(f"[RAPPORT] ERREUR cas {i}: {e}\n{traceback.format_exc()}")
                errors.append({"cas": i, "error": str(e)})

        if created or updated:
            return Response({
                "created": len(created),
                "updated": len(updated),
                "ids": created + updated,
                "errors": errors,
            }, status=201)

        return Response({
            "error": "Aucun rapport créé ou modifié",
            "details": errors,
        }, status=400)


def _check_alert(report):
    try:
        maladie = report.maladie
        seuil = getattr(maladie, 'seuil_alerte', None)
        cas_c = report.cas_confirmes or 0

        if not seuil or cas_c < seuil:
            return

        if hasattr(report, 'status'):
            report.status = "alert"
            report.save(update_fields=["status"])

        if hasattr(report, 'submitted_by') and report.submitted_by:
            Notification.objects.create(
                user=report.submitted_by,
                title=f"⚠️ Alerte : {maladie.name}",
                message=f"Seuil dépassé : {cas_c} cas confirmés",
                type="alert",
            )

        _send_alert_notification(report)

    except Exception as e:
        print(f"[ALERTE] Erreur: {e}")


def _send_alert_notification(report):
    User = get_user_model()

    wilaya_id = report.wilaya_id
    maladie_name = report.maladie.name if report.maladie else '?'
    wilaya_name = getattr(report.wilaya, 'nom', '?')
    moughataa_name = getattr(report.moughataa, 'nom', '?')
    cas = report.cas_confirmes or 0
    fosa_name = ''
    if hasattr(report, 'fosa') and report.fosa:
        fosa_name = (getattr(report.fosa, 'nom_fr', '') or
                     getattr(report.fosa, 'structure', '') or '')

    title = f"⚠️ Alerte épidémique : {maladie_name}"
    message = (
        f"{cas} cas confirmés de {maladie_name} "
        f"à {fosa_name} ({moughataa_name}, {wilaya_name}). "
        f"Date : {report.date}"
    )
    data = {
        "maladie_name": maladie_name,
        "maladie_name_ar": getattr(report.maladie, "name_ar", None),
        "cas": cas,
        "fosa_name": fosa_name,
        "wilaya_name": wilaya_name,
        "moughataa_name": moughataa_name,
        "date": str(report.date),
    }

    central = User.objects.filter(role__nom="Administrateur", status="approved")
    wilaya_supervisors = User.objects.filter(
        role__nom="Surveillance",
        status="approved",
        wilayas__id=wilaya_id,
    ).distinct()

    destinataires = (central | wilaya_supervisors).distinct()

    for user in destinataires:
        Notification.objects.create(
            user=user, title=title, message=message, type="alert", data=data,
        )
        if user.email and "@mobile" not in user.email:
            try:
                send_mail(
                    subject=title,
                    message=(
                        f"Bonjour,\n\n{message}\n\n"
                        f"Connectez-vous à l'application pour plus de détails.\n\n"
                        f"Ministère de la Santé — Surveillance Épidémiologique"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"[ALERTE] Erreur email {user.email}: {e}")

    print(f"[ALERTE] {destinataires.count()} destinataire(s) notifié(s) (Administrateur + Surveillance wilaya)")

def _send_pin_sms(phone_number, name, pin):
    print(f"[SMS] Envoi à {phone_number} : Bonjour {name}, votre PIN est {pin}")


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        role_nom = getattr(user.role, 'nom', None)

        if role_nom == "Rapporteur":
            notifs = Notification.objects.filter(user=user).exclude(type='alert')
        else:
            notifs = Notification.objects.filter(user=user)

        return Response([{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at,
        } for n in notifs.order_by('-created_at')])


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({"error": "Notification introuvable"}, status=404)

        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return Response({"message": "Marquée comme lue"})


# ============================================================
# STATS WILAYA (Surveillance / Administrateur)
# ============================================================

class WilayaStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        role_nom = getattr(getattr(user, "role", None), "nom", None)

        if role_nom not in ("Surveillance", "Administrateur") and not user.is_superuser:
            return Response({"error": "Accès réservé au personnel de surveillance"}, status=403)

        if role_nom == "Administrateur" or user.is_superuser:
            wilaya_ids = list(Wilaya.objects.values_list("id", flat=True))
        else:
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))

        if not wilaya_ids:
            return Response({"error": "Aucune wilaya assignée"}, status=400)

        today = date.today()
        ws = today - timedelta(days=today.weekday())

        reports = MaladieReport.objects.filter(
            wilaya_id__in=wilaya_ids, week_start=ws
        ).select_related("moughataa", "maladie")

        stats = {}
        for r in reports:
            key = r.moughataa.nom
            stats.setdefault(key, {"total_reports": 0, "alerts": 0, "cas_confirmes": 0})
            stats[key]["total_reports"] += 1
            stats[key]["cas_confirmes"] += r.cas_confirmes or 0
            if r.status == "alert":
                stats[key]["alerts"] += 1

        return Response({
            "week_start": ws,
            "by_moughataa": [{"moughataa": k, **v} for k, v in stats.items()],
        })
