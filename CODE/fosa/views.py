from accounts.permissions import CustomModelPermissions, FOSARolePermission
from rest_framework import viewsets, permissions, serializers, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import HttpResponse
from import_export import resources
from tablib import Dataset
from django.contrib.auth.models import User
from .models import FOSA, FOSAHistory
import logging
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q
from import_export import resources
from .models import FOSA, TypeStructure
import json
from .models import (
    Wilaya, Moughataa, Commune, FOSA, FOSAHistory,
    Maladie, MaladieReport,
    TypeStructure, NormePersonnel, NormeService, NormeMateriel
)
from .serializers import (
    FOSASerializer, WilayaSerializer, MoughataaSerializer, CommuneSerializer,
    MaladieSerializer, MaladieReportSerializer, TypeStructureSerializer,
    NormePersonnelSerializer, NormeServiceSerializer, NormeMaterielSerializer,
    PersonnelStructureSerializer, ServiceStructureSerializer, MaterielStructureSerializer,
    FOSAHistorySerializer
)

from .models import PersonnelStructure, ServiceStructure, MaterielStructure
from .util import filter_queryset_by_role
from django.conf import settings
logger = logging.getLogger(__name__)


# ============================================================
# PERSONNEL STRUCTURE VIEWSET
# ============================================================
class PersonnelStructureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing personnel in FOSA structures.
    Filter by FOSA using ?fosa={code_etablissement}
    """
    serializer_class = PersonnelStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['structure']
    search_fields = ['intitule_poste', 'structure__nom_fr', 'structure__code_etablissement']

    def get_queryset(self):
        qs = PersonnelStructure.objects.select_related('structure').all()
        
        # Filter by FOSA code if provided
        fosa_code = self.request.query_params.get('fosa')
        if fosa_code:
            qs = qs.filter(structure__code_etablissement=fosa_code)
        
        # Filter by structure ID if provided
        structure_id = self.request.query_params.get('structure')
        if structure_id:
            qs = qs.filter(structure_id=structure_id)
        
        return qs.order_by('structure__code_etablissement', 'intitule_poste')

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


# ============================================================
# SERVICE STRUCTURE VIEWSET
# ============================================================
class ServiceStructureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing services in FOSA structures.
    Filter by FOSA using ?fosa={code_etablissement}
    """
    serializer_class = ServiceStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['structure', 'disponible']
    search_fields = ['nom_service', 'structure__nom_fr', 'structure__code_etablissement']

    def get_queryset(self):
        qs = ServiceStructure.objects.select_related('structure').all()
        
        # Filter by FOSA code if provided
        fosa_code = self.request.query_params.get('fosa')
        if fosa_code:
            qs = qs.filter(structure__code_etablissement=fosa_code)
        
        # Filter by structure ID if provided
        structure_id = self.request.query_params.get('structure')
        if structure_id:
            qs = qs.filter(structure_id=structure_id)
        
        return qs.order_by('structure__code_etablissement', 'nom_service')

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


# ============================================================
# MATERIEL STRUCTURE VIEWSET
# ============================================================
class MaterielStructureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing materiel (equipment) in FOSA structures.
    Filter by FOSA using ?fosa={code_etablissement}
    """
    serializer_class = MaterielStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['structure']
    search_fields = ['nom_materiel', 'structure__nom_fr', 'structure__code_etablissement']

    def get_queryset(self):
        qs = MaterielStructure.objects.select_related('structure').all()
        
        # Filter by FOSA code if provided
        fosa_code = self.request.query_params.get('fosa')
        if fosa_code:
            qs = qs.filter(structure__code_etablissement=fosa_code)
        
        # Filter by structure ID if provided
        structure_id = self.request.query_params.get('structure')
        if structure_id:
            qs = qs.filter(structure_id=structure_id)
        
        return qs.order_by('structure__code_etablissement', 'nom_materiel')

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


# fosa/views_geo.py
from rest_framework import viewsets, filters
# from django_filters.rest_framework import DjangoFilterBackend
from .models import Wilaya, Moughataa, Commune
from .serializers import  FOSASerializer, WilayaSerializer, MoughataaSerializer, CommuneSerializer
from accounts.permissions import CustomModelPermissions  # si tu veux verrouiller CRUD



class WilayaViewSet(viewsets.ModelViewSet):
    serializer_class = WilayaSerializer

    def get_queryset(self):
        qs = Wilaya.objects.all().order_by("nom")
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
            return qs.filter(Q(id__in=wilaya_ids) | Q(nom__in=wilaya_noms))

        if role == "gestionnaire local":
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))
            wilaya_noms = list(user.wilayas.values_list("nom", flat=True))
            return qs.filter(Q(id__in=wilaya_ids) | Q(nom__in=wilaya_noms))

        return qs.none()
    #=========================mobile===============================
    @action(
        detail=False,
        methods=["get"],
        url_path="mobile",
        permission_classes=[AllowAny],
    )
    def mobile_list(self, request):
        token    = request.headers.get("X-Mobile-Token", "")
        expected = getattr(settings, "MOBILE_ACCESS_TOKEN",
                           "msr-sante-2026-mobile-key")
        print(f"HEADERS REÇUS: {dict(request.headers)}")
        print(f"X-Mobile-Token reçu: {token}")

        if token != expected:
            return Response({"error": "Non autorisé"}, status=403)
        
        wilayas = Wilaya.objects.all().order_by("nom")
        return Response([{
            "id":   w.id,
            "name": w.nom,
        } for w in wilayas])
    #===============================================================
class MoughataaViewSet(viewsets.ModelViewSet):
    serializer_class = MoughataaSerializer
    filterset_fields = ["wilaya"]
    search_fields = ["nom", "code", "wilaya__nom"]

    def get_queryset(self):
        qs = Moughataa.objects.select_related("wilaya").all()
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
            return qs.filter(Q(wilaya_id__in=wilaya_ids) | Q(wilaya__nom__in=wilaya_noms))

        if role == "gestionnaire local":
            return qs.filter(
                Q(id=user.moughataa_fk_id) |
                Q(nom=getattr(user.moughataa_fk, "nom", None))
            )

        return qs.none()

    #=============================mobile==============================
    @action(
    detail=False,
    methods=["get"],
    url_path="mobile",
    permission_classes=[AllowAny],
    )
    def mobile_list(self, request):
        token    = request.headers.get("X-Mobile-Token", "")
        expected = getattr(settings, "MOBILE_ACCESS_TOKEN", "msr-sante-2026-mobile-key")

        if token != expected:
            return Response({"error": "Non autorisé"}, status=403)

        wilaya_id = request.query_params.get("wilaya")
        if not wilaya_id: 
            return Response({"error": "Paramètre wilaya requis"}, status=400)

        qs = Moughataa.objects.filter(wilaya_id=wilaya_id).order_by("nom")

        print(f"MOUGHATAAS URL: {request.build_absolute_uri()}")
        print(f"MOUGHATAAS STATUS: 200 | BODY: {list(qs.values('id','nom'))}")

        return Response([{"id": m.id, "name": m.nom,} for m in qs])
    #==============================================================

class CommuneViewSet(viewsets.ModelViewSet):
    serializer_class = CommuneSerializer
    filterset_fields = ["moughataa"]
    search_fields = ["nom", "code", "moughataa__nom", "moughataa__wilaya__nom"]

    def get_queryset(self):
        qs = Commune.objects.select_related("moughataa", "moughataa__wilaya").all()
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
                Q(moughataa__wilaya_id__in=wilaya_ids) |
                Q(moughataa__wilaya__nom__in=wilaya_noms)
            )

        if role == "gestionnaire local":
            q = qs.filter(
                Q(moughataa_id=user.moughataa_fk_id) |
                Q(moughataa__nom=getattr(user.moughataa_fk, "nom", None))
            )
            if user.commune_fk_id:
                q = q.filter(id=user.commune_fk_id)
            return q

        return qs.none()
    
    #========================mobile===============================
    @action(
        detail=False,
        methods=["get"],
        url_path="mobile",
        permission_classes=[AllowAny],
    )
    def mobile_list(self, request):
        token    = request.headers.get("X-Mobile-Token", "")
        expected = getattr(settings, "MOBILE_ACCESS_TOKEN", "msr-sante-2026-mobile-key")

        if token != expected:
            return Response({"error": "Non autorisé"}, status=403)

        moughataa_id = request.query_params.get("moughataa")
        if not moughataa_id:
            return Response({"error": "Paramètre moughataa requis"}, status=400)
        
        qs = Commune.objects.filter(moughataa_id=moughataa_id).order_by("nom")

        return Response([{"id": c.id,"name": c.nom,} for c in qs])
    #=============================================================

# fosa/views_import.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from .utils_import_geo import import_geo_from_xlsx
from accounts.permissions import CustomModelPermissions  

class GeoImportView(APIView):
    """
    POST multipart/form-data:
      - file: .xlsx
      - update_if_exists: "true" / "false"
    """
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated ,CustomModelPermissions, FOSARolePermission]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "Aucun fichier fourni"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        if not file.name.lower().endswith('.xlsx'):
            return Response({"error": "Seul le format .xlsx est accepté"}, status=400)

        try:
            result = import_geo_from_xlsx(file)
            return Response(result, status=200)
        except Exception as e:
            logger.error(f"Erreur import géo: {e}")
            return Response({"error": str(e)}, status=400)



# Maladie Views
from .models import Maladie, MaladieReport

class MaladieViewSet(viewsets.ModelViewSet):
    queryset = Maladie.objects.all().order_by("name")
    serializer_class = MaladieSerializer
    # permission_classes = [IsAuthenticated, CustomModelPermissions,]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), CustomModelPermissions(),FOSARolePermission()]
    #=================mobile=====================
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return Response([{
            "id": m.id,
            "name": m.name,
            "name_ar": getattr(m, "name_ar",  None),
            "enabled_fields": m.enabled_fields,
            "is_epidemic": getattr(m, "is_epidemic", False),
            "seuil_alerte": getattr(m, "seuil_alerte", None),
            "can_report_individually": getattr(m, "can_report_individually", False),
        } for m in qs])
    #=============================================

class MaladieReportViewSet(viewsets.ModelViewSet):
    serializer_class = MaladieReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['wilaya', 'moughataa', 'maladie', 'date']
    search_fields = ['wilaya__nom', 'moughataa__nom', 'maladie__name']
    #=================mobile======================
    def get_permissions(self):
        params = self.request.query_params
        if (params.get("mine") == "true" or
                params.get("period") == "week"):
            return [IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    #==============================================
    def get_queryset(self):
        qs = MaladieReport.objects.select_related('wilaya', 'moughataa', 'maladie').all()
        user = self.request.user
        params = self.request.query_params
        if not user.is_authenticated:
            return qs.none()

        #=================mobile================
        if self.request.query_params.get("mine") == "true":
            return (
                qs.filter(submitted_by=user)
                .order_by("-date")
            )
        
        if params.get("period") == "week":
            from datetime import date, timedelta
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return (
                qs.filter(
                    submitted_by=user,
                    date__range=(week_start, week_end),
                )
                .order_by("-date")
            )
        date_param = params.get("date")
        date_start = params.get("date_start")
        date_end   = params.get("date_end")
        wilaya     = params.get("wilaya")
        moughataa  = params.get("moughataa")
        maladie    = params.get("maladie")

        if date_param: qs = qs.filter(date=date_param)
        if date_start and date_end: qs = qs.filter(date__range=[date_start, date_end])
        if wilaya: qs = qs.filter(wilaya_id=wilaya)
        if moughataa: qs = qs.filter(moughataa_id=moughataa)
        if maladie: qs = qs.filter(maladie_id=maladie)
        #=========================================================
        if user.is_superuser:
            return qs

        role = getattr(getattr(user, "role", None), "nom", None)

        if role == "Administrateur national":
            return qs

        if role == "gestionnaire régional":
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))
            return qs.filter(wilaya_id__in=wilaya_ids)

        if role == "gestionnaire local":
            if user.moughataa_fk_id:
                return qs.filter(moughataa_fk_id=user.moughataa_fk_id)
            return qs.none()

        return qs.none()
    
    #===================mobile====================
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
    
    @action(detail=False, methods=["get"], url_path="export-weekly")
    def export_weekly(self, request):
        import io
        from datetime import datetime
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from django.http import HttpResponse

        date_start = request.query_params.get("date_start")
        date_end = request.query_params.get("date_end")

        if not date_start or not date_end:
            return Response({"detail": "date_start et date_end sont requis (format: YYYY-MM-DD)"},
                status=400
            )

        try:
            start = datetime.strptime(date_start, "%Y-%m-%d").date()
            end = datetime.strptime(date_end, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Format de date invalide. Utilisez YYYY-MM-DD"},
                status=400
            )
        week_num = start.isocalendar()[1]
        reports = (MaladieReport.objects.filter(date__range=[start, end])
            .select_related("wilaya", "moughataa", "maladie")
            .order_by("wilaya__nom", "moughataa__nom", "maladie__name")
        )
        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport Hebdomadaire"
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        header_font = Font(bold=True, color="FFFFFF", size=11)
        title_font = Font(bold=True, size=12)
        border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin")
        )
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.merge_cells("A1:H1")
        ws["A1"].value = "NOTIFICATION DES MALADIES ET EVENEMENTS"
        ws["A1"].font = title_font
        ws["A1"].alignment = center_align

        ws.merge_cells("A2:H2")
        ws["A2"].value = (
            f"Sem. Épid. N° : {week_num:02d}  "
            f"du {start.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}"
        )
        ws["A2"].font = Font(bold=True, size=10)
        ws["A2"].alignment = center_align

        row  = 4
        headers = [
            "Wilaya", "Moughataa", "Maladie",
            "Cas Suspects", "Décès",
            "Cas Prélevés", "Cas Testés", "Cas Confirmés"
        ]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = border

        row = 5
        for report in reports:
            ws.cell(row=row, column=1).value = report.wilaya.nom
            ws.cell(row=row, column=2).value = report.moughataa.nom
            ws.cell(row=row, column=3).value = report.maladie.name
            ws.cell(row=row, column=4).value = report.cas_suspects  or 0
            ws.cell(row=row, column=5).value = report.deces         or 0
            ws.cell(row=row, column=6).value = report.cas_preleves  or 0
            ws.cell(row=row, column=7).value = report.cas_testes    or 0
            ws.cell(row=row, column=8).value = report.cas_confirmes or 0
            for col in range(1, 9):
                ws.cell(row=row, column=col).border = border
                ws.cell(row=row, column=col).alignment = center_align
            row += 1
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 35
        for col in ["D", "E", "F", "G", "H"]:
            ws.column_dimensions[col].width = 15

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = (
            f"Rapport_Epid_Sem_{week_num:02d}_"
            f"{start.strftime('%Y%m%d')}_au_{end.strftime('%Y%m%d')}.xlsx"
        )
        response = HttpResponse(
            output.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument"".spreadsheetml.sheet"),
        )
        response["Content-Disposition"] = (f"attachment; filename={filename}")
        return response
    #==============================================
# Import/Export


class FOSAResource(resources.ModelResource):
    class Meta:
        model = FOSA


class FOSAViewSet(viewsets.ModelViewSet):
    serializer_class = FOSASerializer
    queryset = FOSA.objects.select_related(
        "wilaya_fk", "moughataa_fk", "commune_fk", "type_structure"
    ).all()
    lookup_field = 'code_etablissement'

    permission_classes = [permissions.IsAuthenticated, CustomModelPermissions, FOSARolePermission]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'wilaya': ['exact'],
        'moughataa': ['exact'],
        'commune': ['exact'],
        'wilaya_fk': ['exact'],
        'moughataa_fk': ['exact'],
        'commune_fk': ['exact'],
        'type': ['exact'],
        'type_structure': ['exact'],
        'is_public': ['exact'],
        'etat': ['exact'],
    }
    search_fields = ['code_etablissement', 'structure', 'nom_fr', 'nom_ar', 'responsable']
    ordering_fields = ['code_etablissement', 'structure', 'type', 'is_public', 'etat']

    # ------------------------------------------------------------
    # Filtrage par rôle
    # ------------------------------------------------------------
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.filter(is_public=True)

        if user.is_superuser:
            return qs

        role = getattr(getattr(user, "role", None), "nom", None)
        if role == "Administrateur national":
            return qs

        if role == "gestionnaire régional":
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))
            return qs.filter(wilaya_fk_id__in=wilaya_ids)

        if role == "gestionnaire local":
            if user.commune_fk_id:
                return qs.filter(commune_fk_id=user.commune_fk_id)
            if user.moughataa_fk_id:
                return qs.filter(moughataa_fk_id=user.moughataa_fk_id)
            return qs.none()

        return qs.filter(is_public=True)
    # ------------------------------------------------------------
    # Historique
    # ------------------------------------------------------------
    def perform_create(self, serializer):
        instance = serializer.save()
        self._create_history(instance, 'CREATE', {})

    def perform_update(self, serializer):
        instance = self.get_object()
        old_data = FOSASerializer(instance).data.copy()
        updated_instance = serializer.save()
        new_data = FOSASerializer(updated_instance).data.copy()
        changes = self._generate_diff(old_data, new_data)
        self._create_history(updated_instance, 'UPDATE', changes)

    def perform_destroy(self, instance):
        self._create_history(instance, 'DELETE', {})
        instance.delete()

    def _generate_diff(self, old, new):
        return {f: [old[f], new[f]] for f in old.keys() if old.get(f) != new.get(f)}

    def _create_history(self, instance, action, changes):
        FOSAHistory.objects.create(
            fosa=instance,
            user=self.request.user if self.request.user.is_authenticated else None,
            action=action,
            changes=changes
        )
     #======================Mobile======================
    @action(
        detail=False,
        methods=["get"],
        url_path="mobile",
        permission_classes=[AllowAny],
    )
    def mobile_list(self, request):
        token    = request.headers.get("X-Mobile-Token", "")
        expected = getattr(settings, "MOBILE_ACCESS_TOKEN", "msr-sante-2026-mobile-key")

        if token != expected:
            return Response({"error": "Non autorisé"}, status=403)

        moughataa_id = request.query_params.get("moughataa")
        if not moughataa_id:
            return Response({"error": "Paramètre moughataa requis"},status=400)
        
        qs = FOSA.objects.filter(moughataa_fk_id=moughataa_id)
        print(f"[FOSA mobile] via moughataa_fk_id={moughataa_id}: {qs.count()} résultats")

        if qs.count() == 0:
            qs = FOSA.objects.filter(commune_fk__moughataa_fk_id=moughataa_id)
            print(f"[FOSA mobile] via commune: {qs.count()} résultats")

        if qs.count() == 0:
            sample = FOSA.objects.first()
            if sample: print(
                            f"[FOSA mobile] Exemple FOSA: "
                            f"code={sample.code_etablissement}, "
                            f"moughataa_fk_id={getattr(sample, 'moughataa_fk_id', 'N/A')}, "
                            f"commune_fk_id={getattr(sample, 'commune_fk_id', 'N/A')}"
                        )

        print(f"FOSAS STATUS: 200 | BODY: {[f.code_etablissement for f in qs]}")

        return Response([{"id": f.code_etablissement, "name": f.nom_fr or f.structure or str(f.code_etablissement),
        } for f in qs.order_by("nom_fr")])
    # ============================================================
    # Import / Export
    # ============================================================
    @action(detail=False, methods=['post'])
    def import_data(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "Aucun fichier fourni"}, status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        if not file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
            return Response({"error": "Formats acceptés: .xlsx, .xls, .csv"}, status=400)

        dataset = Dataset()
        try:
            if file.name.lower().endswith('.csv'):
                imported_data = dataset.load(file.read().decode('utf-8'), format='csv')
            elif file.name.lower().endswith('.xlsx'):
                imported_data = dataset.load(file.read(), format='xlsx')
            else:
                imported_data = dataset.load(file.read(), format='xls')
        except Exception as e:
            return Response({"status": "error", "error": f"Lecture fichier: {e}"}, status=400)

        resource = FOSAResource()
        result = resource.import_data(dataset, dry_run=False, raise_errors=False)
        return Response({
            "status": "success",
            "imported": result.totals.get('new', 0),
            "updated": result.totals.get('update', 0),
            "skipped": result.totals.get('skipped', 0),
            "total": len(imported_data)
        })

    @action(detail=False, methods=['get'])
    def export_data(self, request):
        resource = FOSAResource()
        dataset = resource.export()
        resp = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="fosas_export.xlsx"'
        return resp
    # ============================================================
    # Actions pour les normes (personnel, services, matériel)
    # ============================================================
    @action(detail=True, methods=["get"])
    def personnels(self, request, code_etablissement=None):
        fosa = self.get_object()
        qs = fosa.personnels.all().order_by("intitule_poste")
        return Response(PersonnelStructureSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="personnels/upsert")
    def personnels_upsert(self, request, code_etablissement=None):
        fosa = self.get_object()
        items = request.data if isinstance(request.data, list) else [request.data]
        saved = []
        for it in items:
            intitule = it.get("intitule_poste")
            nombre = it.get("nombre_reel", 0)
            if not intitule:
                return Response({"detail": "intitule_poste manquant"}, status=400)
            obj, _ = PersonnelStructure.objects.update_or_create(
                structure=fosa,
                intitule_poste=intitule,
                defaults={"nombre_reel": nombre},
            )
            saved.append(PersonnelStructureSerializer(obj).data)
        return Response(saved, status=200)

    @action(detail=True, methods=["get"])
    def services(self, request, code_etablissement=None):
        fosa = self.get_object()
        qs = fosa.services.all().order_by("nom_service")
        return Response(ServiceStructureSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="services/upsert")
    def services_upsert(self, request, code_etablissement=None):
        fosa = self.get_object()
        items = request.data if isinstance(request.data, list) else [request.data]
        saved = []
        for it in items:
            nom = it.get("nom_service")
            dispo = bool(it.get("disponible", False))
            if not nom:
                return Response({"detail": "nom_service manquant"}, status=400)
            obj, _ = ServiceStructure.objects.update_or_create(
                structure=fosa,
                nom_service=nom,
                defaults={"disponible": dispo},
            )
            saved.append(ServiceStructureSerializer(obj).data)
        return Response(saved, status=200)

    @action(detail=True, methods=["get"])
    def materiels(self, request, code_etablissement=None):
        fosa = self.get_object()
        qs = fosa.materiels.all().order_by("nom_materiel")
        return Response(MaterielStructureSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="materiels/upsert")
    def materiels_upsert(self, request, code_etablissement=None):
        fosa = self.get_object()
        items = request.data if isinstance(request.data, list) else [request.data]
        saved = []
        for it in items:
            nom = it.get("nom_materiel")
            qte = it.get("quantite_reelle", 0)
            if not nom:
                return Response({"detail": "nom_materiel manquant"}, status=400)
            obj, _ = MaterielStructure.objects.update_or_create(
                structure=fosa,
                nom_materiel=nom,
                defaults={"quantite_reelle": qte},
            )
            saved.append(MaterielStructureSerializer(obj).data)
        return Response(saved, status=200)
    
    @action(detail=False, methods=["get"], url_path="conformity-report")
    def conformity_report(self, request):
        """
        Calculate conformity percentage for each structure by comparing:
        - PersonnelStructure vs NormePersonnel
        - ServiceStructure vs NormeService
        - MaterielStructure vs NormeMateriel
        """
        fosas = self.get_queryset()
        conformity_data = []

        for fosa in fosas:
            if not fosa.type_structure:
                conformity_data.append({
                    "code_etablissement": fosa.code_etablissement,
                    "structure": fosa.structure or fosa.nom_fr,
                    "type": fosa.type,
                    "conformity_percentage": 0,
                    "message": "Type de structure non défini",
                    "details": {
                        "personnel": {"met": 0, "total": 0},
                        "services": {"met": 0, "total": 0},
                        "materiel": {"met": 0, "total": 0},
                    }
                })
                continue

            # ✅ PERSONNEL: Compare PersonnelStructure with NormePersonnel
            from .models import NormePersonnel
            norme_personnel = NormePersonnel.objects.filter(type_structure=fosa.type_structure)
            actual_personnel = PersonnelStructure.objects.filter(structure=fosa)
            
            personnel_met = 0
            for norme in norme_personnel:
                actual = actual_personnel.filter(intitule_poste=norme.intitule_poste).first()
                if actual and actual.nombre_reel >= norme.nombre_minimal:
                    personnel_met += 1

            # ✅ SERVICES: Compare ServiceStructure with NormeService
            from .models import NormeService
            norme_services = NormeService.objects.filter(type_structure=fosa.type_structure, obligatoire=True)
            actual_services = ServiceStructure.objects.filter(structure=fosa)
            
            services_met = 0
            for norme in norme_services:
                actual = actual_services.filter(nom_service=norme.nom_service, disponible=True).first()
                if actual:
                    services_met += 1

            # ✅ MATERIEL: Compare MaterielStructure with NormeMateriel
            from .models import NormeMateriel
            norme_materiel = NormeMateriel.objects.filter(type_structure=fosa.type_structure)
            actual_materiel = MaterielStructure.objects.filter(structure=fosa)
            
            materiel_met = 0
            for norme in norme_materiel:
                actual = actual_materiel.filter(nom_materiel=norme.nom_materiel).first()
                if actual and actual.quantite_reelle >= norme.quantite_minimale:
                    materiel_met += 1

            # ✅ Calculate overall conformity
            total_norms = len(norme_personnel) + len(norme_services) + len(norme_materiel)
            total_met = personnel_met + services_met + materiel_met
            conformity_percentage = (total_met / total_norms * 100) if total_norms > 0 else 0

            conformity_data.append({
                "code_etablissement": fosa.code_etablissement,
                "structure": fosa.structure or fosa.nom_fr,
                "type": fosa.type,
                "conformity_percentage": round(conformity_percentage, 2),
                "message": f"Conformité: {total_met}/{total_norms} normes respectées",
                "details": {
                    "personnel": {"met": personnel_met, "total": len(norme_personnel)},
                    "services": {"met": services_met, "total": len(norme_services)},
                    "materiel": {"met": materiel_met, "total": len(norme_materiel)},
                }
            })

        return Response(conformity_data)
    



# Vue Historique
class FOSAHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    fosa_code = serializers.CharField(source='fosa.code_etablissement', read_only=True)

    class Meta:
        model = FOSAHistory
        fields = ['id', 'fosa', 'fosa_code', 'user', 'username', 'action', 'changes', 'created_at']
        read_only_fields = ['id', 'created_at']


class FOSAHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FOSAHistorySerializer
    queryset = FOSAHistory.objects.select_related('fosa', 'user').all()
    permission_classes = [permissions.IsAuthenticated ,CustomModelPermissions, FOSARolePermission]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.filter(fosa__is_public=True)

        if getattr(user, "is_superuser", False):
            return qs

        role = getattr(getattr(user, "role", None), "nom", None)

        # --- Administrateur national ---
        if role == "Administrateur national":
            return qs

        # --- Gestionnaire régional ---
        if role == "gestionnaire régional":
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))
            wilaya_noms = list(user.wilayas.values_list("nom", flat=True))

            return qs.filter(
                Q(fosa__wilaya_fk_id__in=wilaya_ids) |
                Q(fosa__wilaya__in=wilaya_noms)
            )

        # --- Gestionnaire local ---
        if role == "gestionnaire local":
            wilaya_ids = list(user.wilayas.values_list("id", flat=True))
            wilaya_noms = list(user.wilayas.values_list("nom", flat=True))

            q = qs.filter(
                Q(fosa__moughataa_fk_id=user.moughataa_fk_id) |
                Q(fosa__moughataa=user.moughataa.nom, fosa__wilaya__in=wilaya_noms)
            )



            return q

        # --- Utilisateurs publics ---
        return qs.filter(fosa__is_public=True)


import csv, io, json
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser,JSONParser, FormParser
from rest_framework.response import Response
from rest_framework import permissions

def to_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ('true', '1', 'oui', 'yes', 'o')
    return bool(v)

def to_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except:
            return [x.strip() for x in v.split(',')]
    return []


# ============================================================
# NORMS VIEWSETS (Normes)
# ============================================================
from .models import NormePersonnel, NormeService, NormeMateriel

class TypeStructureViewSet(viewsets.ModelViewSet):
    queryset = TypeStructure.objects.all().order_by("libelle")
    serializer_class = TypeStructureSerializer

class NormePersonnelViewSet(viewsets.ModelViewSet):
    queryset = NormePersonnel.objects.all()
    serializer_class = NormePersonnelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        type_structure = self.request.query_params.get("type_structure")
        # ✅ FIX: Only filter if type_structure is not null/None
        if type_structure and type_structure != "null":
            try:
                qs = qs.filter(type_structure_id=int(type_structure))
            except (ValueError, TypeError):
                pass
        return qs.order_by("intitule_poste")


class NormeServiceViewSet(viewsets.ModelViewSet):
    queryset = NormeService.objects.all()
    serializer_class = NormeServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        type_structure = self.request.query_params.get("type_structure")
        # ✅ FIX: Only filter if type_structure is not null/None
        if type_structure and type_structure != "null":
            try:
                qs = qs.filter(type_structure_id=int(type_structure))
            except (ValueError, TypeError):
                pass
        return qs.order_by("nom_service")


class NormeMaterielViewSet(viewsets.ModelViewSet):
    queryset = NormeMateriel.objects.all()
    serializer_class = NormeMaterielSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        type_structure = self.request.query_params.get("type_structure")
        # ✅ FIX: Only filter if type_structure is not null/None
        if type_structure and type_structure != "null":
            try:
                qs = qs.filter(type_structure_id=int(type_structure))
            except (ValueError, TypeError):
                pass
        return qs.order_by("nom_materiel")
    
from django.db.models import Q
from rest_framework import viewsets


# class StructureSanteViewSet(viewsets.ModelViewSet):
#     queryset = StructureSante.objects.select_related(
#         "type_structure", "wilaya_fk", "moughataa_fk", "commune_fk"
#     ).all()
#     serializer_class = StructureSanteSerializer
#     parser_classes = [MultiPartParser]
#     permission_classes = [permissions.IsAuthenticated ,CustomModelPermissions, FOSARolePermission]

#     def get_queryset(self):
#         qs = super().get_queryset()


