from django.db.models import Q

def filter_queryset_by_role(qs, user, prefix=""):
    """
    Restreint un queryset en fonction du rôle utilisateur et de son rattachement géographique.
    :param qs: queryset de base
    :param user: utilisateur courant
    :param prefix: préfixe pour accéder aux champs liés (ex: 'fosa__' pour FOSAHistory)
    """
    if not user.is_authenticated:
        return qs.filter(**{f"{prefix}is_public": True})

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
            Q(**{f"{prefix}wilaya_fk_id__in": wilaya_ids}) |
            Q(**{f"{prefix}wilaya__in": wilaya_noms})
        ).distinct()

    # --- Gestionnaire local ---
    if role == "gestionnaire local":
        wilaya_noms = list(user.wilayas.values_list("nom", flat=True))

        q = qs.filter(
            Q(**{f"{prefix}moughataa_fk_id": user.moughataa_fk_id}) |
            Q(**{
                f"{prefix}moughataa": getattr(user.moughataa_fk, "nom", None),
                f"{prefix}wilaya__in": wilaya_noms
            })
        )

        if user.commune_fk_id:
            q = q.filter(**{f"{prefix}commune_fk_id": user.commune_fk_id})

        return q.distinct()

    # --- Utilisateur public ---
    return qs.filter(**{f"{prefix}is_public": True})
