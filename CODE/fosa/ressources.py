# fosa/ressources.py
from import_export import resources
from .models import FOSA, Wilaya, Moughataa, Commune

class FOSAResources(resources.ModelResource):
    class Meta:
        model = FOSA
        import_id_fields = []
        fields = (
            'code_etablissement',
            'nom_fr',
            'nom_ar',
            'type',
            'departement',
            'responsable',
            'adresse',
            'commune',
            'moughataa',
            'wilaya',
            'coordonnees',
            'latitude',
            'longitude',
            'is_public'
        )
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

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

    # ---------- helpers ----------
    def _emptyish(self, v):
        if v is None: return True
        if isinstance(v, str) and v.strip().lower() in {"", "nan", "none", "null", "nil", "-", "--"}:
            return True
        # Tablib peut donner des floats NaN
        try:
            # détecte NaN numériques
            import math
            if isinstance(v, float) and math.isnan(v): return True
        except Exception:
            pass
        return False

    def _row_is_empty(self, row: dict) -> bool:
        # si TOUTES les valeurs du row sont "vides"
        return all(self._emptyish(val) for val in row.values())


    def clean_type(self, raw_value):
        print("not autre value exist")
        if not raw_value:
            print("not autre value exist")
            return "AUTRE"
        value = str(raw_value).strip().replace("é", "e")
        print("not autre value exist" ,value)
        print("not autre value exist" ,self.TYPE_MAPPING.keys())

        print("not autre value exist" ,self.TYPE_MAPPING.get(value, "AUTREE"))
        
        
        
    def clean_coordinates(self, row):
        def to_float_or_none(x):
            if self._emptyish(x): return None
            try: return float(str(x).strip())
            except Exception: return None
        row['latitude']  = to_float_or_none(row.get('latitude'))
        row['longitude'] = to_float_or_none(row.get('longitude'))

    # ---------- hooks import-export ----------
    def before_import_row(self, row, **kwargs):
        """
        Si ligne vide -> on marque pour skip, sinon on normalise.
        Ne JAMAIS lever pour une ligne vide (ça spamme d'erreurs).
        """
        if self._row_is_empty(row):
            row['__empty__'] = '1'
            return

        row['type'] = self.clean_type(row.get('type'))
        self.clean_coordinates(row)

        # Vérifs minimales UNIQUEMENT si non vide
        if self._emptyish(row.get('nom_fr')) and self._emptyish(row.get('nom_ar')):
            raise ValueError("Il faut au moins nom_fr ou nom_ar")
        for champ in ['commune', 'moughataa', 'wilaya']:
            if self._emptyish(row.get(champ)):
                raise ValueError(f"Le champ {champ} est obligatoire")

    def skip_row(self, instance, original):
        # 1) marqueur posé
        if isinstance(original, dict) and original.get('__empty__') == '1':
            return True
        # 2) garde-fou si pas de marqueur
        def empty(v): return v is None or (isinstance(v, str) and v.strip() == "")
        if all(empty(getattr(instance, f, None)) for f in ['nom_fr', 'nom_ar', 'wilaya', 'moughataa', 'commune']):
            return True
        return False

    def before_save_instance(self, instance, using_transactions, dry_run):
        # Résoudre les FK (crée si absent; si tu veux strict, remplace par des erreurs)
        w = Wilaya.objects.filter(nom__iexact=instance.wilaya).first() or Wilaya.objects.create(nom=instance.wilaya)
        m = Moughataa.objects.filter(wilaya=w, nom__iexact=instance.moughataa).first() or Moughataa.objects.create(wilaya=w, nom=instance.moughataa)
        c = Commune.objects.filter(moughataa=m, nom__iexact=instance.commune).first() or Commune.objects.create(moughataa=m, nom=instance.commune)

        instance.wilaya_fk = w
        instance.moughataa_fk = m
        instance.commune_fk = c
