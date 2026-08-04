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
import csv
from rest_framework.permissions import AllowAny
# fosa/views_geo.py
from rest_framework import viewsets, filters
from .models import Wilaya, Moughataa, Commune
from .serializers import  FOSASerializer, WilayaSerializer, MoughataaSerializer, CommuneSerializer
from accounts.permissions import CustomModelPermissions  # si tu veux verrouiller CRUD


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

#=====
#MOBILE MODIFICATION
#=====
MOBILE_TOKEN = "msr-sante-2026-mobile-key"
 
def is_mobile_request(request):
    return request.headers.get("X-Mobile-Token") == MOBILE_TOKEN
 
class WilayaViewSet(viewsets.ModelViewSet):
    serializer_class = WilayaSerializer  
 
    def get_permissions(self):
        if self.action == "mobile":
            return [AllowAny()]
        return [permissions.IsAuthenticated()]
 
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
        
        if role == "rapporteur":
            return qs.filter(id=user.fosa_fk.wilaya_fk_id)
    
        if role in ("gestionnaire régional", "gestionnaire local"):
            wilaya_ids  = list(user.wilayas.values_list("id", flat=True))
            wilaya_noms = list(user.wilayas.values_list("nom", flat=True))
            return qs.filter(Q(id__in=wilaya_ids) | Q(nom__in=wilaya_noms))
 
        return qs.none()
 
    @action(detail=False, methods=["get"], url_path="mobile", permission_classes=[AllowAny])
    def mobile(self, request):
        print("HEADERS:", dict(request.headers))
        print("TOKEN:", request.headers.get("X-Mobile-Token"))

        if not is_mobile_request(request):
            return Response(
               {
                "received": request.headers.get("X-Mobile-Token"),
                "expected": MOBILE_TOKEN,
              },
            status=403,
        )

        wilayas = Wilaya.objects.all().order_by("nom").values("id", "nom")
        return Response(list(wilayas))
 
 
class MoughataaViewSet(viewsets.ModelViewSet):
    serializer_class = MoughataaSerializer
    filterset_fields = ["wilaya"]
    search_fields    = ["nom", "code", "wilaya__nom"]
 
    def get_permissions(self):
        if self.action == "mobile":
            return [AllowAny()]
        return [permissions.IsAuthenticated()]
 
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
        if role == "rapporteur":
           return qs.filter(id=user.fosa_fk.moughataa_fk_id)
            
        if role == "gestionnaire régional":
            wilaya_ids  = list(user.wilayas.values_list("id", flat=True))
            wilaya_noms = list(user.wilayas.values_list("nom", flat=True))
            return qs.filter(
                Q(wilaya_id__in=wilaya_ids) | Q(wilaya__nom__in=wilaya_noms)
            )
 
        if role == "gestionnaire local":
            return qs.filter(
                Q(id=user.moughataa_fk_id) |
                Q(nom=getattr(user.moughataa_fk, "nom", None))
            )
 
        return qs.none()
 
    # ── GET /api/moughataas/mobile/?wilaya=3 ────────────────────────
    # ✅ FIXED: only ONE mobile method, filters by wilaya param
    @action(detail=False, methods=["get"], url_path="mobile", permission_classes=[AllowAny])
    def mobile(self, request):
        if not is_mobile_request(request):
            return Response({"detail": "Token mobile requis."}, status=403)
 
        wilaya_id = request.query_params.get("wilaya")
 
        qs = Moughataa.objects.select_related("wilaya").all().order_by("nom")
 
        # ✅ Filter by wilaya if provided
        if wilaya_id:
            try:
                qs = qs.filter(wilaya_id=int(wilaya_id))
            except (ValueError, TypeError):
                return Response({"detail": "wilaya param invalide"}, status=400)
 
        data = list(qs.values("id", "nom", "wilaya_id"))
        return Response(data)
 

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
        if role == "rapporteur":
            return qs.filter(id=user.fosa_fk.commune_fk_id)
            
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
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated ,CustomModelPermissions, FOSARolePermission]

    def post(self, request):
        f = request.FILES.get("file")
        update_if_exists = (request.data.get("update_if_exists") or "").lower() == "true"
        if not f:
            return Response({"detail": "Aucun fichier reçu (clé 'file')."}, status=400)

        temp_path = default_storage.save(f"tmp/geo_import/{f.name}", ContentFile(f.read()))
        absolute = default_storage.path(temp_path)

        try:
            stats = import_geo_from_xlsx(absolute, update_if_exists=update_if_exists)
            return Response({"status": "ok", "update_if_exists": update_if_exists, "stats": stats})
        except Exception as e:
            return Response({"status": "error", "detail": str(e)}, status=400)
        finally:
            # nettoyage best-effort
            try:
                default_storage.delete(temp_path)
            except Exception:
                pass

class FOSAResource(resources.ModelResource):
    class Meta:
        model = FOSA
        import_id_fields = ['code_etablissement']
        fields = (
            'code_etablissement',
            'structure',               # nouveau nom principal
            'nom_fr',
            'nom_ar',
            'type',
            'type_structure',          # nouveau champ (code ou libellé)
            'departement',
            'responsable',
            'adresse',
            'commune',
            'moughataa',
            'wilaya',
            'coordonnees',
            'latitude',
            'longitude',
            'is_public',
            # nouveaux champs de StructureSante
            'etat',
            'etat_batiment',
            'cloture',
            'electricite',
            'internet',
            'eau',
            'cdf',
            'equipement',
            'date_de_construction',
            'fosa_reference',
            'fosa_plus_proche',
            'prestation_service',
            'service_manquant',
            'besoins',
            'pourcentage_activite',
            'observation',
            'bailleur',
            'source_file',
        )
        skip_unchanged = True
        report_skipped = True
        use_transactions = False

    TYPE_MAPPING = {
        'poste de santé': 'PS',
        'PS': 'PS',
        'centre de santé': 'CS',
        'CS': 'CS',
        'CH': 'CH',
        'direction régionale de santé': 'DRS',
        'DRS': 'DRS',
        'direction centrale': 'DAF',
        'DAF': 'DAF',
        'FOND': 'FOND',
        'autres': 'AUTRE',
    }

    # ------------------------------------------------------------
    # Helpers de nettoyage
    # ------------------------------------------------------------
    def parse_bool(self, value):
        if value is None:
            return None
        s = str(value).strip().lower()
        if s in ('1', 'true', 'vrai', 'oui', 'y', 'yes'):
            return True
        if s in ('0', 'false', 'faux', 'non', 'n', 'no'):
            return False
        return None

    def parse_list(self, value):
        if value is None:
            return []
        s = str(value).strip()
        if not s:
            return []
        if s.startswith('[') and s.endswith(']'):
            try:
                obj = json.loads(s)
                if isinstance(obj, list):
                    return obj
            except:
                pass
        if ';' in s:
            return [x.strip() for x in s.split(';') if x.strip()]
        if ',' in s:
            return [x.strip() for x in s.split(',') if x.strip()]
        return [s]

    def clean_type(self, raw_value):
        if not raw_value:
            return "AUTRE"
        value = str(raw_value).strip().replace("é", "e")
        return self.TYPE_MAPPING.get(value, "AUTRE")

    def clean_coordinates(self, row):
        lat = row.get('latitude', '')
        lon = row.get('longitude', '')
        if lat in ('', ',', 'nan', 'none', None, 'None'):
            row['latitude'] = None
        else:
            try:
                if isinstance(lat, str):
                    row['latitude'] = float(lat.strip())
                else:
                    row['latitude'] = float(lat)
            except (ValueError, TypeError):
                raise ValueError(f"Latitude invalide : {lat}")

        if lon in ('', ',', 'nan', 'none', None, 'None'):
            row['longitude'] = None
        else:
            try:
                if isinstance(lon, str):
                    row['longitude'] = float(lon.strip())
                else:
                    row['longitude'] = float(lon)
            except (ValueError, TypeError):
                raise ValueError(f"Longitude invalide : {lon}")

    # ------------------------------------------------------------
    # Avant importation de chaque ligne
    # ------------------------------------------------------------
    def before_import_row(self, row, **kwargs):
        # Type
        row['type'] = self.clean_type(row.get('type'))
        # Coordonnées
        self.clean_coordinates(row)
        # Booléens
        for bf in ['cloture', 'electricite', 'internet', 'eau', 'cdf']:
            row[bf] = self.parse_bool(row.get(bf))

        # Listes JSON
        row['prestation_service'] = self.parse_list(row.get('prestation_service'))
        row['service_manquant'] = self.parse_list(row.get('service_manquant'))

        # Remplir structure si vide mais nom_fr présent 
        if not row.get('structure') and row.get('nom_fr'):
            row['structure'] = row['nom_fr']

        # Validation obligatoire
        if not row.get('structure') and not row.get('nom_fr') and not row.get('nom_ar'):
            raise ValueError("Il faut au moins structure, nom_fr ou nom_ar")
        for field in ['commune', 'moughataa', 'wilaya']:
            if not row.get(field):
                raise ValueError(f"Le champ {field} est obligatoire")

    # ------------------------------------------------------------
    # Avant sauvegarde de l'instance
    # ------------------------------------------------------------
    def before_save_instance(self, instance, *args, **kwargs):
        # Public / privé
        instance.is_public = instance.type in [
            'PS', 'CS', 'CH', 'Poste de Santé', 'Centre de Santé', 'Centre hospitalier'
        ]

        # Résolution du type_structure (par code ou libellé)
        ts_val = getattr(instance, 'type_structure', None)
        if ts_val and not isinstance(ts_val, TypeStructure):
            ts = TypeStructure.objects.filter(code=ts_val).first() \
                  or TypeStructure.objects.filter(libelle=ts_val).first()
            instance.type_structure = ts

        # Remplir structure si manquant (par nom_fr)
        if not instance.structure and instance.nom_fr:
            instance.structure = instance.nom_fr
            
    def get_instance(self, instance_loader, row):
        try:
            code = row.get('code_etablissement')
            if code:
                return self._meta.model.objects.get(code_etablissement=code)
        except self._meta.model.DoesNotExist:
            return None
        return None
    
      
from django.db import transaction

# ============================================================
# FOSA VIEWSET
# ============================================================
class FOSAViewSet(viewsets.ModelViewSet):
    serializer_class = FOSASerializer
    queryset = FOSA.objects.select_related(
        "wilaya_fk", "moughataa_fk", "commune_fk", "type_structure"
    ).all()
    lookup_field = 'code_etablissement'
    lookup_url_kwarg = 'code_etablissement'
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

    # ============================================================
    # FILTRAGE PAR RÔLE
    # ============================================================
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
        
        if role == "rapporteur":
            return qs.filter(code_etablissement=user.fosa_fk_id)

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
    # ============================================================
    # HISTORIQUE
    # ============================================================
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
    # IMPORT / EXPORT
    # ============================================================
    @action(detail=False, methods=["post"], url_path="import_data")
    @transaction.atomic
    def import_data(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read CSV file
            decoded_file = file.read().decode("utf-8")
            csv_data = csv.DictReader(io.StringIO(decoded_file), delimiter=";")
            
            imported = 0
            updated = 0
            skipped = 0
            errors = []

            for row_idx, row in enumerate(csv_data, start=2):  # Start at 2 (header is row 1)
                try:
                    # ✅ Get or create Wilaya by name
                    wilaya_name = row.get("wilaya", "").strip()
                    wilaya_fk = None
                    if wilaya_name:
                        wilaya_fk, _ = Wilaya.objects.get_or_create(
                            nom__iexact=wilaya_name,
                            defaults={"nom": wilaya_name}
                        )

                    # ✅ Get or create Moughataa by name (linked to Wilaya)
                    moughataa_name = row.get("moughataa", "").strip()
                    moughataa_fk = None
                    if moughataa_name and wilaya_fk:
                        moughataa_fk, _ = Moughataa.objects.get_or_create(
                            nom__iexact=moughataa_name,
                            wilaya=wilaya_fk,
                            defaults={"nom": moughataa_name, "wilaya": wilaya_fk}
                        )

                    # ✅ Get or create Commune by name (linked to Moughataa)
                    commune_name = row.get("commune", "").strip()
                    commune_fk = None
                    if commune_name and moughataa_fk:
                        commune_fk, _ = Commune.objects.get_or_create(
                            nom__iexact=commune_name,
                            moughataa=moughataa_fk,
                            defaults={"nom": commune_name, "moughataa": moughataa_fk}
                        )

                    # ✅ Get TypeStructure by code
                    type_code = row.get("type", "").strip().upper()
                    type_structure = None
                    if type_code:
                        type_structure = TypeStructure.objects.filter(code__iexact=type_code).first()

                    # ✅ Parse boolean fields
                    def parse_bool(val):
                        if not val:
                            return None
                        val = str(val).strip().lower()
                        if val in ["oui", "yes", "true", "1"]:
                            return True
                        elif val in ["non", "no", "false", "0"]:
                            return False
                        return None

                    # ✅ Build FOSA data
                    code = row.get("code", "").strip()
                    if not code:
                        errors.append(f"Row {row_idx}: Missing code")
                        skipped += 1
                        continue

                    fosa_data = {
                        "structure": row.get("structure", "").strip(),
                        "nom_ar": row.get("nom_ar", "").strip(),
                        "nom_fr": row.get("structure", "").strip(),
                        "type": row.get("type", "").strip(),
                        "etat": row.get("etat", "").strip(),
                        "departement": row.get("departement", "").strip(),
                        "etat_batiment": row.get("etat_batiment", "").strip(),
                        "equipement": row.get("equipement", "").strip(),
                        "coordonnee_gps": row.get("cordonnee", "").strip(),  # Note: CSV has typo "cordonnee"
                        "responsable": row.get("responsable", "").strip(),
                        "date_de_construction": row.get("date_de_construction", "").strip() or None,
                        "fosa_reference": row.get("fosa_reference", "").strip(),
                        "fosa_plus_proche": row.get("fosa_plus_proche", "").strip(),
                        "bailleur": row.get("bailleur", "").strip(),
                        "besoins": row.get("besoins", "").strip(),
                        "observation": row.get("observation", "").strip() or row.get("remarque", "").strip(),
                        "pourcentage_activite": row.get("pourcentage_activite", "").strip(),
                        
                        # ✅ Boolean fields
                        "internet": parse_bool(row.get("internet")),
                        "eau": parse_bool(row.get("eau")),
                        "electricite": parse_bool(row.get("electricite")),
                        "cloture": parse_bool(row.get("cloture")),
                        
                        # ✅ Foreign keys
                        "wilaya_fk": wilaya_fk,
                        "moughataa_fk": moughataa_fk,
                        "commune_fk": commune_fk,
                        "type_structure": type_structure,
                        
                        # ✅ Set wilaya/moughataa/commune text fields
                        "wilaya": wilaya_name or "Inconnu",
                        "moughataa": moughataa_name or "Inconnu",
                        "commune": commune_name or "Inconnu",
                    }

                    # ✅ Update or create
                    obj, created = FOSA.objects.update_or_create(
                        code_etablissement=code,
                        defaults=fosa_data
                    )

                    if created:
                        imported += 1
                    else:
                        updated += 1

                except Exception as e:
                    errors.append(f"Row {row_idx}: {str(e)}")
                    skipped += 1
                    continue

            return Response({
                "imported": imported,
                "updated": updated,
                "skipped": skipped,
                "errors": errors[:10]  # Return first 10 errors
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"Import failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action(detail=False, methods=['get'])
    def export_data(self, request):
        resource = FOSAResource()
        dataset = resource.export()
        resp = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="fosas_export.xlsx"'
        return resp

    # ============================================================
    # PERSONNEL ACTIONS
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

    # ============================================================
    # SERVICES ACTIONS
    # ============================================================
    @action(detail=True, methods=["get"])
    def services(self, request, code_etablissement=None):
        """Get all services for this structure"""
        fosa = self.get_object()
        qs = fosa.services.all().order_by("nom_service")
        return Response(ServiceStructureSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="services/upsert")
    def services_upsert(self, request, code_etablissement=None):
        """Upsert multiple service items"""
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

    # ============================================================
    # MATERIEL ACTIONS
    # ============================================================
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

    # CONFORMITY REPORT
    @action(detail=False, methods=["get"], url_path="conformity-report")
    def conformity_report(self, request):
        """Calculate conformity percentage for each structure"""
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
            from .models import NormePersonnel, NormeService, NormeMateriel, PersonnelStructure, ServiceStructure, MaterielStructure
            
            norme_personnel = NormePersonnel.objects.filter(type_structure=fosa.type_structure)
            actual_personnel = PersonnelStructure.objects.filter(structure=fosa)
            
            personnel_met = 0
            for norme in norme_personnel:
                actual = actual_personnel.filter(intitule_poste=norme.intitule_poste).first()
                if actual and actual.nombre_reel >= norme.nombre_minimal:
                    personnel_met += 1

            # ✅ SERVICES: Compare ServiceStructure with NormeService
            norme_services = NormeService.objects.filter(type_structure=fosa.type_structure, obligatoire=True)
            actual_services = ServiceStructure.objects.filter(structure=fosa)
            
            services_met = 0
            for norme in norme_services:
                actual = actual_services.filter(nom_service=norme.nom_service, disponible=True).first()
                if actual:
                    services_met += 1

            # ✅ MATERIEL: Compare MaterielStructure with NormeMateriel
            norme_materiel = NormeMateriel.objects.filter(type_structure=fosa.type_structure)
            actual_materiel = MaterielStructure.objects.filter(structure=fosa)
            
            materiel_met = 0
            for norme in norme_materiel:
                actual = actual_materiel.filter(nom_materiel=norme.nom_materiel).first()
                if actual and actual.quantite_reelle >= norme.quantite_minimale:
                    materiel_met += 1

            # ✅ Calculate total conformity percentage
            total_normes = norme_personnel.count() + norme_services.count() + norme_materiel.count()
            total_met = personnel_met + services_met + materiel_met

            if total_normes == 0:
                conformity_percentage = 0
                message = "Aucune norme définie"
            else:
                conformity_percentage = int((total_met / total_normes) * 100)
                message = f"{total_met}/{total_normes} normes respectées"

            conformity_data.append({
                "code_etablissement": fosa.code_etablissement,
                "structure": fosa.structure or fosa.nom_fr,
                "type": fosa.type,
                "wilaya": fosa.wilaya_fk.nom or fosa.wilaya,
                "moughataa": fosa.moughataa_fk.nom or fosa.moughataa,
                "conformity_percentage": conformity_percentage,
                "message": message,
                "details": {
                    "personnel": {
                        "met": personnel_met,
                        "total": norme_personnel.count(),
                    },
                    "services": {
                        "met": services_met,
                        "total": norme_services.count(),
                    },
                    "materiel": {
                        "met": materiel_met,
                        "total": norme_materiel.count(),
                    },
                }
            })

        return Response(conformity_data)  
    ###--------------
    #MOBILE SECTION
    ###-------------
    def get_permissions(self):
        
        if self.action == "mobile":
            return [AllowAny()]
        return [
            permissions.IsAuthenticated(),
            CustomModelPermissions(),
            FOSARolePermission(),
        ]
    
    @action(detail=False, methods=["get"], url_path="mobile", permission_classes=[AllowAny])
    def mobile(self, request):
        if not is_mobile_request(request):
            return Response({"detail": "Token mobile requis."}, status=403)
 
        moughataa_id = request.query_params.get("moughataa")
        wilaya_id    = request.query_params.get("wilaya")
 
        # ✅ Query directly — bypass get_queryset() which requires auth
        qs = FOSA.objects.select_related(
            "wilaya_fk", "moughataa_fk"
        ).all().order_by("structure")
 
        if moughataa_id:
            try:
                mid = int(moughataa_id)
                moughataa_obj = Moughataa.objects.filter(id=mid).first()
                if moughataa_obj:
                    qs = qs.filter(
                        Q(moughataa_fk_id=mid) |
                        Q(moughataa__iexact=moughataa_obj.nom)
                    )
                else:
                    qs = qs.filter(moughataa_fk_id=mid)
            except (ValueError, TypeError):
                return Response({"detail": "moughataa param invalide"}, status=400)
 
        if wilaya_id:
            try:
                wid = int(wilaya_id)
                wilaya_obj = Wilaya.objects.filter(id=wid).first()
                if wilaya_obj:
                    qs = qs.filter(
                        Q(wilaya_fk_id=wid) |
                        Q(wilaya__iexact=wilaya_obj.nom)
                    )
                else:
                    qs = qs.filter(wilaya_fk_id=wid)
            except (ValueError, TypeError):
                return Response({"detail": "wilaya param invalide"}, status=400)
 
        data = list(qs.values(
            "code_etablissement", "structure", "nom_fr",
            "moughataa", "wilaya"
        ))
        return Response(data)
 
class FOSAHistorySerializer(serializers.ModelSerializer):
    fosa_code_etablissement = serializers.ReadOnlyField(source='fosa.code_etablissement')
    fosa_nom_fr = serializers.ReadOnlyField(source='fosa.nom_fr')
    fosa_nom_ar = serializers.ReadOnlyField(source='fosa.nom_ar')
    username = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = FOSAHistory
        fields = ['fosa_code_etablissement', 'fosa_nom_fr', 'fosa_nom_ar',
                  'username', 'action', 'changes', 'timestamp']



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
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("1", "true", "vrai", "oui", "y", "yes"):
        return True
    if s in ("0", "false", "faux", "non", "n", "no"):
        return False
    return None

def to_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    s = str(v).strip()
    if not s:
        return []

    if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
        try:
            obj = json.loads(s)
            return obj if isinstance(obj, list) else []
        except Exception:
            pass

    if ";" in s:
        return [x.strip() for x in s.split(";") if x.strip()]
    if "," in s:
        return [x.strip() for x in s.split(",") if x.strip()]

    return [s]


from .models import Maladie, MaladieReport
from .serializers import MaladieSerializer, MaladieReportSerializer

class MaladieViewSet(viewsets.ModelViewSet):
    queryset = Maladie.objects.all().order_by("name")
    serializer_class = MaladieSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [permissions.IsAuthenticated ,CustomModelPermissions, FOSARolePermission]

from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime, timedelta
import io

class MaladieReportViewSet(viewsets.ModelViewSet):
    queryset = MaladieReport.objects.select_related("wilaya", "moughataa", "maladie").all()
    serializer_class = MaladieReportSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_permissions(self):
        if self.action in ("create", "list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [
            permissions.IsAuthenticated(),
            CustomModelPermissions(),
            FOSARolePermission(),
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # ── Role-based scoping ──────────────────────────────
        if not user.is_authenticated:
            return qs.none()

        if not user.is_superuser:
            role = getattr(getattr(user, "role", None), "nom", None)
            if role == "Administrateur national":
                pass  # sees everything
            elif role == "gestionnaire régional":
                wilaya_ids = list(user.wilayas.values_list("id", flat=True))
                qs = qs.filter(wilaya_id__in=wilaya_ids)

            elif role == "gestionnaire local":
                qs = qs.filter(moughataa_id=user.moughataa_fk_id)

            elif role == "rapporteur":
                qs = qs.filter(submitted_by=user)

            else:
                return qs.none()
        # ── Query param filters ─────────────────────────────
        date       = self.request.query_params.get("date")
        date_start = self.request.query_params.get("date_start")
        date_end   = self.request.query_params.get("date_end")
        wilaya     = self.request.query_params.get("wilaya")
        moughataa  = self.request.query_params.get("moughataa")
        maladie    = self.request.query_params.get("maladie")
        status_f   = self.request.query_params.get("status")

        if date:
            qs = qs.filter(date=date)
        if date_start and date_end:
            qs = qs.filter(date__range=[date_start, date_end])
        if wilaya:
            qs = qs.filter(wilaya_id=wilaya)
        if moughataa:
            qs = qs.filter(moughataa_id=moughataa)
        if maladie:
            qs = qs.filter(maladie_id=maladie)
        if status_f:
            qs = qs.filter(status=status_f)

        return qs.order_by("date", "wilaya_id", "moughataa_id", "maladie_id")

    def perform_create(self, serializer):
        serializer.save(
            submitted_by=self.request.user,
            status="submitted",
        )
    
    @action(detail=False, methods=["post"], url_path="upsert")
    def upsert(self, request):
        key_fields = ["date", "wilaya", "moughataa", "maladie"]
        missing = [f for f in key_fields if f not in request.data]
        if missing:
            return Response({"detail": f"Champs manquants: {missing}"}, status=400)

        obj = MaladieReport.objects.filter(
            date=request.data["date"],
            wilaya_id=request.data["wilaya"],
            moughataa_id=request.data["moughataa"],
            maladie_id=request.data["maladie"],
        ).first()

        if obj:
            ser = self.get_serializer(obj, data=request.data, partial=False)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="export-weekly")
    def export_weekly(self, request):
        date_start = request.query_params.get("date_start")
        date_end = request.query_params.get("date_end")

        if not date_start or not date_end:
            return Response(
                {"detail": "date_start and date_end are required (format: YYYY-MM-DD)"},
                status=400
            )

        try:
            start = datetime.strptime(date_start, "%Y-%m-%d").date()
            end = datetime.strptime(date_end, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        week_num = start.isocalendar()[1]

        reports = MaladieReport.objects.filter(
            date__range=[start, end]
        ).select_related("wilaya", "moughataa", "maladie").order_by(
            "wilaya__nom", "moughataa__nom", "maladie__name"
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport Hebdomadaire"

        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        title_font = Font(bold=True, size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        title_cell.value = "NOTIFICATION DES MALADIES ET EVENEMENTS"
        title_cell.font = title_font
        title_cell.alignment = center_align

        ws.merge_cells("A2:H2")
        week_cell = ws["A2"]
        week_cell.value = f"Sem. Épid. N° : {week_num:02d}  du {start.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}"
        week_cell.font = Font(bold=True, size=10)
        week_cell.alignment = center_align

        row = 4
        stats = [
            ("Nombre de rapports attendus des Moughataas", len(set(reports.values_list("moughataa_id", flat=True)))),
            ("Nombre de rapports reçus des Moughataas", len(set(reports.values_list("moughataa_id", flat=True)))),
            ("Nombre de rapports reçus à temps des Moughataas", len(set(reports.values_list("moughataa_id", flat=True)))),
        ]

        for stat_label, stat_value in stats:
            ws[f"A{row}"] = stat_label
            ws[f"B{row}"] = stat_value
            ws[f"C{row}"] = f"{100}%"
            row += 1

        row = 8
        headers = ["Wilaya", "Moughataa", "Maladie", "Cas Suspects", "Décès", "Cas Prélevés", "Cas Testés", "Cas Confirmés"]

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = border

        row = 9
        for report in reports:
            ws.cell(row=row, column=1).value = report.wilaya.nom
            ws.cell(row=row, column=2).value = report.moughataa.nom
            ws.cell(row=row, column=3).value = report.maladie.name
            ws.cell(row=row, column=4).value = report.cas_suspects or 0
            ws.cell(row=row, column=5).value = report.deces or 0
            ws.cell(row=row, column=6).value = report.cas_preleves or 0
            ws.cell(row=row, column=7).value = report.cas_testes or 0
            ws.cell(row=row, column=8).value = report.cas_confirmes or 0

            for col in range(1, 9):
                ws.cell(row=row, column=col).border = border
                ws.cell(row=row, column=col).alignment = center_align

            row += 1

        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 30
        for col in ["D", "E", "F", "G", "H"]:
            ws.column_dimensions[col].width = 15

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"Rapport_Epid_Sem_{week_num:02d}_{start.strftime('%Y%m%d')}_au_{end.strftime('%Y%m%d')}.xlsx"

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    @action(detail=False, methods=["get"], url_path="export-daily")
    def export_daily(self, request):
        date = request.query_params.get("date")

        if not date:
            return Response({"detail": "date parameter is required (format: YYYY-MM-DD)"}, status=400)

        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        reports = MaladieReport.objects.filter(
            date=date
        ).select_related("wilaya", "moughataa", "maladie").order_by(
            "wilaya__nom", "moughataa__nom", "maladie__name"
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport Journalier"

        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        title_font = Font(bold=True, size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        title_cell.value = "NOTIFICATION DES MALADIES ET EVENEMENTS"
        title_cell.font = title_font
        title_cell.alignment = center_align

        ws.merge_cells("A2:H2")
        date_cell = ws["A2"]
        date_cell.value = f"Rapport du {date_obj.strftime('%d/%m/%Y')}"
        date_cell.font = Font(bold=True, size=10)
        date_cell.alignment = center_align

        row = 4
        headers = ["Wilaya", "Moughataa", "Maladie", "Cas Suspects", "Décès", "Cas Prélevés", "Cas Testés", "Cas Confirmés"]

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = border

        row = 5
        for report in reports:
            ws.cell(row=row, column=1).value = report.wilaya.nom if report.wilaya else "-"
            ws.cell(row=row, column=2).value = report.moughataa.nom if report.moughataa else "-"
            ws.cell(row=row, column=3).value = report.maladie.name if report.maladie else "-"
            ws.cell(row=row, column=4).value = report.cas_suspects or 0
            ws.cell(row=row, column=5).value = report.deces or 0
            ws.cell(row=row, column=6).value = report.cas_preleves or 0
            ws.cell(row=row, column=7).value = report.cas_testes or 0
            ws.cell(row=row, column=8).value = report.cas_confirmes or 0

            for col in range(1, 9):
                ws.cell(row=row, column=col).border = border
                ws.cell(row=row, column=col).alignment = center_align

            row += 1

        for col in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            ws.column_dimensions[col].width = 18

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"Rapport_Maladie_{date}.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
     
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    TypeStructure,
    NormePersonnel, NormeService, NormeMateriel,
    PersonnelStructure, ServiceStructure, MaterielStructure
)


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
    
#initvalues
class FosaInitDefaultsViewSet(viewsets.ViewSet):
    """
    Endpoints:
      POST /api/fosa-init/{code_etablissement}/init/   → init one FOSA
      POST /api/fosa-init/init-all/                    → init ALL FOSA (bulk)
      GET  /api/fosa-init/{code_etablissement}/status/ → check init status
      POST /api/fosa-init/{code_etablissement}/reset/  → reset to 0 (keep rows, reset values)
    """
    permission_classes = [permissions.IsAuthenticated]
 
    def _init_fosa(self, fosa):
        """
        Core logic: create PersonnelStructure, ServiceStructure, MaterielStructure
        for a FOSA based on its type_structure norms.
        Uses get_or_create so it's safe to call multiple times — no duplicates.
        Returns dict with created/skipped counts.
        """
        if not fosa.type_structure:
            return None  # Signal: no type defined
 
        counts = {
            "personnel": {"created": 0, "skipped": 0},
            "services":  {"created": 0, "skipped": 0},
            "materiel":  {"created": 0, "skipped": 0},
        }
 
        # ── Personnel ──────────────────────────────────────
        for norme in NormePersonnel.objects.filter(type_structure=fosa.type_structure):
            _, created = PersonnelStructure.objects.get_or_create(
                structure=fosa,
                intitule_poste=norme.intitule_poste,
                defaults={"nombre_reel": 0},
            )
            if created:
                counts["personnel"]["created"] += 1
            else:
                counts["personnel"]["skipped"] += 1
 
        # ── Services ───────────────────────────────────────
        for norme in NormeService.objects.filter(type_structure=fosa.type_structure):
            _, created = ServiceStructure.objects.get_or_create(
                structure=fosa,
                nom_service=norme.nom_service,
                defaults={"disponible": False},
            )
            if created:
                counts["services"]["created"] += 1
            else:
                counts["services"]["skipped"] += 1
 
        # ── Matériel ───────────────────────────────────────
        for norme in NormeMateriel.objects.filter(type_structure=fosa.type_structure):
            _, created = MaterielStructure.objects.get_or_create(
                structure=fosa,
                nom_materiel=norme.nom_materiel,
                defaults={"quantite_reelle": 0},
            )
            if created:
                counts["materiel"]["created"] += 1
            else:
                counts["materiel"]["skipped"] += 1
 
        return counts
    # ──────────────────────────────────────────────────────
    # POST /api/fosa-init/{code}/init/
    # Initialize one FOSA
    # ──────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="init")
    @transaction.atomic
    def init_one(self, request, pk=None):
        try:
            fosa = FOSA.objects.select_related("type_structure").get(
                code_etablissement=pk
            )
        except FOSA.DoesNotExist:
            return Response(
                {"detail": f"FOSA '{pk}' introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        counts = self._init_fosa(fosa)
 
        if counts is None:
            return Response(
                {
                    "detail": "Type de structure non défini pour cette FOSA. Veuillez d'abord assigner un type.",
                    "fosa": pk,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        total_created = sum(v["created"] for v in counts.values())
 
        return Response(
            {
                "detail": "Initialisation réussie." if total_created > 0 else "Déjà initialisé — aucune nouvelle entrée.",
                "fosa": fosa.code_etablissement,
                "type_structure": fosa.type_structure.code,
                "created": {k: v["created"] for k, v in counts.items()},
                "skipped": {k: v["skipped"] for k, v in counts.items()},
            },
            status=status.HTTP_200_OK,
        )
 
    # ──────────────────────────────────────────────────────
    # POST /api/fosa-init/init-all/
    # Bulk init ALL FOSA (or filtered by type_structure)
    # Optional query param: ?type_structure=CSA
    # ──────────────────────────────────────────────────────
    @action(detail=False, methods=["post"], url_path="init-all")
    @transaction.atomic
    def init_all(self, request):
        type_code = request.query_params.get("type_structure")
 
        qs = FOSA.objects.select_related("type_structure").all()
        if type_code:
            qs = qs.filter(type_structure__code__iexact=type_code)
 
        total_fosas = qs.count()
        if total_fosas == 0:
            return Response(
                {"detail": "Aucune FOSA trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        results = {
            "total_fosas": total_fosas,
            "initialized": 0,
            "skipped_no_type": 0,
            "created": {"personnel": 0, "services": 0, "materiel": 0},
            "skipped": {"personnel": 0, "services": 0, "materiel": 0},
            "errors": [],
        }
 
        for fosa in qs:
            try:
                counts = self._init_fosa(fosa)
                if counts is None:
                    results["skipped_no_type"] += 1
                    continue
 
                results["initialized"] += 1
                for key in ["personnel", "services", "materiel"]:
                    results["created"][key] += counts[key]["created"]
                    results["skipped"][key] += counts[key]["skipped"]
 
            except Exception as e:
                results["errors"].append(
                    {"fosa": fosa.code_etablissement, "error": str(e)}
                )
 
        return Response(results, status=status.HTTP_200_OK)
 
    # ──────────────────────────────────────────────────────
    # GET /api/fosa-init/{code}/status/
    # Check how many normes are filled vs total for a FOSA
    # ──────────────────────────────────────────────────────
    @action(detail=True, methods=["get"], url_path="status")
    def status(self, request, pk=None):
        try:
            fosa = FOSA.objects.select_related("type_structure").get(
                code_etablissement=pk
            )
        except FOSA.DoesNotExist:
            return Response(
                {"detail": f"FOSA '{pk}' introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        if not fosa.type_structure:
            return Response(
                {"detail": "Type de structure non défini.", "fosa": pk},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        ts = fosa.type_structure
 
        # Norme totals (what SHOULD exist)
        norme_personnel_count = NormePersonnel.objects.filter(type_structure=ts).count()
        norme_service_count   = NormeService.objects.filter(type_structure=ts).count()
        norme_materiel_count  = NormeMateriel.objects.filter(type_structure=ts).count()
 
        # Actual totals (what EXISTS for this FOSA)
        actual_personnel = PersonnelStructure.objects.filter(structure=fosa)
        actual_services  = ServiceStructure.objects.filter(structure=fosa)
        actual_materiel  = MaterielStructure.objects.filter(structure=fosa)
 
        # How many have real values > 0 or disponible=True
        filled_personnel = actual_personnel.filter(nombre_reel__gt=0).count()
        filled_services  = actual_services.filter(disponible=True).count()
        filled_materiel  = actual_materiel.filter(quantite_reelle__gt=0).count()
 
        total_normes = norme_personnel_count + norme_service_count + norme_materiel_count
        total_actual = actual_personnel.count() + actual_services.count() + actual_materiel.count()
        total_filled = filled_personnel + filled_services + filled_materiel
 
        is_initialized = total_actual >= total_normes and total_normes > 0
        fill_pct = round((total_filled / total_normes * 100)) if total_normes > 0 else 0
 
        return Response({
            "fosa": fosa.code_etablissement,
            "type_structure": ts.code,
            "is_initialized": is_initialized,
            "fill_percentage": fill_pct,
            "personnel": {
                "norme_total": norme_personnel_count,
                "actual_total": actual_personnel.count(),
                "filled": filled_personnel,
            },
            "services": {
                "norme_total": norme_service_count,
                "actual_total": actual_services.count(),
                "filled": filled_services,
            },
            "materiel": {
                "norme_total": norme_materiel_count,
                "actual_total": actual_materiel.count(),
                "filled": filled_materiel,
            },
        })
 
    # ──────────────────────────────────────────────────────
    # POST /api/fosa-init/{code}/reset/
    # Reset all real values to 0 (keeps rows, resets numbers)
    # Useful when you want to re-enter data from scratch
    # ──────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="reset")
    @transaction.atomic
    def reset_one(self, request, pk=None):
        try:
            fosa = FOSA.objects.get(code_etablissement=pk)
        except FOSA.DoesNotExist:
            return Response(
                {"detail": f"FOSA '{pk}' introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        p_count = PersonnelStructure.objects.filter(structure=fosa).update(nombre_reel=0)
        s_count = ServiceStructure.objects.filter(structure=fosa).update(disponible=False)
        m_count = MaterielStructure.objects.filter(structure=fosa).update(quantite_reelle=0)
 
        return Response({
            "detail": "Valeurs réinitialisées à zéro.",
            "fosa": pk,
            "reset": {
                "personnel": p_count,
                "services": s_count,
                "materiel": m_count,
            },
        })
 
 