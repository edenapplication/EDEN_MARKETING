from django.core.management.base import BaseCommand
from eden.models import AcademieEtapeParcours, AcademieStatistique


class Command(BaseCommand):
    help = 'Initialise le contenu de base de l\'Académie'

    def handle(self, *args, **options):
        # Étapes parcours
        etapes = [
            (1,'📖','Découvrir le foncier','Comprendre les bases du foncier camerounais'),
            (2,'📋','Comprendre les documents','Maîtriser les titres et actes fonciers'),
            (3,'🏡','Choisir son terrain','Sélectionner le bon site selon ses critères'),
            (4,'📝','Suivre les procédures','Respecter toutes les étapes légales'),
            (5,'🔒','Recevoir son achat','Finaliser l\'acquisition en toute sécurité'),
            (6,'📐','Implantation','Matérialiser la parcelle sur le terrain'),
            (7,'🏆','Valoriser son patrimoine','Gérer et valoriser son bien foncier'),
        ]
        for num, ico, tit, desc in etapes:
            AcademieEtapeParcours.objects.get_or_create(
                numero=num,
                defaults={'icone': ico, 'titre': tit, 'description': desc, 'ordre': num}
            )

        # Statistiques
        stats = [
            ('150+', 'Textes de loi disponibles', '📜'),
            ('350+', 'Articles et analyses à votre disposition', '📄'),
            ('200+', 'Vidéos pédagogiques et explicatives', '🎬'),
            ('1000+', 'Ressources à télécharger gratuitement', '📦'),
            ('20+', 'Experts à votre écoute', '👥'),
        ]
        for val, label, ico in stats:
            AcademieStatistique.objects.get_or_create(
                label=label,
                defaults={'valeur': val, 'icone': ico}
            )

        self.stdout.write(self.style.SUCCESS('✅ Académie initialisée !'))