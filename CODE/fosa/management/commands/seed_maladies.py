from django.core.management.base import BaseCommand
from fosa.models import Maladie

class Command(BaseCommand):
    help = "Peuple la table des maladies avec les 36 maladies"
    def handle(self, *args, **options):
        maladies = [
            # Maladies épidémiques (seuil = 1 cas) 
            (
                "Choléra",
                "كوليرا",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "COVID-19",
                "كوفيد-19",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Diphtérie",
                "الدفتيريا(خناق)",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Fièvre de la vallée du Rift (FVR)",
                "حمي الوادي المتصدع",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Fièvre hémorragique de Crimée-Congo (FHCC)",
                "حمى القرم-الكونغو النزفية",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Fièvre hémorragique Marburg",
                "حمى ماربورغ النزفية",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "EBOLA",
                "ايبولا",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Ictère fébrile (Fièvre jaune)",
                "يرقان حمى (الحمى الصفراء)",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "MPox",
                "جدري القرود",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Paralysie flasque aiguë (PFA)",
                "الشلل الرخو الحاد",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "SRAS",
                "متلازمة التنفس الحادة الوخيمة (سارس)",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Tétanos Néo Natal (TNN)",
                "كزاز حديثي الولادة",
                True, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Malnutrition Modérée",
                "سوء التغذية الحاد المتوسط",
                True, 1, True,
                ["cas_suspects", "cas_confirmes", "deces"]
            ),

            # Maladies normales (seuil plus élevé ou sans alerte) 
            (
                "AVP",
                "حوادث السير العمومي",
                False, None, False,
                ["deces", "cas_preleves", "cas_testes", "cas_confirmes"]
            ),
            (
                "Conjonctivite",
                "التهاب الملتحمة",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "Décès Maternel",
                "وفيات الأمهات",
                False, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Décès Néo natal",
                "وفيات حديثي الولادة",
                False, 1, True,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Décès Périnatal",
                "وفيات الفترة المحيطة بالولادة",
                False, 1, True,
                ["cas_suspects", "cas_confirmes", "deces"]
            ),
            (
                "Dengue",
                "حمى الضنك",
                False, 5, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Diarrhée sanglante (dysenterie à Shigella dysenteria)",
                "الزحار الجرثومي (إسهال مع دم)",
                False, None, False,
                ["cas_suspects", "cas_confirmes", "deces"]
            ),
            (
                "Diarrhée Simple",
                "الإسهالات البسيطة",
                False, None, False,
                ["cas_suspects", "cas_confirmes", "deces"]
            ),
            (
                "Fièvre",
                "حمى",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "Syndrome Grippal",
                "الإنفلونزا الموسمية",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "IRAS",
                "التهابات الجهاز التنفسي الحادة (IRAS)",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "Malnutrition Sévère",
                "سوء التغذية الحاد الشديد",
                False, None, False,
                ["cas_suspects", "cas_confirmes", "deces"]
            ),
            (
                "Méningite",
                "التهاب السحايا",
                False, 3, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Morsure d'âne",
                "عضات الحمير",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "Morsure de chien",
                "عضات الكلاب",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "Morsure scorpion",
                "لدغة عقرب",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "Morsures de serpent",
                "عضات الأفاعي",
                False, None, False,
                ["cas_suspects", "cas_confirmes"]
            ),
            (
                "Paludisme grave",
                "الملاريا المؤكدة",
                False, None, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Paludisme simple",
                "الملاريا المؤكدة",
                False, None, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Pneumonie <5ANS",
                "الالتهاب الرئوي (أقل من 5 سنوات)",
                False, None, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Rougeole",
                "الحصبة",
                False, 5, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Schistosomiase",
                "بلهارسيا",
                False, None, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Tuberculose",
                "السل الرئوي",
                False, None, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes", "deces"]
            ),
            (
                "Varicelle",
                "الجدري المائي",
                False, None, False,
                ["cas_suspects", "cas_preleves", "cas_testes", "cas_confirmes"]
            ),
        ]

        created = 0
        updated = 0
        for name_fr, name_ar, is_epidemic, seuil, can_indiv, fields in maladies:
            maladie, was_created = Maladie.objects.get_or_create(
                name=name_fr,
                defaults={
                    "name_ar": name_ar,
                    "is_epidemic": is_epidemic,
                    "seuil_alerte": seuil,
                    "can_report_individually":can_indiv,
                    "enabled_fields": fields,
                }
            )

            if not was_created:
                maladie.name_ar = name_ar
                maladie.is_epidemic = is_epidemic
                maladie.seuil_alerte = seuil
                maladie.can_report_individually = can_indiv
                maladie.enabled_fields = fields
                maladie.save()
                updated += 1
            else:
                created += 1
                
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {created} maladies créées, {updated} mises à jour"
            )
        )