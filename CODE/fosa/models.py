from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# ============================================================
#  RÉFÉRENTIEL GÉOGRAPHIQUE (FK propres pour listes React)
# ============================================================

class Wilaya(models.Model):
    nom = models.CharField(_("Nom"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=2, unique=True, blank=True, null=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Moughataa(models.Model):
    wilaya = models.ForeignKey(Wilaya, on_delete=models.CASCADE, related_name="moughataas")
    nom = models.CharField(_("Nom"), max_length=100)
    code = models.CharField(_("Code"), max_length=2, blank=True, null=True)

    class Meta:
        ordering = ["wilaya__nom", "nom"]
        constraints = [
            models.UniqueConstraint(fields=["wilaya", "nom"], name="uniq_moughataa_nom_in_wilaya"),
        ]
        indexes = [
            models.Index(fields=["wilaya", "nom"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.wilaya.nom})"


class Commune(models.Model):
    moughataa = models.ForeignKey(Moughataa, on_delete=models.CASCADE, related_name="communes")
    nom = models.CharField(_("Nom"), max_length=100)
    code = models.CharField(_("Code"), max_length=2, blank=True, null=True)

    class Meta:
        ordering = ["moughataa__wilaya__nom", "moughataa__nom", "nom"]
        constraints = [
            models.UniqueConstraint(fields=["moughataa", "nom"], name="uniq_commune_nom_in_moughataa"),
        ]
        indexes = [
            models.Index(fields=["moughataa", "nom"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.moughataa.nom} / {self.moughataa.wilaya.nom})"


# ============================================================
#  (OPTIONNEL) TON MODÈLE FOSA EXISTANT - CONSERVÉ
#  (utile si tu as déjà des données et codification)
# ============================================================

class FOSA(models.Model):
    TYPE_CHOICES = [
        ("PS", "Poste de Santé"),
        ("CS", "Centre de Santé"),
        ("CH", "Centre hospitalier"),
        ("DRS", "Direction Régionale de Santé"),
        ("DAF", "Direction Administrative et Financière"),
        ("FOND", "FOND"),
        ("AUTRE", "Autre"),
    ]
    PUBLIC_TYPES = {"PS", "CS", "CH"}

    nom_fr = models.CharField(max_length=100, verbose_name="Nom (Français)", blank=True, null=True)
    nom_ar = models.CharField(max_length=100, verbose_name="Nom (Arabe)", blank=True, null=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True, null=True)

    code_etablissement = models.CharField(primary_key=True, max_length=100)

    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    adresse = models.CharField(max_length=200, blank=True, null=True)
    responsable = models.CharField(max_length=100, blank=True, null=True)
    departement = models.CharField(max_length=100, blank=True, null=True)

    # champs texte (legacy/export)
    commune = models.CharField(max_length=100, default="Inconnu")
    moughataa = models.CharField(max_length=100, default="Inconnu")
    wilaya = models.CharField(max_length=100, default="Inconnu")

    # FK (propre pour listes)
    wilaya_fk = models.ForeignKey(Wilaya, on_delete=models.PROTECT, null=True, blank=True, related_name="fosas")
    moughataa_fk = models.ForeignKey(Moughataa, on_delete=models.PROTECT, null=True, blank=True, related_name="fosas")
    commune_fk = models.ForeignKey(Commune, on_delete=models.PROTECT, null=True, blank=True, related_name="fosas")

    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom_fr"]
        indexes = [models.Index(fields=["code_etablissement"])]

    def __str__(self):
        return f"{self.nom_fr or self.nom_ar or 'Sans nom'} ({self.code_etablissement})"

    @property
    def coordonnees(self):
        if self.latitude is not None and self.longitude is not None:
            return f"{self.latitude}, {self.longitude}"
        return None

    def save(self, *args, **kwargs):
        self.is_public = (self.type in self.PUBLIC_TYPES)

        # auto-remplissage des champs texte depuis FK
        if self.commune_fk:
            self.commune = self.commune_fk.nom
            self.moughataa = self.commune_fk.moughataa.nom
            self.wilaya = self.commune_fk.moughataa.wilaya.nom
            self.moughataa_fk = self.commune_fk.moughataa
            self.wilaya_fk = self.commune_fk.moughataa.wilaya
        elif self.moughataa_fk:
            self.moughataa = self.moughataa_fk.nom
            self.wilaya = self.moughataa_fk.wilaya.nom
            self.wilaya_fk = self.moughataa_fk.wilaya
        elif self.wilaya_fk:
            self.wilaya = self.wilaya_fk.nom

        if self.commune and self.moughataa and self.wilaya:
            self.adresse = f"{self.commune.strip()} , {self.moughataa.strip()} , {self.wilaya.strip()}"

        # ⚠️ codification : garde ton code existant si tu l’utilises
        if not self.code_etablissement:
            from .codification import type_codes, wilaya_codes, moughataa_codes, commune_codes
            t_code = type_codes.get(self.type, "00")
            w_code = wilaya_codes.get(self.wilaya, "00")
            m_code = moughataa_codes.get(self.moughataa, "00")
            c_code = commune_codes.get(self.commune, "00")

            prefix = f"{t_code}0{w_code}{m_code}{c_code}"
            count = FOSA.objects.filter(code_etablissement__startswith=prefix).count()
            self.code_etablissement = f"{prefix}{count + 1:02d}"

        super().save(*args, **kwargs)


class FOSAHistory(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Création"),
        ("UPDATE", "Mise à jour"),
        ("DELETE", "Suppression"),
    ]
    fosa = models.ForeignKey(FOSA, on_delete=models.CASCADE, related_name="historiques")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.fosa.nom_fr or self.fosa.nom_ar or self.fosa.code_etablissement}"


# ============================================================
#  MALADIES + RAPPORTS (comme tu utilises déjà en React)
# ============================================================

FIELD_KEYS = [
    "cas_suspects",
    "deces",
    "cas_preleves",
    "cas_testes",
    "cas_confirmes",
]


class Maladie(models.Model):
    name = models.CharField(max_length=120, unique=True)
    enabled_fields = models.JSONField(default=list)  # ex: ["deces","cas_confirmes"]

    def __str__(self):
        return self.name
    
from datetime import timedelta

def week_start(d):
    return d - timedelta(days=d.weekday())

class Maladie(models.Model):
    name = models.CharField(max_length=120, unique=True)
    enabled_fields = models.JSONField(default=list)  # ex: ["deces", "cas_confirmes"]

    def __str__(self):
        return self.name


class MaladieReport(models.Model):
    date = models.DateField()
    week_start = models.DateField(null=True, blank=True, db_index=True)

    # ✅ archive (semaine passée)
    is_archived = models.BooleanField(default=False, db_index=True)

    # ✅ zone + maladie
    wilaya = models.ForeignKey("Wilaya", on_delete=models.PROTECT)
    moughataa = models.ForeignKey("Moughataa", on_delete=models.PROTECT)
    maladie = models.ForeignKey(Maladie, on_delete=models.PROTECT)

    # ✅ indicateurs
    cas_suspects = models.PositiveIntegerField(null=True, blank=True)
    deces = models.PositiveIntegerField(null=True, blank=True)
    cas_preleves = models.PositiveIntegerField(null=True, blank=True)
    cas_testes = models.PositiveIntegerField(null=True, blank=True)
    cas_confirmes = models.PositiveIntegerField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "wilaya", "moughataa", "maladie"],
                name="uniq_report_per_day_area_maladie",
            )
        ]
        indexes = [
            models.Index(fields=["week_start"]),
            models.Index(fields=["is_archived"]),
            models.Index(fields=["week_start", "is_archived"]),
        ]

    def save(self, *args, **kwargs):
        # ✅ calcule week_start automatiquement
        if self.date:
            self.week_start = week_start(self.date)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.wilaya.nom} / {self.moughataa.nom} - {self.maladie.name}"
# ============================================================
#  NORMES (référentiel) + STRUCTURE SANTE (avec FK géo propres)
# ============================================================

class TypeStructure(models.Model):
    code = models.CharField(max_length=10, unique=True)
    libelle = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Type de structure"
        verbose_name_plural = "Types de structure"

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class NormePersonnel(models.Model):
    type_structure = models.ForeignKey(TypeStructure, on_delete=models.CASCADE, related_name="normes_personnel")
    intitule_poste = models.CharField(max_length=150)
    nombre_minimal = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Norme de personnel"
        verbose_name_plural = "Normes de personnel"
        unique_together = ("type_structure", "intitule_poste")

    def __str__(self):
        return f"{self.type_structure.code} - {self.intitule_poste} (min {self.nombre_minimal})"


class NormeService(models.Model):
    type_structure = models.ForeignKey(TypeStructure, on_delete=models.CASCADE, related_name="normes_services")
    nom_service = models.CharField(max_length=200)
    obligatoire = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Norme de service"
        verbose_name_plural = "Normes de service"
        unique_together = ("type_structure", "nom_service")

    def __str__(self):
        return f"{self.type_structure.code} - {self.nom_service}"


class NormeMateriel(models.Model):
    type_structure = models.ForeignKey(TypeStructure, on_delete=models.CASCADE, related_name="normes_materiel")
    nom_materiel = models.CharField(max_length=200)
    quantite_minimale = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Norme de matériel"
        verbose_name_plural = "Normes de matériel"
        unique_together = ("type_structure", "nom_materiel")

    def __str__(self):
        return f"{self.type_structure.code} - {self.nom_materiel} (min {self.quantite_minimale})"


class StructureSante(models.Model):
    code = models.CharField(
    max_length=20,
    unique=True,
    blank=True,
    null=True,
    db_index=True,)

    structure = models.CharField("Nom de la structure", max_length=255, blank=True, null=True)
    type_structure = models.ForeignKey(
        TypeStructure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="structures",
        verbose_name="Type normatif"
    )
    etat = models.CharField("État de fonctionnalité", max_length=64, blank=True, null=True)
    nom_ar = models.CharField("Nom en arabe", max_length=128, blank=True, null=True)
    coordonnee_gps = models.CharField("Coordonnées", max_length=128, blank=True, null=True)
    responsable = models.CharField("Responsable", max_length=128, blank=True, null=True)

    etat_batiment = models.CharField(max_length=100, blank=True, null=True)

    # ---- géographie (FK pour listes)
    wilaya_fk = models.ForeignKey(Wilaya, on_delete=models.PROTECT, null=True, blank=True, related_name="structures_sante")
    moughataa_fk = models.ForeignKey(Moughataa, on_delete=models.PROTECT, null=True, blank=True, related_name="structures_sante")
    commune_fk = models.ForeignKey(Commune, on_delete=models.PROTECT, null=True, blank=True, related_name="structures_sante")

    date_de_construction = models.CharField(max_length=100, blank=True, null=True)

    # ---- infrastructures
    cloture = models.BooleanField(null=True, blank=True)
    electricite = models.BooleanField(null=True, blank=True)
    internet = models.BooleanField(null=True, blank=True)
    eau = models.BooleanField(null=True, blank=True)
    cdf = models.BooleanField(null=True, blank=True)  # chaîne de froid
    equipement = models.CharField(max_length=255,null=True, blank=True)

    # ---- infos diverses
    fosa_reference = models.CharField(max_length=255, blank=True, null=True)
    fosa_plus_proche = models.CharField(max_length=255, blank=True, null=True)

    prestation_service = models.JSONField(null=True, blank=True, default=list)
    service_manquant = models.JSONField(null=True, blank=True, default=list)
   
    besoins = models.CharField(max_length=255, blank=True, null=True)
    pourcentage_activite = models.CharField(max_length=50, blank=True, null=True)

    observation = models.TextField(blank=True, null=True)
    bailleur = models.TextField(blank=True, null=True)

    source_file = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Structure de santé"
        verbose_name_plural = "Structures de santé"
        ordering = ["wilaya_fk__nom", "moughataa_fk__nom", "commune_fk__nom", "structure"]
    indexes = [
        models.Index(fields=["wilaya_fk", "moughataa_fk", "commune_fk"]),
        models.Index(fields=["code"]),
    ]

    def __str__(self):
         return f"{self.structure or 'Sans nom'} — {self.wilaya_fk.nom if self.wilaya_fk else ''} ({self.code or ''})"

    def save(self, *args, **kwargs):
        # Remplir les champs texte depuis FK (important pour affichage / exports)
        if self.commune_fk:
            self.commune = self.commune_fk.nom
            self.moughataa = self.commune_fk.moughataa.nom
            self.wilaya = self.commune_fk.moughataa.wilaya.nom
            self.moughataa_fk = self.commune_fk.moughataa
            self.wilaya_fk = self.commune_fk.moughataa.wilaya
        elif self.moughataa_fk:
            self.moughataa = self.moughataa_fk.nom
            self.wilaya = self.moughataa_fk.wilaya.nom
            self.wilaya_fk = self.moughataa_fk.wilaya
        elif self.wilaya_fk:
            self.wilaya = self.wilaya_fk.nom

        creating = self.pk is None
        super().save(*args, **kwargs)

        if creating and not self.code:
         self.code = f"FOSA-{self.pk:04d}"  # FOSA-0001
         super().save(update_fields=["code"])

    # ===== méthodes conformité (comme ton modèle normes)
    def manques_personnel(self):
        if not self.type_structure:
            return []
        manques = []
        normes = self.type_structure.normes_personnel.all()
        reels = {p.intitule_poste: p.nombre_reel for p in self.personnels.all()}
        for norme in normes:
            reel = reels.get(norme.intitule_poste, 0)
            if reel < norme.nombre_minimal:
                manques.append({"poste": norme.intitule_poste, "reel": reel, "minimal": norme.nombre_minimal})
        return manques

    def manques_services(self):
        if not self.type_structure:
            return []
        manques = []
        normes = self.type_structure.normes_services.filter(obligatoire=True)
        reels = {s.nom_service: s.disponible for s in self.services.all()}
        for norme in normes:
            dispo = reels.get(norme.nom_service, False)
            if not dispo:
                manques.append(norme.nom_service)
        return manques

    def manques_materiel(self):
        if not self.type_structure:
            return []
        manques = []
        normes = self.type_structure.normes_materiel.all()
        reels = {m.nom_materiel: m.quantite_reelle for m in self.materiels.all()}
        for norme in normes:
            reel = reels.get(norme.nom_materiel, 0)
            if reel < norme.quantite_minimale:
                manques.append({"materiel": norme.nom_materiel, "reel": reel, "minimal": norme.quantite_minimale})
        return manques

    def est_conforme(self):
        return (not self.manques_personnel() and not self.manques_services() and not self.manques_materiel())


class PersonnelStructure(models.Model):
    structure = models.ForeignKey(StructureSante, on_delete=models.CASCADE, related_name="personnels")
    intitule_poste = models.CharField(max_length=150)
    nombre_reel = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Personnel réel de la structure"
        verbose_name_plural = "Personnel réel des structures"
        unique_together = ("structure", "intitule_poste")

    def __str__(self):
        return f"{self.structure} - {self.intitule_poste} ({self.nombre_reel})"


class ServiceStructure(models.Model):
    structure = models.ForeignKey(StructureSante, on_delete=models.CASCADE, related_name="services")
    nom_service = models.CharField(max_length=200)
    disponible = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Service offert par la structure"
        verbose_name_plural = "Services offerts par les structures"
        unique_together = ("structure", "nom_service")

    def __str__(self):
        return f"{self.structure} - {self.nom_service} ({'oui' if self.disponible else 'non'})"


class MaterielStructure(models.Model):
    structure = models.ForeignKey(StructureSante, on_delete=models.CASCADE, related_name="materiels")
    nom_materiel = models.CharField(max_length=200)
    quantite_reelle = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Matériel de la structure"
        verbose_name_plural = "Matériel des structures"
        unique_together = ("structure", "nom_materiel")

    def __str__(self):
        return f"{self.structure} - {self.nom_materiel} ({self.quantite_reelle})"

class NormeStructureInfo(models.Model):
    type_structure = models.OneToOneField(TypeStructure, on_delete=models.CASCADE, related_name="norme_info")
    population_min = models.PositiveIntegerField(null=True, blank=True)
    population_max = models.PositiveIntegerField(null=True, blank=True)
    superficie_min_m2 = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.population_min} - {self.population_max} ({self.superficie_min_m2})"
