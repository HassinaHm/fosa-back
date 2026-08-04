# ============================================================
# signals.py
# Place this file in your app directory (e.g. fosa/signals.py)
# Then register it in apps.py (see bottom of this file)
# ============================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    FOSA,
    PersonnelStructure,
    ServiceStructure,
    MaterielStructure,
    NormePersonnel,
    NormeService,
    NormeMateriel,
)


@receiver(post_save, sender=FOSA)
def create_defaults_for_fosa(sender, instance, created, **kwargs):
    """
    Auto-create personnel, services, and materiel defaults
    when a new FOSA is created (import or manual creation).
    Uses norms linked to the FOSA's type_structure.
    """
    if not created:
        return

    if not instance.type_structure:
        # No type defined — skip silently
        return

    # ✅ Personnel defaults
    for norme in NormePersonnel.objects.filter(type_structure=instance.type_structure):
        PersonnelStructure.objects.get_or_create(
            structure=instance,
            intitule_poste=norme.intitule_poste,
            defaults={"nombre_reel": 0}
        )

    # ✅ Service defaults
    for norme in NormeService.objects.filter(type_structure=instance.type_structure):
        ServiceStructure.objects.get_or_create(
            structure=instance,
            nom_service=norme.nom_service,
            defaults={"disponible": False}
        )

    # ✅ Materiel defaults
    for norme in NormeMateriel.objects.filter(type_structure=instance.type_structure):
        MaterielStructure.objects.get_or_create(
            structure=instance,
            nom_materiel=norme.nom_materiel,
            defaults={"quantite_reelle": 0}
        )



INIT_DEFAULTS_ACTION = '''
    @action(detail=True, methods=["post"], url_path="init-defaults")
    def init_defaults(self, request, code_etablissement=None):
        """
        Initialize default personnel/services/materiel for an existing FOSA
        based on its type_structure norms.
        Safe to call multiple times — uses get_or_create so no duplicates.
        """
        from .models import NormePersonnel, NormeService, NormeMateriel

        fosa = self.get_object()

        if not fosa.type_structure:
            return Response(
                {"detail": "Type de structure non défini pour cette FOSA."},
                status=400
            )

        created_counts = {"personnel": 0, "services": 0, "materiel": 0}

        # ✅ Personnel
        for norme in NormePersonnel.objects.filter(type_structure=fosa.type_structure):
            _, created = PersonnelStructure.objects.get_or_create(
                structure=fosa,
                intitule_poste=norme.intitule_poste,
                defaults={"nombre_reel": 0}
            )
            if created:
                created_counts["personnel"] += 1

        # ✅ Services
        for norme in NormeService.objects.filter(type_structure=fosa.type_structure):
            _, created = ServiceStructure.objects.get_or_create(
                structure=fosa,
                nom_service=norme.nom_service,
                defaults={"disponible": False}
            )
            if created:
                created_counts["services"] += 1

        # ✅ Materiel
        for norme in NormeMateriel.objects.filter(type_structure=fosa.type_structure):
            _, created = MaterielStructure.objects.get_or_create(
                structure=fosa,
                nom_materiel=norme.nom_materiel,
                defaults={"quantite_reelle": 0}
            )
            if created:
                created_counts["materiel"] += 1

        return Response({
            "detail": "Valeurs par défaut initialisées avec succès.",
            "created": created_counts,
            "fosa": fosa.code_etablissement,
        })
'''