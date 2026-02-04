from rest_framework import serializers
from .models import FOSA, FOSAHistory,Maladie, MaladieReport,FIELD_KEYS
from django.contrib.auth.models import User


# fosa/serializers_geo.py
from .models import Wilaya, Moughataa, Commune

class WilayaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wilaya
        fields = ["id", "nom", "code"]


class MoughataaSerializer(serializers.ModelSerializer):
    
    wilaya = serializers.PrimaryKeyRelatedField(queryset=Wilaya.objects.all())
    
    wilaya_nom = serializers.CharField(source="wilaya.nom", read_only=True)

    class Meta:
        model = Moughataa
        fields = ["id", "nom", "code", "wilaya", "wilaya_nom"]


class CommuneSerializer(serializers.ModelSerializer):
    
    moughataa = serializers.PrimaryKeyRelatedField(queryset=Moughataa.objects.all())
    moughataa_nom = serializers.CharField(source="moughataa.nom", read_only=True)
    wilaya_id = serializers.IntegerField(source="moughataa.wilaya_id", read_only=True)

    class Meta:
        model = Commune
        fields = ["id", "nom", "code", "moughataa", "moughataa_nom", "wilaya_id"]


class MaladieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maladie
        fields = ["id", "name", "enabled_fields"]

class MaladieReportSerializer(serializers.ModelSerializer):
    wilaya_nom = serializers.CharField(source="wilaya.nom", read_only=True)
    moughataa_nom = serializers.CharField(source="moughataa.nom", read_only=True)
    maladie_nom = serializers.CharField(source="maladie.name", read_only=True)  # or name depending on model

    class Meta:
        model = MaladieReport
        fields = [
            "id", "date",
            "wilaya", "wilaya_nom",
            "moughataa", "moughataa_nom",
            "maladie", "maladie_nom",
            "cas_suspects", "deces", "cas_preleves", "cas_testes", "cas_confirmes",
        ]


from rest_framework import serializers
from .models import (
    TypeStructure,
    NormePersonnel, NormeService, NormeMateriel,
    StructureSante,
    PersonnelStructure, ServiceStructure, MaterielStructure
)

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


class StructureSanteSerializer(serializers.ModelSerializer):
    # noms lisibles (pour affichage tableau)
    wilaya_nom = serializers.CharField(source="wilaya_fk.nom", read_only=True)
    moughataa_nom = serializers.CharField(source="moughataa_fk.nom", read_only=True)
    commune_nom = serializers.CharField(source="commune_fk.nom", read_only=True)

    type_structure_code = serializers.CharField(source="type_structure.code", read_only=True)
    type_structure_libelle = serializers.CharField(source="type_structure.libelle", read_only=True)
    prestation_service = serializers.ListField(
    child=serializers.CharField(),
    required=False,allow_empty=True)
    service_manquant = serializers.ListField(
    child=serializers.CharField(),
    required=False,allow_empty=True)


    class Meta:
        model = StructureSante
        fields = [
            "id", "code",
            "structure", "etat", "nom_ar", "coordonnee_gps", "responsable",
            "type_structure",

            # ✅ FK ids (pour Select React)
            "wilaya_fk", "moughataa_fk", "commune_fk",

            # ✅ noms lisibles (pour tableau React)
            "wilaya_nom", "moughataa_nom", "commune_nom",
            "type_structure_code", "type_structure_libelle",

            "date_de_construction",

            "etat_batiment", 
            "cloture", "electricite", "internet", "eau", "cdf", "equipement",

            "fosa_reference", "fosa_plus_proche",
            "prestation_service", "service_manquant", "besoins",
            "pourcentage_activite",
            "observation", "bailleur",
            "source_file", "created_at", "last_updated",
        ]



# ------- Données réelles (upsert) -------
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





class FOSASerializer2(serializers.ModelSerializer):

    wilaya_fk = serializers.PrimaryKeyRelatedField(queryset=Wilaya.objects.all(), required=False, allow_null=True)
    moughataa_fk = serializers.PrimaryKeyRelatedField(queryset=Moughataa.objects.all(), required=False, allow_null=True)
    commune_fk = serializers.PrimaryKeyRelatedField(queryset=Commune.objects.all(), required=False, allow_null=True)


    wilaya = serializers.SerializerMethodField()
    moughataa = serializers.SerializerMethodField()
    commune = serializers.SerializerMethodField()

    class Meta:
        model = FOSA
        fields = [
            'code_etablissement', 'nom_fr', 'nom_ar', 'type',
            'longitude', 'latitude', 'coordonnees', 'adresse',
            'responsable',
            
            'wilaya', 'moughataa', 'commune',
            'wilaya_fk', 'moughataa_fk', 'commune_fk',
            'departement', 'is_public',
        ]
        read_only_fields = ['code_etablissement', 'adresse', 'coordonnees', 'is_public']

    def get_wilaya(self, obj):
        
        if obj.wilaya_fk_id:
            return {"id": obj.wilaya_fk_id, "nom": obj.wilaya_fk.nom}
        return {"id": None, "nom": obj.wilaya or None}

    def get_moughataa(self, obj):
        if obj.moughataa_fk_id:
            return {"id": obj.moughataa_fk_id, "nom": obj.moughataa_fk.nom}
        return {"id": None, "nom": obj.moughataa or None}

    def get_commune(self, obj):
        if obj.commune_fk_id:
            return {"id": obj.commune_fk_id, "nom": obj.commune_fk.nom}
        return {"id": None, "nom": obj.commune or None}

    def validate(self, data):
        errors = {}
        if not data.get('nom_fr') and not data.get('nom_ar'):
            errors['nom_fr'] = "Veuillez remplir au moins Nom FR ou Nom Arabe."

        commune_fk   = data.get("commune_fk")
        moughataa_fk = data.get("moughataa_fk")
        wilaya_fk    = data.get("wilaya_fk")

        if commune_fk:
            if moughataa_fk and commune_fk.moughataa_id != moughataa_fk.id:
                errors['commune_fk'] = "La commune n'appartient pas à la moughataa sélectionnée."
            if wilaya_fk and commune_fk.moughataa.wilaya_id != wilaya_fk.id:
                errors['commune_fk'] = "La commune n'appartient pas à la wilaya sélectionnée."
        if moughataa_fk and wilaya_fk and moughataa_fk.wilaya_id != wilaya_fk.id:
            errors['moughataa_fk'] = "La moughataa n'appartient pas à la wilaya sélectionnée."

        lat, lon = data.get('latitude'), data.get('longitude')
        if (lat is None) ^ (lon is None):
            errors['coordonnees'] = "Renseignez latitude ET longitude, ou laissez les deux vides."

        if errors:
            raise serializers.ValidationError(errors)
        return data



class FOSAHistorySerializer(serializers.ModelSerializer):
    fosa_code_etablissement = serializers.ReadOnlyField(source='fosa.code_etablissement')
    fosa_nom_fr = serializers.ReadOnlyField(source='fosa.nom_fr')
    fosa_nom_ar = serializers.ReadOnlyField(source='fosa.nom_ar')
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = FOSAHistory
        fields = [
            'fosa_code_etablissement',  
            'fosa_nom_fr',              
            'fosa_nom_ar',              
            'username',            
            'action',              
            'changes',             
            'timestamp',           
        ]

   


