# fosa/admin.py
from django.contrib import admin
from .models import FOSA, Wilaya, Moughataa, Commune,Maladie,MaladieReport,TypeStructure


class MoughataaInline(admin.TabularInline):
    model = Moughataa
    extra = 1
    show_change_link = True

@admin.register(Wilaya)
class WilayaAdmin(admin.ModelAdmin):
    list_display = ("nom",)                      
    search_fields = ("nom",)                     
    inlines = [MoughataaInline]

class CommuneInline(admin.TabularInline):
    model = Commune
    extra = 1
    show_change_link = True

@admin.register(Moughataa)
class MoughataaAdmin(admin.ModelAdmin):
    list_display = ("nom", "wilaya")             
    list_filter = ("wilaya",)
    search_fields = ("nom", "wilaya__nom")       
    inlines = [CommuneInline]


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ("nom", "moughataa", "get_wilaya") 
    list_filter = ("moughataa__wilaya", "moughataa")
    search_fields = ("nom", "moughataa__nom", "moughataa__wilaya__nom") 

    def get_wilaya(self, obj):
        return obj.moughataa.wilaya
    get_wilaya.short_description = "Wilaya"


@admin.register(FOSA)
class FOSAAdmin(admin.ModelAdmin):
    list_display = (
        "code_etablissement", "nom_fr","wilaya","moughataa", "type",
        "wilaya_fk", "moughataa_fk", "commune_fk",
        "is_public",
    )
    list_filter = ("type", "is_public", "wilaya_fk", "moughataa_fk", "commune_fk")
    list_select_related = ("wilaya_fk", "moughataa_fk", "commune_fk")
    autocomplete_fields = ("wilaya_fk", "moughataa_fk", "commune_fk")
    search_fields = (
        "code_etablissement",
        "structure",
        "nom_fr",
        "nom_ar",
        "responsable",
        # IMPORTANT: utiliser les relations pour la recherche
        "wilaya_fk__nom",
        "moughataa_fk__nom",
        "commune_fk__nom",
    )



@admin.register(Maladie)
class MaladieAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    # shows JSON nicely
    list_filter = ()
    ordering = ("name",)

@admin.register(MaladieReport)
class MaladieReportAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "wilaya", "moughataa", "maladie")
    list_filter = ("date", "wilaya", "maladie")
    search_fields = ("disease__name",)

from django.contrib import admin
from .models import (
    Wilaya, Moughataa, Commune,
    TypeStructure, NormePersonnel, NormeService, NormeMateriel,
    PersonnelStructure, ServiceStructure, MaterielStructure,
)


# =========================
#  NORMES (référentiel)
# =========================

@admin.register(TypeStructure)
class TypeStructureAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "libelle")
    search_fields = ("code", "libelle")
    ordering = ("code",)


@admin.register(NormePersonnel)
class NormePersonnelAdmin(admin.ModelAdmin):
    list_display = ("id", "type_structure", "intitule_poste", "nombre_minimal")
    list_filter = ("type_structure",)
    search_fields = ("intitule_poste", "type_structure__code", "type_structure__libelle")
    ordering = ("type_structure__code", "intitule_poste")


@admin.register(NormeService)
class NormeServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "type_structure", "nom_service", "obligatoire")
    list_filter = ("type_structure", "obligatoire")
    search_fields = ("nom_service", "type_structure__code", "type_structure__libelle")
    ordering = ("type_structure__code", "nom_service")


@admin.register(NormeMateriel)
class NormeMaterielAdmin(admin.ModelAdmin):
    list_display = ("id", "type_structure", "nom_materiel", "quantite_minimale")
    list_filter = ("type_structure",)
    search_fields = ("nom_materiel", "type_structure__code", "type_structure__libelle")
    ordering = ("type_structure__code", "nom_materiel")


# =========================
#  DONNÉES RÉELLES (inlines)
# =========================

class PersonnelStructureInline(admin.TabularInline):
    model = PersonnelStructure
    extra = 0
    fields = ("intitule_poste", "nombre_reel")
    autocomplete_fields = ()
    show_change_link = True


class ServiceStructureInline(admin.TabularInline):
    model = ServiceStructure
    extra = 0
    fields = ("nom_service", "disponible")
    show_change_link = True


class MaterielStructureInline(admin.TabularInline):
    model = MaterielStructure
    extra = 0
    fields = ("nom_materiel", "quantite_reelle")
    show_change_link = True


# =========================
#  STRUCTURE SANTE
# =========================

# @admin.register(StructureSante)
# class StructureSanteAdmin(admin.ModelAdmin):
#     list_display = (
#         "id", "code", "structure",
#         "type_structure",
#         "wilaya_fk", "moughataa_fk", "commune_fk",
#         "etat", "last_updated",
#     )
#     list_filter = ("type_structure", "wilaya_fk", "moughataa_fk", "etat")
#     search_fields = (
#         "code", "structure", "nom_ar",
#         "wilaya", "moughataa", "commune",
#         "wilaya_fk__nom", "moughataa_fk__nom", "commune_fk__nom",
#     )
#     ordering = ("wilaya_fk__nom", "moughataa_fk__nom", "commune_fk__nom", "structure")
#     readonly_fields = ("created_at", "last_updated")

#     # Très pratique si tu as beaucoup de champs
#     fieldsets = (
#         ("Identification", {
#             "fields": ("code", "structure", "nom_ar", "type_structure",  "etat", "responsable")
#         }),
#         ("Localisation", {
#             "fields": ("wilaya_fk", "moughataa_fk", "commune_fk", "wilaya", "moughataa", "commune", "coordonnee_gps")
#         }),
#         ("État / Infrastructures", {
#             "fields": ("etat_batiment",  "cloture", "electricite", "eau", "internet", "cdf", "equipement")
#         }),
#         ("Services / Divers", {
#             "fields": (
#                 "fosa_reference", "fosa_plus_proche",
#                 "prestation_service", "service_manquant",
#                 "besoins",  "pourcentage_activite",
#                 "observation", "bailleur", 
#                 "source_file",
#             )
#         }),
#         ("Dates", {
#             "fields": ("date_de_creation", "date_de_construction", "created_at", "last_updated")
#         }),
#     )

#     inlines = [PersonnelStructureInline, ServiceStructureInline, MaterielStructureInline]


# =========================
#  (Optionnel) si tu veux aussi gérer les tables réelles séparément
# =========================

@admin.register(PersonnelStructure)
class PersonnelStructureAdmin(admin.ModelAdmin):
    list_display = ("id", "structure", "intitule_poste", "nombre_reel")
    list_filter = ("structure__type_structure", "structure__wilaya_fk")
    search_fields = ("intitule_poste", "structure__structure", "structure__code")
    ordering = ("structure__code", "intitule_poste")


@admin.register(ServiceStructure)
class ServiceStructureAdmin(admin.ModelAdmin):
    list_display = ("id", "structure", "nom_service", "disponible")
    list_filter = ("disponible", "structure__type_structure", "structure__wilaya_fk")
    search_fields = ("nom_service", "structure__structure", "structure__code")
    ordering = ("structure__code", "nom_service")


@admin.register(MaterielStructure)
class MaterielStructureAdmin(admin.ModelAdmin):
    list_display = ("id", "structure", "nom_materiel", "quantite_reelle")
    list_filter = ("structure__type_structure", "structure__wilaya_fk")
    search_fields = ("nom_materiel", "structure__structure", "structure__code")
    ordering = ("structure__code", "nom_materiel")
