from accounts.permissions import CustomModelPermissions, FOSARolePermission
from rest_framework import viewsets, permissions, serializers, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
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

from .serializers import (
    FOSASerializer, WilayaSerializer, MoughataaSerializer, CommuneSerializer,
    MaladieSerializer, MaladieReportSerializer, TypeStructureSerializer,
    NormePersonnelSerializer, NormeServiceSerializer, NormeMaterielSerializer,
    PersonnelStructureSerializer, ServiceStructureSerializer, MaterielStructureSerializer,
    FOSAHistorySerializer
)

from .models import PersonnelStructure, ServiceStructure, MaterielStructure

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
    permission_classes = [permissions.IsAuthenticated]


class MaladieReportViewSet(viewsets.ModelViewSet):
    serializer_class = MaladieReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['wilaya', 'moughataa', 'maladie', 'date']
    search_fields = ['wilaya__nom', 'moughataa__nom', 'maladie__name']

    def get_queryset(self):
        qs = MaladieReport.objects.select_related('wilaya', 'moughataa', 'maladie').all()
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
            if user.moughataa_fk_id:
                return qs.filter(moughataa_fk_id=user.moughataa_fk_id)
            return qs.none()

        return qs.none()


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
