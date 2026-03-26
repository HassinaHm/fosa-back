from django.contrib import admin
from .models import (
    FOSA, FOSAHistory,
    Wilaya, Moughataa, Commune,
    Maladie, MaladieReport,
    TypeStructure, NormePersonnel, NormeService, NormeMateriel,
    PersonnelStructure, ServiceStructure, MaterielStructure,
)


# ============================================================
#  GÉOGRAPHIQUE
# ============================================================

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


# ============================================================
#  MALADIES
# ============================================================

@admin.register(Maladie)
class MaladieAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(MaladieReport)
class MaladieReportAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "wilaya", "moughataa", "maladie")
    list_filter = ("date", "wilaya", "maladie")
    search_fields = ("maladie__name",)


# ============================================================
#  NORMES 
# ============================================================

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


# ============================================================
#  DONNÉES RÉELLES 
# ============================================================

class PersonnelStructureInline(admin.TabularInline):
    model = PersonnelStructure
    extra = 0
    fields = ("intitule_poste", "nombre_reel")
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


# ============================================================
#  FOSA 
# ============================================================

@admin.register(FOSA)
class FOSAAdmin(admin.ModelAdmin):
    list_display = (
        "code_etablissement",
        "structure",
        "type",
        "type_structure",
        "wilaya_fk",
        "moughataa_fk",
        "commune_fk",
        "etat",
        "is_public",
    )
    list_filter = (
        "type",
        "type_structure",
        "wilaya_fk",
        "moughataa_fk",
        "commune_fk",
        "etat",
        "is_public",
    )
    list_select_related = ("wilaya_fk", "moughataa_fk", "commune_fk", "type_structure")
    autocomplete_fields = ("wilaya_fk", "moughataa_fk", "commune_fk", "type_structure")
    search_fields = (
        "code_etablissement",
        "structure",
        "nom_fr",
        "nom_ar",
        "responsable",
        "wilaya_fk__nom",
        "moughataa_fk__nom",
        "commune_fk__nom",
    )
    readonly_fields = ("created_at", "last_updated")

    fieldsets = (
        ("Identification", {
            "fields": (
                "code_etablissement",
                "structure",
                "nom_fr",
                "nom_ar",
                "type",
                "type_structure",
                "responsable",
                "departement",
            )
        }),
        ("Localisation", {
            "fields": (
                "wilaya_fk",
                "moughataa_fk",
                "commune_fk",
                "coordonnee_gps",
                "latitude",
                "longitude",
                "adresse",
            )
        }),
        ("État / Infrastructures", {
            "fields": (
                "etat",
                "etat_batiment",
                "cloture",
                "electricite",
                "eau",
                "internet",
                "cdf",
                "equipement",
                "date_de_construction",
            )
        }),
        ("Services / Divers", {
            "fields": (
                "fosa_reference",
                "fosa_plus_proche",
                "prestation_service",
                "service_manquant",
                "besoins",
                "pourcentage_activite",
                "observation",
                "bailleur",
                "source_file",
            )
        }),
        ("Dates", {
            "fields": ("created_at", "last_updated")
        }),
        ("Statut", {
            "fields": ("is_public",)
        }),
    )

    inlines = [PersonnelStructureInline, ServiceStructureInline, MaterielStructureInline]


# ============================================================
#  HISTORIQUE
# ============================================================

@admin.register(FOSAHistory)
class FOSAHistoryAdmin(admin.ModelAdmin):
    list_display = ("fosa", "user", "action", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("fosa__code_etablissement", "fosa__structure", "user__username")
    readonly_fields = ("fosa", "user", "action", "changes", "timestamp")
    ordering = ("-timestamp",)