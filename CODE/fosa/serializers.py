from rest_framework import serializers
from .models import (
    FOSA,
    FOSAHistory,
    Maladie,
    MaladieReport,
    Wilaya,
    Moughataa,
    Commune,
    TypeStructure,
    NormePersonnel,
    NormeService,
    NormeMateriel,
    PersonnelStructure,
    ServiceStructure,
    MaterielStructure,
)

# ============================================================
# GÉOGRAPHIQUE
# ============================================================

class WilayaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wilaya
        fields = ["id", "nom", "code"]


class MoughataaSerializer(serializers.ModelSerializer):
    wilaya_nom = serializers.CharField(source="wilaya.nom", read_only=True)

    class Meta:
        model = Moughataa
        fields = ["id", "nom", "code", "wilaya", "wilaya_nom"]


class CommuneSerializer(serializers.ModelSerializer):
    moughataa_nom = serializers.CharField(source="moughataa.nom", read_only=True)
    wilaya_id = serializers.IntegerField(source="moughataa.wilaya_id", read_only=True)

    class Meta:
        model = Commune
        fields = ["id", "nom", "code", "moughataa", "moughataa_nom", "wilaya_id"]


# ============================================================
# MALADIES
# ============================================================

class MaladieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maladie
        fields = ["id", "name", "enabled_fields"]


class MaladieReportSerializer(serializers.ModelSerializer):
    wilaya_nom = serializers.CharField(source="wilaya.nom", read_only=True)
    moughataa_nom = serializers.CharField(source="moughataa.nom", read_only=True)
    maladie_nom = serializers.CharField(source="maladie.name", read_only=True)

    class Meta:
        model = MaladieReport
        fields = [
            "id", "date",
            "wilaya", "wilaya_nom",
            "moughataa", "moughataa_nom",
            "maladie", "maladie_nom",
            "cas_suspects", "deces", "cas_preleves", "cas_testes", "cas_confirmes",
        ]


# ============================================================
# NORMES ET TYPES
# ============================================================

class TypeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeStructure
        fields = ["id", "code", "libelle", "description"]


class NormePersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormePersonnel
        fields = ["id", "type_structure", "intitule_poste", "nombre_minimal"]


class NormeServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormeService
        fields = ["id", "type_structure", "nom_service", "obligatoire"]


class NormeMaterielSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormeMateriel
        fields = ["id", "type_structure", "nom_materiel", "quantite_minimale"]


# ============================================================
# DONNÉES RÉELLES (PERSONNEL, SERVICES, MATÉRIEL)
# ============================================================

class PersonnelStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonnelStructure
        fields = ["id", "structure", "intitule_poste", "nombre_reel"]


class ServiceStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStructure
        fields = ["id", "structure", "nom_service", "disponible"]


class MaterielStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterielStructure
        fields = ["id", "structure", "nom_materiel", "quantite_reelle"]


# ============================================================
# FOSA 
# ============================================================

class FOSASerializer(serializers.ModelSerializer):
    # Champs lisibles 
    wilaya_nom = serializers.CharField(source="wilaya_fk.nom", read_only=True)
    moughataa_nom = serializers.CharField(source="moughataa_fk.nom", read_only=True)
    commune_nom = serializers.CharField(source="commune_fk.nom", read_only=True)
    type_structure_code = serializers.CharField(source="type_structure.code", read_only=True)
    type_structure_libelle = serializers.CharField(source="type_structure.libelle", read_only=True)

    
    wilaya = serializers.CharField(source="wilaya_fk.nom", read_only=True)   # si besoin
    moughataa = serializers.CharField(source="moughataa_fk.nom", read_only=True)
    commune = serializers.CharField(source="commune_fk.nom", read_only=True)

    
    prestation_service = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    service_manquant = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    # Pour les booléens
    cloture = serializers.BooleanField(required=False, allow_null=True)
    electricite = serializers.BooleanField(required=False, allow_null=True)
    internet = serializers.BooleanField(required=False, allow_null=True)
    eau = serializers.BooleanField(required=False, allow_null=True)
    cdf = serializers.BooleanField(required=False, allow_null=True)


    coordonnee_gps = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = FOSA
        fields = [
            # Identifiants
            "code_etablissement",
            "structure",
            "nom_fr",
            "nom_ar",
            "type",
            "type_structure",
            "type_structure_code",
            "type_structure_libelle",

            # Géographie (FK)
            "wilaya_fk",
            "moughataa_fk",
            "commune_fk",
            "wilaya_nom",
            "moughataa_nom",
            "commune_nom",
            "wilaya",      
            "moughataa",
            "commune",

            # Coordonnées
            "latitude",
            "longitude",
            "coordonnee_gps",
            "adresse",

            # Infos structure
            "responsable",
            "departement",
            "etat",
            "etat_batiment",
            "date_de_construction",

            # Infrastructures
            "cloture",
            "electricite",
            "internet",
            "eau",
            "cdf",
            "equipement",

            # Références FOSA
            "fosa_reference",
            "fosa_plus_proche",

            # Services et besoins
            "prestation_service",
            "service_manquant",
            "besoins",
            "pourcentage_activite",

            # Observations
            "observation",
            "bailleur",
            "source_file",

            # Métadonnées
            "is_public",
            "created_at",
            "last_updated",
        ]
        read_only_fields = [
            "code_etablissement",
            "adresse",
            "is_public",
            "created_at",
            "last_updated",
            "coordonnee_gps"
        ]

    def validate(self, data):
        """
        Validation croisée :
        - Au moins un nom (structure ou nom_fr ou nom_ar)
        - Cohérence géographique (commune appartient à moughataa, etc.)
        - Latitude/longitude ensemble ou vides
        """
        errors = {}

        # Vérification du nom
        if not data.get("structure") and not data.get("nom_fr") and not data.get("nom_ar"):
            errors["structure"] = "Veuillez renseigner au moins le nom (structure, nom_fr ou nom_ar)."

        # Vérification des FK géographiques
        commune_fk = data.get("commune_fk")
        moughataa_fk = data.get("moughataa_fk")
        wilaya_fk = data.get("wilaya_fk")

        if commune_fk:
            if moughataa_fk and commune_fk.moughataa_id != moughataa_fk.id:
                errors["commune_fk"] = "La commune n'appartient pas à la moughataa sélectionnée."
            if wilaya_fk and commune_fk.moughataa.wilaya_id != wilaya_fk.id:
                errors["commune_fk"] = "La commune n'appartient pas à la wilaya sélectionnée."

        if moughataa_fk and wilaya_fk and moughataa_fk.wilaya_id != wilaya_fk.id:
            errors["moughataa_fk"] = "La moughataa n'appartient pas à la wilaya sélectionnée."

        # Vérification latitude/longitude
        lat = data.get("latitude")
        lon = data.get("longitude")
        if (lat is None) ^ (lon is None):
            errors["coordonnee_gps"] = "Renseignez latitude ET longitude, ou laissez les deux vides."

        if errors:
            print(errors)
            raise serializers.ValidationError(errors)

        return data

    def get_coordonnee_gps(self, obj):
        return obj.coordonnee_gps
# ============================================================
# HISTORIQUE FOSA
# ============================================================

class FOSAHistorySerializer(serializers.ModelSerializer):
    fosa_code_etablissement = serializers.ReadOnlyField(source="fosa.code_etablissement")
    fosa_nom_fr = serializers.ReadOnlyField(source="fosa.nom_fr")
    fosa_nom_ar = serializers.ReadOnlyField(source="fosa.nom_ar")
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = FOSAHistory
        fields = [
            "fosa_code_etablissement",
            "fosa_nom_fr",
            "fosa_nom_ar",
            "username",
            "action",
            "changes",
            "timestamp",
        ]