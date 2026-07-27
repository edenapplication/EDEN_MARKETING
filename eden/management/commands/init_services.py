from django.core.management.base import BaseCommand
from eden.models import ServiceCategorie, Service, EtapeProcessus, EngagementService


class Command(BaseCommand):
    help = 'Initialise les services EDEN GROUP'

    def handle(self, *args, **options):
        # Catégories
        cats = [
            ('Tous nos services', '🏠', 'tous'),
            ('Acquisition & Vente', '🏡', 'acquisition-vente'),
            ('Lotissement & Viabilisation', '🗺', 'lotissement-viabilisation'),
            ('Sécurisation Foncière', '🔒', 'securisation-fonciere'),
            ('Dossier Technique', '📋', 'dossier-technique'),
            ('Implantation de Parcelles', '📐', 'implantation-parcelles'),
            ('Construction Clé en Main', '🏗', 'construction-cle-en-main'),
            ('Accompagnement Administratif', '📝', 'accompagnement-administratif'),
            ('Livret de Sécurité', '📔', 'livret-securite'),
            ('EDEN GROUP Académie', '🎓', 'academie'),
            ('Assistance Client', '🎧', 'assistance-client'),
        ]
        for i, (nom, icone, slug) in enumerate(cats):
            cat, _ = ServiceCategorie.objects.get_or_create(slug=slug, defaults={'nom': nom, 'icone': icone, 'ordre': i})

        # Services
        services = [
            (1, 'Acquisition de terrains', '🏠', 'acquisition-vente', 'Nous vous proposons des terrains sécurisés avec titres fonciers authentiques dans des zones à fort potentiel.'),
            (2, 'Lotissement & Viabilisation', '🗺', 'lotissement-viabilisation', 'Études, morcellement, ouverture de voies, assainissement et viabilisation complète de nos lotissements.'),
            (3, 'Sécurisation Foncière', '🔒', 'securisation-fonciere', 'Vérification des titres, authentification des documents et sécurisation juridique de votre investissement.'),
            (4, 'Dossier Technique', '📋', 'dossier-technique', 'Constitution complète du dossier technique de morcellement conforme aux normes en vigueur.'),
            (5, 'Implantation de Parcelles', '📐', 'implantation-parcelles', 'Implantation précise de votre parcelle par nos géomètres experts et remise du procès-verbal d\'implantation.'),
            (6, 'Construction Clé en Main', '🏗', 'construction-cle-en-main', 'De la conception à la livraison, nous construisons pour vous des maisons modernes et durables.'),
            (7, 'Accompagnement Administratif', '📝', 'accompagnement-administratif', 'Assistance dans toutes les démarches administratives et notariales jusqu\'à l\'obtention de votre titre foncier.'),
            (8, 'Livret de Sécurité', '📔', 'livret-securite', 'Livret Physique et Numérique pour la conservation sécurisée de tous vos documents fonciers.'),
            (9, 'EDEN GROUP Académie', '🎓', 'academie', 'Formations professionnelles et certifications pour développer les compétences dans le secteur foncier.'),
            (10, 'Assistance Client', '🎧', 'assistance-client', 'Notre équipe est toujours disponible pour vous accompagner et répondre à toutes vos préoccupations.'),
        ]
        for numero, nom, icone, cat_slug, desc in services:
            cat = ServiceCategorie.objects.filter(slug=cat_slug).first()
            Service.objects.get_or_create(
                numero=numero,
                defaults={'nom': nom, 'icone': icone, 'categorie': cat, 'description': desc, 'ordre': numero}
            )

        # Étapes processus
        etapes = [
            (1, 'Écoute & Conseil', 'Nous écoutons votre besoin et vous conseillons.', '👂'),
            (2, 'Recherche & Étude', 'Nous sélectionnons les meilleurs sites pour votre projet.', '🔍'),
            (3, 'Acquisition & Réservation', 'Vous réservez votre terrain en toute sécurité.', '🤝'),
            (4, 'Implantation', 'Nous matérialisons votre terrain sur le terrain.', '📐'),
            (5, 'Dossier & Suivi', 'Nous constituons et suivons votre dossier jusqu\'au titre.', '📋'),
            (6, 'Accompagnement', 'Nous restons à vos côtés même après l\'acquisition.', '🛡'),
        ]
        for num, tit, desc, ico in etapes:
            EtapeProcessus.objects.get_or_create(
                numero=num,
                defaults={'titre': tit, 'description': desc, 'icone': ico, 'ordre': num}
            )

        # Engagements
        engagements = [
            ('🔒', 'Sécurité garantie', 'Tous nos terrains sont sécurisés avec titres fonciers authentiques.', 'blue'),
            ('👤', 'Accompagnement personnalisé', 'Un conseiller dédié pour un suivi rigoureux de votre projet.', 'red'),
            ('📊', 'Transparence totale', 'Des informations claires et des procédures transparentes.', 'green'),
            ('⭐', 'Qualité & Professionnalisme', 'Une équipe d\'experts à votre service avec professionnalisme.', 'purple'),
        ]
        for ico, tit, desc, col in engagements:
            EngagementService.objects.get_or_create(
                titre=tit,
                defaults={'icone': ico, 'description': desc, 'couleur': col}
            )

        self.stdout.write(self.style.SUCCESS('✅ Services EDEN GROUP initialisés avec succès !'))