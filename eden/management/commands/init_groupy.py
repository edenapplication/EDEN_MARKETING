from django.core.management.base import BaseCommand
from eden.models import GroupyCategorie, GroupyQR


class Command(BaseCommand):
    help = 'Initialise la base de connaissances GROUPY avec des Q&R de départ'

    def handle(self, *args, **kwargs):
        # Créer les catégories
        cats = {
            'entreprise': GroupyCategorie.objects.get_or_create(nom='Entreprise', emoji='🏢')[0],
            'sites': GroupyCategorie.objects.get_or_create(nom='Sites & Terrains', emoji='🏡')[0],
            'prix': GroupyCategorie.objects.get_or_create(nom='Prix & Budget', emoji='💰')[0],
            'reservation': GroupyCategorie.objects.get_or_create(nom='Réservation', emoji='📋')[0],
            'contact': GroupyCategorie.objects.get_or_create(nom='Contact', emoji='📞')[0],
            'juridique': GroupyCategorie.objects.get_or_create(nom='Juridique', emoji='📜')[0],
            'promo': GroupyCategorie.objects.get_or_create(nom='Promotions', emoji='🔥')[0],
            'paiement': GroupyCategorie.objects.get_or_create(nom='Paiement', emoji='💳')[0],
        }

        qrs = [
            # ── ENTREPRISE ──
            {
                'categorie': cats['entreprise'],
                'question': "Qui est EDEN GROUP | c'est quoi EDEN GROUP | présentation EDEN GROUP | que fait EDEN GROUP | EDEN GROUP c'est quoi",
                'mots_cles': 'eden group, présentation, qui, c\'est quoi, que fait, histoire, fondé',
                'reponse': """🏢 **EDEN GROUP** est une plateforme foncière premium fondée en **2018** à Yaoundé, Cameroun.

Notre mission : rendre l'accès à la propriété terrienne **transparent, simple et sécurisé** pour chaque africain.

📊 En chiffres :
- 6+ années d'expérience
- 500+ clients satisfaits
- 98% de satisfaction client
- 30+ experts (juristes, cartographes, agents)
- {NB_SITES} sites fonciers actifs
- {NB_DISPONIBLES} parcelles disponibles

📞 {TEL} | ✉ {EMAIL}""",
                'priorite': 8,
            },
            # ── LOCALISATION ──
            {
                'categorie': cats['contact'],
                'question': "Où se trouve EDEN GROUP | quelle est votre adresse | comment venir | où êtes-vous | bureau EDEN | siège EDEN | localisation EDEN",
                'mots_cles': 'adresse, localisation, situé, trouver, bureau, siège, venir, kennedy, yaoundé, où',
                'reponse': """📍 **EDEN GROUP est situé à :**

🏢 Immeuble EDEN, Avenue Kennedy
Yaoundé, Cameroun

📞 {TEL}
💬 WhatsApp : {TEL}
✉ {EMAIL}

🕐 **Horaires :** {HORAIRES}

N'hésitez pas à nous appeler avant de venir !""",
                'priorite': 9,
            },
            # ── HORAIRES ──
            {
                'categorie': cats['contact'],
                'question': "Quels sont vos horaires | à quelle heure êtes-vous ouverts | vous êtes ouverts quand | horaires d'ouverture | quand appelez-vous",
                'mots_cles': 'horaire, heure, ouvert, fermé, quand, disponible, semaine, samedi',
                'reponse': """🕐 **Horaires d'ouverture EDEN GROUP :**

📅 Lundi - Vendredi : **8h00 - 18h00**
📅 Samedi : **9h00 - 13h00**
📅 Dimanche : Fermé

📞 Téléphone : {TEL}
💬 WhatsApp disponible pendant les horaires

🤖 Moi, **GROUPY**, je suis disponible **24h/24, 7j/7** pour répondre à vos questions !""",
                'priorite': 7,
            },
            # ── CONTACT ──
            {
                'categorie': cats['contact'],
                'question': "Comment vous contacter | numéro de téléphone | email EDEN GROUP | whatsapp EDEN",
                'mots_cles': 'contact, téléphone, appeler, whatsapp, email, joindre, numéro',
                'reponse': """📞 **Contactez EDEN GROUP :**

📱 Téléphone : **{TEL}**
💬 WhatsApp : **{TEL}**
✉ Email : **{EMAIL}**
📍 Adresse : Immeuble EDEN, Avenue Kennedy, Yaoundé

🕐 {HORAIRES}

Notre équipe répond rapidement à toutes vos demandes !""",
                'priorite': 8,
            },
            # ── SITES DISPONIBLES ──
            {
                'categorie': cats['sites'],
                'question': "Quels sont vos sites disponibles | liste des terrains | parcelles disponibles | sites fonciers EDEN | catalogue terrains",
                'mots_cles': 'site, terrain, parcelle, disponible, catalogue, liste, lotissement, foncier',
                'reponse': """🏡 **Nos sites fonciers EDEN GROUP :**

{LISTE_SITES}

📊 En ce moment : **{NB_DISPONIBLES} parcelles disponibles** sur {NB_SITES} sites actifs !

👉 Visitez notre catalogue complet sur le site
📞 Appelez-nous pour plus d'infos : {TEL}""",
                'priorite': 9,
            },
            # ── PRIX ──
            {
                'categorie': cats['prix'],
                'question': "Quels sont vos prix | combien coûte une parcelle | tarifs EDEN GROUP | quel est le prix | budget nécessaire | prix des terrains",
                'mots_cles': 'prix, tarif, coût, combien, budget, fcfa, million, argent, cher, coûte',
                'reponse': """💰 **Prix de nos parcelles EDEN GROUP :**

{LISTE_SITES}

📐 Nos parcelles vont de **400 m²** à **1 000 m²** selon les sites.

💡 Le prix dépend de :
- La localisation du site
- La superficie de la parcelle
- Les aménagements disponibles

📞 Appelez-nous pour une étude personnalisée selon votre budget : **{TEL}**""",
                'priorite': 9,
            },
            # ── COMMENT RÉSERVER ──
            {
                'categorie': cats['reservation'],
                'question': "Comment réserver | comment acheter un terrain | étapes pour acheter | procédure achat | comment procéder | je veux acheter",
                'mots_cles': 'réserver, acheter, comment, étapes, procédure, procéder, achat, acquérir',
                'reponse': """📋 **Comment réserver une parcelle EDEN GROUP ?**

**Étape 1️⃣** — Choisissez votre parcelle sur notre site ou carte interactive

**Étape 2️⃣** — Cliquez sur "Réserver" ou contactez-nous :
📞 {TEL} | 💬 WhatsApp

**Étape 3️⃣** — Notre équipe vous contacte sous **24 heures**

**Étape 4️⃣** — Visite du terrain si souhaité

**Étape 5️⃣** — Signature du contrat + titre foncier certifié ✅

⚡ Délai moyen de confirmation : **48 heures**
🔒 100% sécurisé — titre foncier garanti""",
                'priorite': 10,
            },
            # ── TITRE FONCIER ──
            {
                'categorie': cats['juridique'],
                'question': "Titre foncier inclus | document légal | est-ce sécurisé | papiers officiels | certifié | authentique | légal",
                'mots_cles': 'titre, foncier, document, légal, sécurisé, certifié, authentique, papier, juridique',
                'reponse': """📜 **Sécurité juridique EDEN GROUP :**

✅ **Tous nos titres fonciers sont certifiés et authentiques**

🔒 Notre processus de sécurisation :
- Vérification juridique complète avant chaque vente
- Titres enregistrés au **Cadastre du Cameroun**
- Accompagnement notarial inclus
- Suivi administratif complet jusqu'à la remise du titre
- **Garantie EDEN GROUP**

⚖ Notre équipe de juristes spécialisés supervise chaque transaction.

📞 Questions juridiques : {TEL}""",
                'priorite': 7,
            },
            # ── PROMOTIONS ──
            {
                'categorie': cats['promo'],
                'question': "Avez-vous des promotions | réductions disponibles | offres spéciales | remises | soldes terrains | prix réduit",
                'mots_cles': 'promotion, réduction, offre, remise, solde, spécial, avantage, discount, promo',
                'reponse': """🔥 **Promotions EDEN GROUP :**

{LISTE_PROMOS}

📢 Nous proposons régulièrement des offres exclusives avec des réductions allant jusqu'à **-20%** !

✅ Offres à durée limitée
✅ Parcelles sélectionnées
✅ Prix négociables selon budget
✅ Facilités de paiement disponibles

⚡ Ces offres sont limitées — ne tardez pas !
📞 Renseignez-vous : {TEL}""",
                'priorite': 8,
            },
            # ── PAIEMENT ──
            {
                'categorie': cats['paiement'],
                'question': "Comment payer | modes de paiement | paiement en plusieurs fois | acompte | facilités de paiement | crédit possible",
                'mots_cles': 'paiement, payer, acompte, versement, facilité, mensualité, crédit, tranches, financement',
                'reponse': """💳 **Options de paiement EDEN GROUP :**

✅ **Paiement comptant** — avec remise possible
✅ **Acompte + solde** — versement initial puis le reste à la signature
✅ **Paiement en tranches** — selon accord avec notre équipe
💰 **Prix négociables** selon le dossier

📋 **Fonctionnement :**
1. Un acompte confirme votre réservation
2. Le solde est versé avant remise du titre foncier
3. Nous établissons un échéancier personnalisé

📞 Étude de financement gratuite : **{TEL}**""",
                'priorite': 7,
            },
            # ── VISITE ──
            {
                'categorie': cats['reservation'],
                'question': "Puis-je visiter un terrain | organiser une visite | voir le terrain avant d'acheter | visite sur place | venir voir",
                'mots_cles': 'visite, visiter, voir, terrain, avant, place, déplacer, venir',
                'reponse': """📅 **Organiser une visite chez EDEN GROUP :**

Bien sûr ! Nous vous encourageons à **visiter votre terrain avant d'acheter**.

🗓 **Comment programmer une visite :**
1. Appelez-nous au **{TEL}**
2. Ou envoyez-nous un message WhatsApp
3. Nous programmons la visite selon vos disponibilités
4. Un de nos agents vous accompagnera sur place

🕐 Visites disponibles pendant nos horaires :
{HORAIRES}

📞 Réservez votre visite : **{TEL}**""",
                'priorite': 6,
            },
            # ── SUPERFICIE ──
            {
                'categorie': cats['sites'],
                'question': "Quelle superficie | taille des parcelles | dimensions terrains | combien de mètres carrés | grand ou petit terrain",
                'mots_cles': 'superficie, taille, dimension, mètre, m2, carré, grand, petit, longueur, largeur',
                'reponse': """📐 **Superficies disponibles chez EDEN GROUP :**

Nos parcelles varient généralement de **400 m²** à **1 000 m²+**

🏡 **Exemples typiques :**
- 400 m² — idéal villa individuelle
- 500 m² — standard résidentiel
- 600-800 m² — grand standing
- 1 000 m²+ — projet commercial ou villa luxe

💡 La superficie impacte directement le prix.
Nous adaptons selon votre **projet et budget** !

📞 {TEL} pour discuter de votre projet""",
                'priorite': 5,
            },
            # ── SALUTATIONS ──
            {
                'categorie': cats['entreprise'],
                'question': "Bonjour | bonsoir | salut | hello | bonne journée | coucou",
                'mots_cles': 'bonjour, bonsoir, salut, hello, coucou, bonne journée, bonne soirée',
                'reponse': """👋 Bonjour ! Je suis **GROUPY**, l'assistant virtuel d'**EDEN GROUP**.

Je peux vous aider avec :
🏡 Nos sites et parcelles disponibles ({NB_DISPONIBLES} dispo !)
💰 Les prix et budgets
📋 Comment réserver un terrain
📍 Notre localisation et horaires
🔥 Nos promotions en cours ({NB_PROMOS} offre(s) active(s))

Que puis-je faire pour vous ? ✨""",
                'priorite': 10,
            },
        ]

        created = 0
        for data in qrs:
            obj, is_new = GroupyQR.objects.get_or_create(
                question=data['question'],
                defaults={
                    'categorie': data.get('categorie'),
                    'reponse': data['reponse'],
                    'mots_cles': data.get('mots_cles', ''),
                    'priorite': data.get('priorite', 0),
                    'is_active': True,
                }
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Q&R créée : {obj.question[:50]}'))

        self.stdout.write(self.style.SUCCESS(f'\n🤖 GROUPY initialisé ! {created} Q&R ajoutées.'))
        self.stdout.write(self.style.WARNING('👉 Allez sur /dashboard/groupy/ pour voir et compléter la base.'))