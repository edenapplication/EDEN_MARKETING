import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db import models
from .models import HeroConfig


from .models import (
    SiteFoncier, ImageSite, Parcelle, ImageParcelle,
    Temoignage, DemandeContact, Reservation, VisiteProgrammee, HeroConfig, ServiceItem, EtapeAcquisition,
    SectionLivret, ActualiteHome, CommentaireHome, StatistiqueHome,UneEvenement, UneEvenementCategorie, 
Projet, ProjetImage, ProjetInfrastructure, EtapeProjet, SousEtapeProjet, Agence, AgenceService, StatAgence,ServiceCategorie, Service,
    EtapeProcessus, EngagementService, AcademieDocument, AcademieVideo, AcademieEtapeParcours,
    AcademieFAQ, AcademieStatistique, AcademieCategorie,VideoGlobale

)
from .forms import (
    DemandeContactForm, ReservationForm, VisiteForm,
    SiteFoncierForm, ParcelleForm, TemoignageForm
)


def is_agent(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ═══════════════════════════════════════════════
# PAGES PUBLIQUES
# ═══════════════════════════════════════════════
def splash(request):
    """Page de chargement avec animation 3D — redirige vers home après 5s"""
    return render(request, 'eden/splash.html')

def home(request):
    from .models import (
        HeroConfig, HeroSlide, ServiceItem, EtapeAcquisition,
        SectionLivret, ActualiteHome, CommentaireHome,
        StatistiqueHome, JournalEdition, UneEvenement
    )

    sites = SiteFoncier.objects.filter(is_active=True).prefetch_related('images', 'parcelles')
    temoignages = Temoignage.objects.filter(is_active=True).order_by('ordre', '-created_at')[:5]
    promos = Parcelle.objects.filter(
        is_active=True, en_promotion=True, statut='disponible'
    ).select_related('site')[:3]

    total_p = Parcelle.objects.filter(is_active=True).count()
    vendues = Parcelle.objects.filter(statut='vendue').count()
    stats = {
        'sites': SiteFoncier.objects.filter(is_active=True).count(),
        'vendues': vendues,
        'disponibles': Parcelle.objects.filter(statut='disponible').count(),
        'pourcentage': round((vendues / total_p * 100), 1) if total_p else 0,
    }

    hero_config = HeroConfig.objects.filter(pk=1).first()
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('ordre')
    services = ServiceItem.objects.filter(is_active=True).order_by('ordre')[:6]
    etapes = EtapeAcquisition.objects.filter(is_active=True).order_by('numero')
    livret = SectionLivret.objects.filter(is_active=True).first()
    actualites = ActualiteHome.objects.filter(is_active=True).order_by('-date_evenement')
    stats_home = StatistiqueHome.objects.filter(is_active=True).order_by('ordre')
    journaux = JournalEdition.objects.filter(statut='publie').order_by('-numero')
    villes = SiteFoncier.objects.filter(is_active=True).values_list('ville', flat=True).distinct()

    # ═══ Récupérer les actualités du module Une & Événements ═══
    articles_une = UneEvenement.objects.filter(
        categorie='une', statut='publie'
    ).order_by('ordre', '-created_at')[:4]
    
    evenements_avenir = UneEvenement.objects.filter(
        categorie='evenement_avenir', statut='publie'
    ).order_by('date_evenement')[:4]
    
    actualites_recentes = UneEvenement.objects.filter(
        categorie='actualite', statut='publie'
    ).order_by('-date_evenement', '-created_at')[:4]
    
    evenements_passes = UneEvenement.objects.filter(
        categorie='evenement_passe', statut='publie'
    ).order_by('-date_evenement')[:4]
    
    # Combiner toutes les actualités
    actualites_une = list(articles_une) + list(evenements_avenir) + list(actualites_recentes) + list(evenements_passes)
    
    # Trier par date (les plus récentes d'abord)
    actualites_une = sorted(actualites_une, key=lambda x: x.date_evenement or x.created_at, reverse=True)[:8]

    # ═══ PRÉPARER LES DONNÉES POUR LE JAVASCRIPT (FILTRAGE AJAX) ═══
    sites_json = []
    for site in sites:
        sites_json.append({
            'slug': site.slug,
            'nom': site.nom,
            'localisation': site.localisation,
            'statut': site.statut,
            'prix_m2': float(site.prix_min or 0),
            'morcellement': float(site.superficie_min_effective or 0),
            'superficie_affichage': float(site.superficie_minimale_affichage or 0),
            'prix_min': float(site.prix_min or 0),
            'nb_dispo': site.nb_disponibles,
            'url': site.get_absolute_url(),
        })

    if request.method == 'POST':
        form = DemandeContactForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ip_address = request.META.get('REMOTE_ADDR')
            obj.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Votre demande a été envoyée !')
            return redirect('home')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': str(form.errors)})

    form = DemandeContactForm()
    return render(request, 'eden/home.html', {
        'sites': sites,
        'temoignages': temoignages,
        'promos': promos,
        'stats': stats,
        'form': form,
        'hero_config': hero_config,
        'hero_slides': hero_slides,
        'services': services,
        'etapes': etapes,
        'livret': livret,
        'actualites': actualites,
        'actualites_une': actualites_une,
        'stats_home': stats_home,
        'journaux': journaux,
        'villes': villes,
        'sites_json': sites_json,  # ⬅️ AJOUTÉ POUR LE FILTRAGE AJAX
    })
    

def sites_list(request):
    from .models import HeroConfig, HeroSlide
    from django.db.models import Q, Value, DecimalField
    from django.db.models.functions import Coalesce

    # ═══ RÉCUPÉRATION DES SITES AVEC TOUS LES CHAMPS NÉCESSAIRES ═══
    sites = SiteFoncier.objects.filter(is_active=True).prefetch_related(
        'images', 'parcelles', 'stats_manuelles'
    )
    
    # ═══ FORCER LE CHARGEMENT DES CHAMPS POUR ÉVITER LES PROBLÈMES ═══
    sites = sites.only(
        'nom', 'slug', 'localisation', 'ville', 'statut', 
        'prix_min', 'prix_max', 'morcellement',
        'en_promotion', 'description_courte', 'superficie_totale',
        'image_principale', 'superficie_minimale_affichage'
    )

    # Filtre par slug de site
    slug = request.GET.get('slug', '')
    if slug:
        sites = sites.filter(slug=slug)

    # ═══ FILTRE BUDGET CORRIGÉ ═══
    budget = request.GET.get('budget', '')
    if budget:
        try:
            b = float(budget)
            sites = sites.filter(
                Q(prix_min__lte=b) |
                Q(stats_manuelles__prix_min_manuel__lte=b) |
                Q(parcelles__prix__lte=b)
            ).distinct()
        except ValueError:
            pass

    # Filtre par statut
    statut = request.GET.get('statut', '')
    if statut:
        sites = sites.filter(statut=statut)

    # Filtre promo
    if request.GET.get('promo'):
        sites = sites.filter(en_promotion=True)

    # ═══ FILTRE SUPERFICIE CORRIGÉ ═══
    sup_min = request.GET.get('superficie_min', '')
    if sup_min:
        try:
            s = float(sup_min)
            sites = sites.filter(
                Q(parcelles__superficie__gte=s) |
                Q(stats_manuelles__superficie_min__gte=s) |
                Q(morcellement__lte=s)
            ).distinct()
        except ValueError:
            pass

    # Recherche texte
    q = request.GET.get('q', '')
    if q:
        sites = sites.filter(
            Q(nom__icontains=q) |
            Q(localisation__icontains=q) |
            Q(ville__icontains=q)
        )

    hero_config = HeroConfig.objects.filter(pk=1).first()
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('ordre')

    # ═══ PRÉPARER LES DONNÉES POUR LE JAVASCRIPT ═══
    sites_json = []

    for site in sites:
        sites_json.append({
            'slug': site.slug,
            'nom': site.nom,
            'localisation': site.localisation,
            'statut': site.statut,
            'en_promotion': site.en_promotion,
            
            # Valeurs calculées par Django
            'prix_m2': float(site.prix_min or 0),
            'morcellement': float(site.superficie_min_effective),
            'superficie_affichage': float(site.superficie_minimale_affichage) if site.superficie_minimale_affichage else 0,
            'prix_min': float(site.prix_min) if site.prix_min else 0,
            'nb_dispo': site.nb_disponibles,
        })

    return render(request, 'eden/sites_list.html', {
        'sites': sites,
        'sites_json': sites_json,
        'hero_config': hero_config,
        'hero_slides': hero_slides,
        'q': q,
        'budget': budget,
        'statut': statut,
    })

def site_detail(request, slug):
    site = get_object_or_404(SiteFoncier, slug=slug, is_active=True)
    parcelles = site.parcelles.filter(is_active=True).prefetch_related('images')
    similaires = SiteFoncier.objects.filter(is_active=True, ville=site.ville).exclude(id=site.id)[:3]
    all_sites = SiteFoncier.objects.filter(is_active=True)[:10]
    
    form = DemandeContactForm(initial={'site': site})
    
    if request.method == 'POST':
        form = DemandeContactForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ip_address = request.META.get('REMOTE_ADDR')
            obj.site = site
            obj.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Demande envoyée !'})
            
            messages.success(request, 'Demande envoyée !')
            return redirect('site_detail', slug=slug)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    return render(request, 'eden/site_detail.html', {
        'site': site,
        'parcelles': parcelles,
        'similaires': similaires,
        'form': form,
        'sites': all_sites,
    })




def parcelle_detail(request, site_slug, numero):
    site = get_object_or_404(SiteFoncier, slug=site_slug, is_active=True)
    parcelle = get_object_or_404(Parcelle, site=site, numero=numero, is_active=True)
    similaires = Parcelle.objects.filter(site=site, statut='disponible', is_active=True).exclude(id=parcelle.id)[:4]
    return render(request, 'eden/parcelle_detail.html', {'parcelle': parcelle, 'site': site, 'similaires': similaires})


def carte(request):
    sites = SiteFoncier.objects.filter(is_active=True)
    return render(request, 'eden/carte.html', {'sites': sites, 'WHATSAPP_NUMBER': '237600000000'})


def promotions(request):
    promos = Parcelle.objects.filter(is_active=True, en_promotion=True).select_related('site')
    all_sites = SiteFoncier.objects.filter(is_active=True).prefetch_related('parcelles')
    return render(request, 'eden/promotions.html', {'promos': promos, 'all_sites': all_sites})


def a_propos(request):
    """Page À Propos — 100% dynamique pilotée par l'admin."""
    from .models import (
        AProposSection, AProposElement, AProposIndicateur,
        AProposTableau, AProposEtape, AProposCellule,
        Temoignage,
    )
    import json

    # ── Charger toutes les sections actives ──
    sections = {
        s.type_section: s
        for s in AProposSection.objects.filter(is_active=True).order_by('ordre')
    }

    # ═══════════════════════════════════════════════
    # SECTION PRÉSENTATION
    # ═══════════════════════════════════════════════
    pres = sections.get('presentation')
    presentation_data = {
        'section': pres,
        'elements': AProposElement.objects.filter(
            section=pres, is_active=True
        ).order_by('ordre') if pres else [],
    }

    # ═══════════════════════════════════════════════
    # SECTION HISTOIRE (timeline)
    # ═══════════════════════════════════════════════
    hist = sections.get('histoire')
    histoire_data = {
        'section': hist,
        'etapes': AProposEtape.objects.filter(
            section=hist, is_active=True
        ).order_by('ordre') if hist else [],
    }

    # ═══════════════════════════════════════════════
    # SECTION ACTIVITÉS
    # ═══════════════════════════════════════════════
    act = sections.get('activites')
    activites_data = {
        'section': act,
        'elements': AProposElement.objects.filter(
            section=act, is_active=True
        ).order_by('ordre') if act else [],
    }

    # ═══════════════════════════════════════════════
    # SECTION CHIFFRES CLÉS (indicateurs + tableaux + graphique)
    # ═══════════════════════════════════════════════
    chf = sections.get('chiffres')
    chiffres_data = {
        'section': chf,
        'indicateurs': [],
        'tableaux': [],
        'chart_data': None,
    }

    if chf:
        # Indicateurs
        chiffres_data['indicateurs'] = AProposIndicateur.objects.filter(
            section=chf, is_active=True
        ).order_by('ordre')

        # Tableaux
        for tab in AProposTableau.objects.filter(section=chf).order_by('ordre'):
            colonnes = list(tab.colonnes.order_by('ordre'))
            lignes = []
            for ligne in tab.lignes.order_by('ordre'):
                valeurs = []
                for colonne in colonnes:
                    cellule = AProposCellule.objects.filter(ligne=ligne, colonne=colonne).first()
                    valeurs.append(cellule.valeur if cellule else '')
                lignes.append({
                    'label': ligne.label,
                    'valeurs': valeurs,
                })
            chiffres_data['tableaux'].append({
                'obj': tab,
                'titre': tab.titre,
                'est_pour_graphique': tab.est_pour_graphique,
                'colonnes': colonnes,
                'lignes': lignes,
            })

        # Préparer les données JSON pour le graphique
        for tab_data in chiffres_data['tableaux']:
            if tab_data['est_pour_graphique']:
                labels = [c.titre for c in tab_data['colonnes']]
                datasets = []
                palette = ['#fec322', '#1B4FDB', '#C8102E', '#0F6E56', '#d97706', '#7B20B4']

                for i, ligne in enumerate(tab_data['lignes']):
                    data = []
                    for col in tab_data['colonnes']:
                        val = ligne['cellules'].get(col.id, '0')
                        try:
                            data.append(float(str(val).replace(',', '.').replace(' ', '')))
                        except (ValueError, TypeError):
                            data.append(0)
                    datasets.append({
                        'label': ligne['label'],
                        'data': data,
                        'backgroundColor': palette[i % len(palette)],
                        'borderColor': palette[i % len(palette)],
                        'borderWidth': 1,
                        'borderRadius': 4,
                    })
                chiffres_data['chart_data'] = json.dumps({
                    'labels': labels,
                    'datasets': datasets,
                })
                break

    # ═══════════════════════════════════════════════
    # SECTION VALEURS
    # ═══════════════════════════════════════════════
    val = sections.get('valeurs')
    valeurs_data = {
        'section': val,
        'elements': AProposElement.objects.filter(
            section=val, is_active=True
        ).order_by('ordre') if val else [],
    }

    # ═══════════════════════════════════════════════
    # SECTION ÉQUIPE
    # ═══════════════════════════════════════════════
    eq = sections.get('equipe')
    equipe_data = {
        'section': eq,
        'elements': AProposElement.objects.filter(
            section=eq, is_active=True
        ).order_by('ordre') if eq else [],
    }

    # ═══════════════════════════════════════════════
    # TÉMOIGNAGES (existants)
    # ═══════════════════════════════════════════════
    temoignages = Temoignage.objects.filter(is_active=True).order_by('ordre', '-created_at')

    context = {
        'presentation': presentation_data,
        'histoire': histoire_data,
        'activites': activites_data,
        'chiffres': chiffres_data,
        'valeurs': valeurs_data,
        'equipe': equipe_data,
        'temoignages': temoignages,
    }

    return render(request, 'eden/a_propos.html', context)

def contact(request):
    if request.method == 'POST':
        # Accepter aussi les soumissions sans formulaire Django (depuis JS)
        nom = request.POST.get('nom', request.POST.get('prenom', '') + ' ' + request.POST.get('Nom', '')).strip()
        email = request.POST.get('email', '')
        telephone = request.POST.get('telephone', request.POST.get('Telephone / WhatsApp', ''))
        message = request.POST.get('message', request.POST.get('Message', 'Demande de contact via le site'))
        type_demande = request.POST.get('type_demande', 'reservation')

        # Si le formulaire Django standard est utilisé
        form = DemandeContactForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ip_address = request.META.get('REMOTE_ADDR')
            obj.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Message envoye !')
            return redirect('home')

        # Si les champs minimaux sont présents (formulaire custom JS)
        if telephone or email:
            c = DemandeContact()
            c.nom = nom or 'Anonyme'
            c.email = email or 'non@renseigne.cm'
            c.telephone = telephone or 'Non renseigne'
            c.message = request.POST.get('message', request.POST.get('Message', 'Demande via carte/modal'))
            c.type_demande = type_demande if type_demande in ['achat', 'visite', 'information', 'reservation', 'autre'] else 'reservation'
            c.ip_address = request.META.get('REMOTE_ADDR')
            # Site associé
            site_nom = request.POST.get('msite', request.POST.get('site_interet', ''))
            if site_nom:
                site = SiteFoncier.objects.filter(nom__icontains=site_nom.split('—')[0].strip()).first()
                if site:
                    c.site = site
            c.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Message envoye !')
            return redirect('home')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': 'Veuillez remplir les champs obligatoires.'})
    return render(request, 'eden/contact.html', {'form': DemandeContactForm()})

def reserver(request, parcelle_id):
    parcelle = get_object_or_404(Parcelle, id=parcelle_id, is_active=True)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.parcelle = parcelle
            r.montant_total = parcelle.prix_affiche
            r.save()
            if parcelle.statut == 'disponible':
                parcelle.statut = 'reservee'
                parcelle.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'reference': r.reference})
            messages.success(request, 'Reservation effectuee ! Reference : %s' % r.reference)
            return redirect('home')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': str(form.errors)})
    return render(request, 'eden/reservation.html', {'parcelle': parcelle, 'form': ReservationForm()})

def demande_visite(request):
    if request.method == 'POST':
        form = VisiteForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Demande de visite enregistree !')
            return redirect('home')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors})
    return render(request, 'eden/visite.html', {'form': VisiteForm()})


# ═══════════════════════════════════════════════
# API JSON
# ═══════════════════════════════════════════════

def api_stats(request):
    total = Parcelle.objects.filter(is_active=True).count()
    vendues = Parcelle.objects.filter(statut='vendue').count()
    return JsonResponse({
        'sites': SiteFoncier.objects.filter(is_active=True).count(),
        'total': total, 'vendues': vendues,
        'disponibles': Parcelle.objects.filter(statut='disponible').count(),
        'pourcentage': round((vendues / total * 100), 1) if total else 0,
    })


def api_sites_geo(request):
    sites = SiteFoncier.objects.filter(is_active=True)
    features = []
    for s in sites:
        image_url = request.build_absolute_uri(s.image_principale.url) if s.image_principale else None
        # Chercher aussi la première image galerie
        if not image_url:
            first_img = s.images.first()
            if first_img:
                image_url = request.build_absolute_uri(first_img.image.url)
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [float(s.longitude), float(s.latitude)]} if s.latitude and s.longitude else None,
            'properties': {
                'id': str(s.id), 'nom': s.nom, 'slug': s.slug,
                'statut': s.statut, 'ville': s.ville, 'localisation': s.localisation,
                'pourcentage': s.pourcentage_vendu, 'disponibles': s.nb_disponibles,
                'vendues': s.nb_vendues, 'total': s.nb_parcelles_total,
                'prix_min': float(s.prix_min) if s.prix_min else None,
                'zoom': s.zoom_carte, 'en_promotion': s.en_promotion,
                'description_courte': s.description_courte, 'image_url': image_url,
            }
        })
    return JsonResponse({'type': 'FeatureCollection', 'features': features})


def api_parcelles_geo(request):
    site_slug = request.GET.get('site')
    qs = Parcelle.objects.filter(is_active=True).select_related('site').prefetch_related('images')
    if site_slug:
        qs = qs.filter(site__slug=site_slug)
    features = []
    for p in qs:
        image_url = None
        first_img = p.images.first()
        if first_img:
            image_url = request.build_absolute_uri(first_img.image.url)
        elif p.site.image_principale:
            image_url = request.build_absolute_uri(p.site.image_principale.url)
        props = {
            'id': str(p.id), 'numero': p.numero,
            'superficie': float(p.superficie), 'prix': float(p.prix_affiche),
            'prix_m2': p.prix_m2, 'statut': p.statut, 'couleur': p.couleur_statut,
            'site_nom': p.site.nom, 'site_slug': p.site.slug,
            'en_promotion': p.en_promotion, 'reduction': p.reduction_pct,
            'description': p.description, 'image_url': image_url,
        }
        if p.geojson:
            features.append({'type': 'Feature', 'geometry': p.geojson, 'properties': props})
        elif p.latitude and p.longitude:
            features.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [float(p.longitude), float(p.latitude)]}, 'properties': props})
    return JsonResponse({'type': 'FeatureCollection', 'features': features})


def api_recherche(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'sites': [], 'parcelles': []})
    sites = SiteFoncier.objects.filter(Q(nom__icontains=q) | Q(ville__icontains=q) | Q(localisation__icontains=q), is_active=True)[:5]
    parcelles = Parcelle.objects.filter(Q(numero__icontains=q) | Q(site__nom__icontains=q), is_active=True).select_related('site')[:8]
    return JsonResponse({
        'sites': [{'id': str(s.id), 'nom': s.nom, 'ville': s.ville, 'slug': s.slug,
                   'lat': float(s.latitude) if s.latitude else None,
                   'lng': float(s.longitude) if s.longitude else None} for s in sites],
        'parcelles': [{'id': str(p.id), 'numero': p.numero, 'site': p.site.nom,
                       'prix': float(p.prix_affiche), 'superficie': float(p.superficie),
                       'statut': p.statut,
                       'lat': float(p.latitude) if p.latitude else None,
                       'lng': float(p.longitude) if p.longitude else None} for p in parcelles],
    })


@csrf_exempt
def api_geo_import(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Non autorise'}, status=403)
    try:
        data = json.loads(request.body)
        site = SiteFoncier.objects.get(id=data.get('site_id'))
        created = []
        geo_data = data.get('data', {})
        if geo_data.get('type') == 'FeatureCollection':
            for i, feature in enumerate(geo_data.get('features', [])):
                props = feature.get('properties', {})
                numero = props.get('numero') or 'P-%03d' % (i + 1)
                p, _ = Parcelle.objects.get_or_create(
                    site=site, numero=numero,
                    defaults={'superficie': props.get('superficie', 1), 'prix': props.get('prix', 0), 'geojson': feature.get('geometry')}
                )
                created.append(numero)
        return JsonResponse({'success': True, 'created': len(created)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ═══════════════════════════════════════════════
# DASHBOARD — COMPLET SANS ADMIN DJANGO
# ═══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_home(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    stats = {
        'sites': SiteFoncier.objects.count(),
        'sites_actifs': SiteFoncier.objects.filter(is_active=True).count(),
        'parcelles_total': Parcelle.objects.filter(is_active=True).count(),
        'disponibles': Parcelle.objects.filter(statut='disponible').count(),
        'vendues': Parcelle.objects.filter(statut='vendue').count(),
        'reservees': Parcelle.objects.filter(statut='reservee').count(),
        'reservations_total': Reservation.objects.count(),
        'reservations_mois': Reservation.objects.filter(created_at__date__gte=month_start).count(),
        'contacts_nouveaux': DemandeContact.objects.filter(statut='nouveau').count(),
        'contacts_total': DemandeContact.objects.count(),
        'chiffre_affaires': float(Reservation.objects.filter(statut='payee').aggregate(t=Sum('montant_total'))['t'] or 0),
        'temoignages': Temoignage.objects.count(),
        'utilisateurs': User.objects.count(),
        'visites_a_venir': VisiteProgrammee.objects.filter(date_visite__gte=timezone.now(), statut__in=['demandee', 'confirmee']).count(),
    }
    sites_perf = SiteFoncier.objects.filter(is_active=True).prefetch_related('parcelles')
    derniers_contacts = DemandeContact.objects.order_by('-created_at')[:6]
    dernieres_reservations = Reservation.objects.order_by('-created_at').select_related('parcelle__site')[:6]
    from datetime import date
    chart = []
    for i in range(11, -1, -1):
        month = (today.month - i - 1) % 12 + 1
        year = today.year - ((i - today.month + 1) // 12)
        try:
            m_start = date(year, month, 1)
            m_end = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
            cnt = Reservation.objects.filter(created_at__date__gte=m_start, created_at__date__lt=m_end).count()
            chart.append({'mois': m_start.strftime('%b'), 'count': cnt})
        except Exception:
            chart.append({'mois': '?', 'count': 0})
    return render(request, 'eden/dashboard/home.html', {
        'stats': stats, 'sites_perf': sites_perf,
        'derniers_contacts': derniers_contacts,
        'dernieres_reservations': dernieres_reservations,
        'chart_data': json.dumps(chart),
    })


# ── SITES ──

@login_required
@user_passes_test(is_agent)
def dashboard_sites(request):
    qs = SiteFoncier.objects.all().prefetch_related('parcelles', 'images').order_by('-created_at')
    q = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(ville__icontains=q))
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, 'eden/dashboard/sites.html', {'sites': qs, 'q': q, 'statut': statut})


@login_required
@user_passes_test(is_agent)
def dashboard_site_form(request, pk=None):
    site = get_object_or_404(SiteFoncier, pk=pk) if pk else None
    if request.method == 'POST':
        form = SiteFoncierForm(request.POST, request.FILES, instance=site)
        if form.is_valid():
            saved = form.save()
            for img in request.FILES.getlist('gallery_images'):
                ImageSite.objects.create(site=saved, image=img)
            messages.success(request, 'Site enregistre avec succes.')
            return redirect('dashboard_sites')
    else:
        form = SiteFoncierForm(instance=site)
    return render(request, 'eden/dashboard/site_form.html', {
        'form': form, 'site': site,
        'images_site': site.images.all() if site else []
    })


@login_required
@user_passes_test(is_agent)
def dashboard_site_toggle(request, pk):
    site = get_object_or_404(SiteFoncier, pk=pk)
    if request.method == 'POST':
        site.is_active = not site.is_active
        site.save()
        return JsonResponse({'success': True, 'is_active': site.is_active})
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_agent)
def dashboard_site_supprimer(request, pk):
    site = get_object_or_404(SiteFoncier, pk=pk)
    if request.method == 'POST':
        nom = site.nom
        site.delete()
        messages.success(request, 'Site "%s" supprime.' % nom)
        return redirect('dashboard_sites')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': site, 'retour': 'dashboard_sites'})


@login_required
@user_passes_test(is_agent)
def dashboard_image_site_supprimer(request, pk):
    img = get_object_or_404(ImageSite, pk=pk)
    img.delete()
    return JsonResponse({'success': True})


# ── PARCELLES ──

@login_required
@user_passes_test(is_agent)
def dashboard_parcelles(request):
    qs = Parcelle.objects.all().select_related('site').order_by('-created_at')
    site_slug = request.GET.get('site', '')
    statut = request.GET.get('statut', '')
    q = request.GET.get('q', '')
    if site_slug:
        qs = qs.filter(site__slug=site_slug)
    if statut:
        qs = qs.filter(statut=statut)
    if q:
        qs = qs.filter(Q(numero__icontains=q) | Q(site__nom__icontains=q))
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'eden/dashboard/parcelles.html', {
        'parcelles': page, 'sites': SiteFoncier.objects.all(),
        'site_slug': site_slug, 'statut': statut, 'q': q
    })


@login_required
@user_passes_test(is_agent)
def dashboard_parcelle_form(request, pk=None):
    parcelle = get_object_or_404(Parcelle, pk=pk) if pk else None
    if request.method == 'POST':
        form = ParcelleForm(request.POST, request.FILES, instance=parcelle)
        if form.is_valid():
            saved = form.save()
            for img in request.FILES.getlist('gallery_images'):
                ImageParcelle.objects.create(parcelle=saved, image=img)
            messages.success(request, 'Parcelle enregistree.')
            return redirect('dashboard_parcelles')
    else:
        form = ParcelleForm(instance=parcelle)
    return render(request, 'eden/dashboard/parcelle_form.html', {
        'form': form, 'parcelle': parcelle,
        'images_parcelle': parcelle.images.all() if parcelle else [],
        'sites': SiteFoncier.objects.all()
    })


@login_required
@user_passes_test(is_agent)
def dashboard_parcelle_supprimer(request, pk):
    parcelle = get_object_or_404(Parcelle, pk=pk)
    if request.method == 'POST':
        parcelle.delete()
        messages.success(request, 'Parcelle supprimee.')
        return redirect('dashboard_parcelles')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': parcelle, 'retour': 'dashboard_parcelles'})


@login_required
@user_passes_test(is_agent)
def dashboard_parcelle_statut(request, pk):
    if request.method == 'POST':
        parcelle = get_object_or_404(Parcelle, pk=pk)
        nouveau = request.POST.get('statut')
        if nouveau in ['disponible', 'reservee', 'vendue', 'indisponible']:
            parcelle.statut = nouveau
            parcelle.save()
            return JsonResponse({'success': True, 'statut': parcelle.get_statut_display(), 'couleur': parcelle.couleur_statut})
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_agent)
def dashboard_image_parcelle_supprimer(request, pk):
    img = get_object_or_404(ImageParcelle, pk=pk)
    img.delete()
    return JsonResponse({'success': True})


# ── RÉSERVATIONS ──

@login_required
@user_passes_test(is_agent)
def dashboard_reservations(request):
    qs = Reservation.objects.all().select_related('parcelle__site').order_by('-created_at')
    statut = request.GET.get('statut', '')
    q = request.GET.get('q', '')
    if statut:
        qs = qs.filter(statut=statut)
    if q:
        qs = qs.filter(Q(nom_client__icontains=q) | Q(reference__icontains=q) | Q(telephone_client__icontains=q))
    paginator = Paginator(qs, 25)
    return render(request, 'eden/dashboard/reservations.html', {
        'reservations': paginator.get_page(request.GET.get('page')),
        'statut': statut, 'q': q, 'total': qs.count()
    })


@login_required
@user_passes_test(is_agent)
def dashboard_reservation_detail(request, pk):
    r = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut:
            r.statut = nouveau_statut
            r.save()
            if nouveau_statut == 'payee':
                r.parcelle.statut = 'vendue'
                r.parcelle.save()
            elif nouveau_statut == 'annulee':
                r.parcelle.statut = 'disponible'
                r.parcelle.save()
            messages.success(request, 'Statut mis a jour.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
    return render(request, 'eden/dashboard/reservation_detail.html', {'reservation': r})


@login_required
@user_passes_test(is_agent)
def dashboard_reservation_supprimer(request, pk):
    r = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        r.delete()
        messages.success(request, 'Reservation supprimee.')
        return redirect('dashboard_reservations')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': r, 'retour': 'dashboard_reservations'})


# ── CONTACTS ──

@login_required
@user_passes_test(is_agent)
def dashboard_contacts(request):
    qs = DemandeContact.objects.all().order_by('-created_at')
    statut = request.GET.get('statut', '')
    type_d = request.GET.get('type', '')
    q = request.GET.get('q', '')
    if statut:
        qs = qs.filter(statut=statut)
    if type_d:
        qs = qs.filter(type_demande=type_d)
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(telephone__icontains=q) | Q(email__icontains=q))
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pk = request.POST.get('pk')
        nouveau_statut = request.POST.get('statut')
        if pk and nouveau_statut:
            DemandeContact.objects.filter(pk=pk).update(statut=nouveau_statut)
            return JsonResponse({'success': True})
    paginator = Paginator(qs, 20)
    return render(request, 'eden/dashboard/contacts.html', {
        'contacts': paginator.get_page(request.GET.get('page')),
        'statut': statut, 'type_d': type_d, 'q': q,
        'nouveaux': DemandeContact.objects.filter(statut='nouveau').count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_contact_detail(request, pk):
    c = get_object_or_404(DemandeContact, pk=pk)
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        notes = request.POST.get('notes_internes', '')
        if nouveau_statut:
            c.statut = nouveau_statut
        if notes:
            c.notes_internes = notes
        c.save()
        messages.success(request, 'Contact mis a jour.')
    return render(request, 'eden/dashboard/contact_detail.html', {'contact': c})


@login_required
@user_passes_test(is_agent)
def dashboard_contact_supprimer(request, pk):
    c = get_object_or_404(DemandeContact, pk=pk)
    if request.method == 'POST':
        c.delete()
        messages.success(request, 'Contact supprime.')
        return redirect('dashboard_contacts')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': c, 'retour': 'dashboard_contacts'})


# ── VISITES ──

@login_required
@user_passes_test(is_agent)
def dashboard_visites(request):
    visites = VisiteProgrammee.objects.all().select_related('site').order_by('-date_visite')
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pk = request.POST.get('pk')
        statut = request.POST.get('statut')
        if pk and statut:
            VisiteProgrammee.objects.filter(pk=pk).update(statut=statut)
            return JsonResponse({'success': True})
    return render(request, 'eden/dashboard/visites.html', {'visites': visites})


@login_required
@user_passes_test(is_agent)
def dashboard_visite_form(request, pk=None):
    visite = get_object_or_404(VisiteProgrammee, pk=pk) if pk else None
    if request.method == 'POST':
        form = VisiteForm(request.POST, instance=visite)
        if form.is_valid():
            form.save()
            messages.success(request, 'Visite enregistree.')
            return redirect('dashboard_visites')
    else:
        form = VisiteForm(instance=visite)
    return render(request, 'eden/dashboard/visite_form.html', {'form': form, 'visite': visite})


@login_required
@user_passes_test(is_agent)
def dashboard_visite_supprimer(request, pk):
    v = get_object_or_404(VisiteProgrammee, pk=pk)
    if request.method == 'POST':
        v.delete()
        messages.success(request, 'Visite supprimee.')
        return redirect('dashboard_visites')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': v, 'retour': 'dashboard_visites'})


# ── PROMOTIONS ──

@login_required
@user_passes_test(is_agent)
def dashboard_promotions(request):
    promos_parcelles = Parcelle.objects.filter(en_promotion=True).select_related('site').order_by('-created_at')
    promos_sites = SiteFoncier.objects.filter(en_promotion=True).order_by('-created_at')
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pk = request.POST.get('pk')
        type_obj = request.POST.get('type')
        action = request.POST.get('action')
        if type_obj == 'parcelle' and pk:
            Parcelle.objects.filter(pk=pk).update(en_promotion=(action == 'activer'))
        elif type_obj == 'site' and pk:
            SiteFoncier.objects.filter(pk=pk).update(en_promotion=(action == 'activer'))
        return JsonResponse({'success': True})
    toutes_parcelles = Parcelle.objects.filter(statut='disponible', is_active=True).select_related('site').order_by('site__nom', 'numero')
    tous_sites = SiteFoncier.objects.filter(is_active=True).order_by('nom')
    return render(request, 'eden/dashboard/promotions.html', {
        'promos_parcelles': promos_parcelles, 'promos_sites': promos_sites,
        'toutes_parcelles': toutes_parcelles, 'tous_sites': tous_sites,
    })


# ── TÉMOIGNAGES ──

@login_required
@user_passes_test(is_agent)
def dashboard_temoignages(request):
    temoignages = Temoignage.objects.all().select_related('site').order_by('ordre', '-created_at')
    return render(request, 'eden/dashboard/temoignages.html', {'temoignages': temoignages})


@login_required
@user_passes_test(is_agent)
def dashboard_temoignage_form(request, pk=None):
    t = get_object_or_404(Temoignage, pk=pk) if pk else None
    if request.method == 'POST':
        form = TemoignageForm(request.POST, request.FILES, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, 'Temoignage enregistre.')
            return redirect('dashboard_temoignages')
    else:
        form = TemoignageForm(instance=t)
    return render(request, 'eden/dashboard/temoignage_form.html', {'form': form, 'obj': t})


@login_required
@user_passes_test(is_agent)
def dashboard_temoignage_supprimer(request, pk):
    t = get_object_or_404(Temoignage, pk=pk)
    if request.method == 'POST':
        t.delete()
        messages.success(request, 'Temoignage supprime.')
        return redirect('dashboard_temoignages')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': t, 'retour': 'dashboard_temoignages'})


# ── UTILISATEURS ──

@login_required
@user_passes_test(lambda u: u.is_superuser)
def dashboard_utilisateurs(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'eden/dashboard/utilisateurs.html', {'users': users})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def dashboard_utilisateur_form(request, pk=None):
    user_obj = get_object_or_404(User, pk=pk) if pk else None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        password = request.POST.get('password', '').strip()

        if user_obj:
            user_obj.username = username
            user_obj.email = email
            user_obj.first_name = first_name
            user_obj.last_name = last_name
            user_obj.is_staff = is_staff
            user_obj.is_superuser = is_superuser
            user_obj.is_active = is_active
            if password:
                user_obj.set_password(password)
                update_session_auth_hash(request, user_obj)
            user_obj.save()
            messages.success(request, 'Utilisateur modifie.')
        else:
            if not password:
                messages.error(request, 'Le mot de passe est requis.')
                return render(request, 'eden/dashboard/utilisateur_form.html', {'user_obj': user_obj})
            new_user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name,
                is_staff=is_staff, is_superuser=is_superuser, is_active=is_active
            )
            messages.success(request, 'Utilisateur cree.')
        return redirect('dashboard_utilisateurs')
    return render(request, 'eden/dashboard/utilisateur_form.html', {'user_obj': user_obj})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def dashboard_utilisateur_supprimer(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte.')
        return redirect('dashboard_utilisateurs')
    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, 'Utilisateur supprime.')
        return redirect('dashboard_utilisateurs')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': user_obj, 'retour': 'dashboard_utilisateurs'})


# ── PARAMÈTRES ──

@login_required
@user_passes_test(is_agent)
def dashboard_parametres(request):
    if request.method == 'POST':
        # Changer mot de passe
        if request.POST.get('action') == 'change_password':
            old_pw = request.POST.get('old_password')
            new_pw = request.POST.get('new_password')
            if request.user.check_password(old_pw):
                request.user.set_password(new_pw)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Mot de passe modifie.')
            else:
                messages.error(request, 'Ancien mot de passe incorrect.')
    return render(request, 'eden/dashboard/parametres.html')


# ── AUTH ──

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard_home'))
        messages.error(request, 'Identifiants incorrects.')
    return render(request, 'eden/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@csrf_exempt
def api_groupy(request):
    """GROUPY — Chatbot EDEN GROUP avec base de connaissances + fallback Claude."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        from .models import GroupyQR
        import difflib

        body = json.loads(request.body)
        message = body.get('message', '').strip()
        historique = body.get('historique', [])

        if not message:
            return JsonResponse({'success': False, 'answer': 'Message vide.'})

        msg_lower = message.lower()

        # ════════════════════════════════════════
        # ÉTAPE 1 — Chercher dans la base Q&R
        # ════════════════════════════════════════
        qrs = GroupyQR.objects.filter(is_active=True).order_by('-priorite', '-nb_utilisations')

        meilleur_score = 0
        meilleure_reponse = None

        for qr in qrs:
            score = 0

            # 1a. Correspondance exacte avec une des questions
            for q_variante in qr.get_questions_list():
                if q_variante in msg_lower or msg_lower in q_variante:
                    score = max(score, 90)
                # Similarité floue
                ratio = difflib.SequenceMatcher(None, msg_lower, q_variante).ratio()
                if ratio > 0.7:
                    score = max(score, int(ratio * 85))

            # 1b. Correspondance par mots-clés
            mots = qr.get_mots_cles_list()
            if mots:
                matches = sum(1 for m in mots if m in msg_lower)
                if matches > 0:
                    kw_score = min(80, 40 + (matches / len(mots)) * 50)
                    score = max(score, kw_score)

            # 1c. Mots de la question dans le message
            mots_question = [
                w for w in qr.question.lower().split()
                if len(w) > 3 and w not in ['pour', 'dans', 'avec', 'vous', 'nous', 'votre', 'notre', 'comment', 'quand', 'quel']
            ]
            if mots_question:
                matches_q = sum(1 for m in mots_question if m in msg_lower)
                if matches_q >= 2:
                    q_score = min(75, 30 + (matches_q / len(mots_question)) * 60)
                    score = max(score, q_score)

            if score > meilleur_score:
                meilleur_score = score
                meilleure_reponse = qr

        # Si score suffisant → répondre depuis la base
        SEUIL = 45
        if meilleur_score >= SEUIL and meilleure_reponse:
            # Incrémenter le compteur d'utilisation
            GroupyQR.objects.filter(pk=meilleure_reponse.pk).update(
                nb_utilisations=models.F('nb_utilisations') + 1
            )

            # Enrichir la réponse avec des données dynamiques
            reponse = enrichir_reponse(meilleure_reponse.reponse)
            return JsonResponse({
                'success': True,
                'answer': reponse,
                'source': 'base',
                'score': meilleur_score
            })

        # ════════════════════════════════════════
        # ÉTAPE 2 — Fallback Claude avec contexte EDEN GROUP
        # ════════════════════════════════════════
        reponse_claude = appeler_claude_groupy(message, historique)
        return JsonResponse({
            'success': True,
            'answer': reponse_claude,
            'source': 'ia'
        })

    except Exception as e:
        print(f"Erreur api_groupy: {e}")
        return JsonResponse({
            'success': False,
            'answer': "Je rencontre une difficulté momentanée. Contactez-nous directement au **+237 600 000 000** ou par WhatsApp !"
        })


def enrichir_reponse(reponse):
    """Remplace les variables dynamiques dans une réponse."""
    sites = SiteFoncier.objects.filter(is_active=True)
    total_dispo = Parcelle.objects.filter(statut='disponible').count()
    total_sites = sites.count()
    promo_count = Parcelle.objects.filter(en_promotion=True, is_active=True).count()

    reponse = reponse.replace('{NB_SITES}', str(total_sites))
    reponse = reponse.replace('{NB_DISPONIBLES}', str(total_dispo))
    reponse = reponse.replace('{NB_PROMOS}', str(promo_count))
    reponse = reponse.replace('{TEL}', '+237 600 000 000')
    reponse = reponse.replace('{EMAIL}', 'info@edengroup.cm')
    reponse = reponse.replace('{HORAIRES}', 'Lun-Ven 8h-18h | Sam 9h-13h')

    # Liste des sites disponibles si demandé
    if '{LISTE_SITES}' in reponse:
        liste = ''
        for s in sites:
            emoji = '🟢' if s.statut == 'disponible' else '🟡' if s.statut == 'en_cours' else '🔴'
            liste += f"\n{emoji} **{s.nom}** — {s.localisation}"
            if s.nb_disponibles > 0:
                liste += f" ({s.nb_disponibles} dispo)"
            if s.prix_min:
                liste += f" · dès {float(s.prix_min)/1000000:.1f}M FCFA"
        reponse = reponse.replace('{LISTE_SITES}', liste if liste else "\nAucun site pour le moment.")

    # Liste des promotions
    if '{LISTE_PROMOS}' in reponse:
        promos = Parcelle.objects.filter(
            en_promotion=True, is_active=True
        ).select_related('site')
        liste = ''
        for p in promos:
            liste += f"\n🔥 **{p.site.nom}** - Parcelle {p.numero}"
            liste += f"\n   {float(p.superficie):.0f}m² · {float(p.prix_affiche)/1000000:.1f}M FCFA"
            liste += f" (-{p.reduction_pct}%)"
            if p.promo_fin:
                liste += f" · expire {p.promo_fin.strftime('%d/%m/%Y')}"
        reponse = reponse.replace('{LISTE_PROMOS}', liste if liste else "\nAucune promotion pour le moment.")

    return reponse


def appeler_claude_groupy(message, historique):
    """Appel Claude pour les questions hors base avec contexte EDEN GROUP."""
    import urllib.request
    import urllib.error

    # Construire le contexte minimal mais précis
    sites = SiteFoncier.objects.filter(is_active=True)
    sites_txt = '\n'.join([
        f"- {s.nom} ({s.localisation}): {s.nb_disponibles} parcelles disponibles"
        + (f", dès {float(s.prix_min)/1000000:.1f}M FCFA" if s.prix_min else "")
        for s in sites
    ]) or "Aucun site configuré"

    total_dispo = Parcelle.objects.filter(statut='disponible').count()
    nb_promos = Parcelle.objects.filter(en_promotion=True, is_active=True).count()

    system = f"""Tu es GROUPY, l'assistant virtuel d'EDEN GROUP, plateforme foncière premium à Yaoundé, Cameroun.

CONTEXTE ACTUEL EDEN GROUP:
- Sites actifs: {sites.count()} | Parcelles disponibles: {total_dispo} | Promotions: {nb_promos}
{sites_txt}

Contact: +237 600 000 000 | info@edengroup.cm | Lun-Ven 8h-18h

RÈGLES:
- Réponds UNIQUEMENT sur EDEN GROUP et l'immobilier/foncier camerounais
- Si hors sujet: "Je suis spécialisé sur EDEN GROUP. Une question sur nos terrains ?"
- Français, max 150 mots, professionnel et chaleureux, emojis pertinents
- Cite les vraies données ci-dessus
- Pour réserver: orientez vers +237 600 000 000 ou le bouton Réserver du site
- Tu es GROUPY, fier représentant d'EDEN GROUP"""

    messages = []
    for m in historique[-6:]:
        if m.get('role') in ['user', 'assistant'] and m.get('content'):
            messages.append({'role': m['role'], 'content': m['content']})
    messages.append({'role': 'user', 'content': message})

    try:
        payload = json.dumps({
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 500,
            'system': system,
            'messages': messages
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01',
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['content'][0]['text']

    except Exception as e:
        print(f"Claude API error: {e}")
        return (
            "Je n'ai pas pu trouver une réponse précise à votre question.\n\n"
            "Notre équipe vous répondra avec plaisir :\n"
            "📞 **+237 600 000 000**\n"
            "✉ info@edengroup.cm\n"
            "💬 WhatsApp disponible !"
        )
    
# ── GROUPY DASHBOARD ──

@login_required
@user_passes_test(is_agent)
def dashboard_groupy(request):
    from .models import GroupyQR, GroupyCategorie
    qrs = GroupyQR.objects.all().select_related('categorie').order_by('-priorite', '-nb_utilisations')
    categories = GroupyCategorie.objects.filter(is_active=True)
    cat_filtre = request.GET.get('cat', '')
    q = request.GET.get('q', '')
    if cat_filtre:
        qrs = qrs.filter(categorie__id=cat_filtre)
    if q:
        qrs = qrs.filter(
            Q(question__icontains=q) | Q(reponse__icontains=q) | Q(mots_cles__icontains=q)
        )
    paginator = Paginator(qrs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'eden/dashboard/groupy.html', {
        'qrs': page, 'categories': categories,
        'cat_filtre': cat_filtre, 'q': q,
        'total': GroupyQR.objects.count(),
        'actifs': GroupyQR.objects.filter(is_active=True).count(),
        'top_questions': GroupyQR.objects.filter(nb_utilisations__gt=0).order_by('-nb_utilisations')[:5],
    })


@login_required
@user_passes_test(is_agent)
def dashboard_groupy_qr_form(request, pk=None):
    from .models import GroupyQR, GroupyCategorie
    qr = get_object_or_404(GroupyQR, pk=pk) if pk else None
    categories = GroupyCategorie.objects.filter(is_active=True)
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        reponse = request.POST.get('reponse', '').strip()
        mots_cles = request.POST.get('mots_cles', '').strip()
        cat_id = request.POST.get('categorie')
        priorite = int(request.POST.get('priorite', 0))
        is_active = request.POST.get('is_active') == 'on'
        if question and reponse:
            if qr:
                qr.question = question
                qr.reponse = reponse
                qr.mots_cles = mots_cles
                qr.priorite = priorite
                qr.is_active = is_active
                qr.categorie_id = cat_id if cat_id else None
                qr.save()
                messages.success(request, 'Q&R modifiée.')
            else:
                GroupyQR.objects.create(
                    question=question, reponse=reponse,
                    mots_cles=mots_cles, priorite=priorite,
                    is_active=is_active,
                    categorie_id=cat_id if cat_id else None
                )
                messages.success(request, 'Q&R ajoutée à la base GROUPY.')
            return redirect('dashboard_groupy')
        else:
            messages.error(request, 'La question et la réponse sont obligatoires.')
    return render(request, 'eden/dashboard/groupy_form.html', {
        'qr': qr, 'categories': categories
    })


@login_required
@user_passes_test(is_agent)
def dashboard_groupy_qr_supprimer(request, pk):
    from .models import GroupyQR
    qr = get_object_or_404(GroupyQR, pk=pk)
    if request.method == 'POST':
        qr.delete()
        messages.success(request, 'Q&R supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_groupy')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': qr, 'retour': 'dashboard_groupy'})


@login_required
@user_passes_test(is_agent)
def dashboard_groupy_categories(request):
    from .models import GroupyCategorie
    categories = GroupyCategorie.objects.annotate(
        nb_questions=models.Count('questions')
    )
    return render(request, 'eden/dashboard/groupy_categories.html', {'categories': categories})


@login_required
@user_passes_test(is_agent)
def dashboard_groupy_cat_form(request):
    from .models import GroupyCategorie
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        emoji = request.POST.get('emoji', '💬').strip()
        if nom:
            GroupyCategorie.objects.create(nom=nom, emoji=emoji)
            messages.success(request, 'Catégorie créée.')
        return redirect('dashboard_groupy_categories')
    return redirect('dashboard_groupy_categories')


@login_required
@user_passes_test(is_agent)
def dashboard_groupy_cat_supprimer(request, pk):
    from .models import GroupyCategorie
    cat = get_object_or_404(GroupyCategorie, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Catégorie supprimée.')
        return redirect('dashboard_groupy_categories')
    return render(request, 'eden/dashboard/confirm_delete.html', {'objet': cat, 'retour': 'dashboard_groupy_categories'})


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_groupy_toggle(request):
    """Toggle actif/inactif d'une Q&R GROUPY."""
    if request.method == 'POST':
        from .models import GroupyQR
        pk = request.GET.get('pk')
        if pk:
            qr = get_object_or_404(GroupyQR, pk=pk)
            qr.is_active = not qr.is_active
            qr.save()
            return JsonResponse({'success': True, 'is_active': qr.is_active})
    return JsonResponse({'success': False})

# ══════════════════════════════════════════════
# JOURNAL EDEN GROUP
# ══════════════════════════════════════════════

def journal_kiosque(request):
    """Kiosque — liste des éditions publiées."""
    from .models import JournalEdition
    # Journaux seulement (pas articles/revues/guides)
    editions = JournalEdition.objects.filter(
        statut='publie', type_academie='journal'
    ).order_by('-date_parution', '-created_at')
    derniere = editions.first()
    return render(request, 'eden/journal/kiosque.html', {
        'editions': editions,
        'derniere': derniere,
    })


def journal_lire(request, numero):
    """Visionneuse flipbook — accepte slug ET entiers."""
    from .models import JournalEdition
    edition = get_object_or_404(JournalEdition, numero=numero, statut='publie')
    pages = edition.pages.order_by('numero')

    pages_json = json.dumps([
        {
            'numero': p.numero,
            'layout': p.layout,
            'contenu': p.contenu,
            'couleur_fond': p.couleur_fond
        }
        for p in pages
    ], ensure_ascii=False)

    return render(request, 'eden/journal/lire.html', {
        'edition': edition,
        'pages': pages,
        'pages_json': pages_json,
        'from_academie': request.GET.get('from') == 'academie',
    })


def journal_page_json(request, numero, page):
    from .models import JournalEdition, JournalPage
    edition = get_object_or_404(JournalEdition, numero=numero, statut='publie')
    p = get_object_or_404(JournalPage, edition=edition, numero=page)
    return JsonResponse({'layout': p.layout, 'contenu': p.contenu, 'couleur_fond': p.couleur_fond})


# ── Dashboard Journal ──

@login_required
@user_passes_test(is_agent)
def dashboard_journal(request):
    from .models import JournalEdition
    editions = JournalEdition.objects.all().order_by('-created_at')
    # Séparer journaux et publications académie
    journaux = editions.filter(type_academie='journal')
    academie = editions.exclude(type_academie='journal')
    return render(request, 'eden/dashboard/journal.html', {
        'editions': editions,
        'journaux': journaux,
        'academie': academie,
    })

@login_required
@user_passes_test(is_agent)
def dashboard_journal_edition_form(request, pk=None):
    from .models import JournalEdition
    import uuid as _uuid
    edition = get_object_or_404(JournalEdition, pk=pk) if pk else None

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/journal_edition_form.html', {
                'edition': edition
            })

        if not edition:
            edition = JournalEdition()

        edition.titre = titre
        edition.sous_titre = request.POST.get('sous_titre', '').strip()
        edition.type_academie = request.POST.get('type_academie', 'journal')
        edition.statut = request.POST.get('statut', 'brouillon')

        # ✅ Numéro : auto-généré si vide, garanti unique
        numero = request.POST.get('numero', '').strip()
        if not numero:
            prefix = {
                'journal': 'JNL',
                'article': 'ART',
                'revue': 'REV',
                'guide': 'GUI',
            }.get(edition.type_academie, 'PUB')
            for _ in range(20):
                candidat = f"{prefix}-{str(_uuid.uuid4())[:8].upper()}"
                if not JournalEdition.objects.filter(numero=candidat).exclude(
                    pk=edition.pk if edition.pk else 0
                ).exists():
                    numero = candidat
                    break

        # Vérifier unicité si numéro manuel
        qs_check = JournalEdition.objects.filter(numero=numero)
        if edition.pk:
            qs_check = qs_check.exclude(pk=edition.pk)
        if qs_check.exists():
            messages.error(request, f'Le numéro "{numero}" existe déjà.')
            return render(request, 'eden/dashboard/journal_edition_form.html', {
                'edition': edition
            })

        edition.numero = numero

        date_str = request.POST.get('date_parution', '')
        if date_str:
            from datetime import date
            try:
                edition.date_parution = date.fromisoformat(date_str)
            except Exception:
                pass

        if request.FILES.get('image_une'):
            edition.image_une = request.FILES['image_une']

        edition.save()

        # Créer page 1 si nouvelle édition
        if not edition.pages.exists():
            from .models import JournalPage
            JournalPage.objects.create(
                edition=edition, numero=1,
                contenu=[], layout='col2'
            )

        messages.success(request, f'"{edition.titre}" enregistré.')

        # Ouvrir éditeur si demandé
        if request.POST.get('action') == 'editeur':
            return redirect('dashboard_journal_page_editer',
                            edition_pk=edition.pk, page_num=1)

        return redirect('dashboard_journal')

    return render(request, 'eden/dashboard/journal_edition_form.html', {
        'edition': edition,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_journal_edition_supprimer(request, pk):
    from .models import JournalEdition
    edition = get_object_or_404(JournalEdition, pk=pk)
    if request.method == 'POST':
        titre = edition.titre
        edition.delete()
        messages.success(request, f'"{titre}" supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_journal')
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_agent)
def dashboard_journal_publier(request, pk):
    from .models import JournalEdition
    from datetime import date
    edition = get_object_or_404(JournalEdition, pk=pk)
    if request.method == 'POST':
        if edition.statut == 'publie':
            edition.statut = 'brouillon'
        else:
            edition.statut = 'publie'
            if not edition.date_parution:
                edition.date_parution = date.today()
        edition.save()
        return JsonResponse({'success': True, 'statut': edition.statut})
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_agent)
def dashboard_journal_page_editer(request, edition_pk, page_num):
    from .models import JournalEdition, JournalPage, JournalMedia
    edition = get_object_or_404(JournalEdition, pk=edition_pk)
    page, created = JournalPage.objects.get_or_create(
        edition=edition, numero=page_num,
        defaults={'contenu': [], 'layout': 'col2', 'couleur_fond': '#FFFEF7'}
    )
    medias = JournalMedia.objects.filter(edition=edition).order_by('-created_at')
    toutes_pages = edition.pages.order_by('numero')

    return render(request, 'eden/dashboard/journal_editeur.html', {
        'edition': edition,
        'page': page,
        'page_json': json.dumps(page.contenu, ensure_ascii=False),
        'medias': medias,
        'toutes_pages': toutes_pages,
        'total_pages': toutes_pages.count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_journal_page_ajouter(request, edition_pk):
    from .models import JournalEdition, JournalPage
    edition = get_object_or_404(JournalEdition, pk=edition_pk)
    dernier = edition.pages.aggregate(m=models.Max('numero'))['m'] or 0
    nouveau_num = dernier + 1
    JournalPage.objects.get_or_create(
        edition=edition, numero=nouveau_num,
        defaults={'contenu': [], 'layout': 'col2'}
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'page_num': nouveau_num})
    return redirect('dashboard_journal_page_editer',
                    edition_pk=edition_pk, page_num=nouveau_num)

@login_required
@user_passes_test(is_agent)
def dashboard_journal_page_supprimer(request, edition_pk, page_num):
    from .models import JournalEdition, JournalPage
    edition = get_object_or_404(JournalEdition, pk=edition_pk)
    page = get_object_or_404(JournalPage, edition=edition, numero=page_num)
    if request.method == 'POST':
        page.delete()
        # Renuméroter
        for i, p in enumerate(edition.pages.order_by('numero'), 1):
            if p.numero != i:
                p.numero = i
                p.save(update_fields=['numero'])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_journal_page_editer',
                        edition_pk=edition_pk, page_num=1)
    return JsonResponse({'success': False})



@login_required
@user_passes_test(is_agent)
def dashboard_journal_media_upload(request):
    """Upload image ou vidéo locale pour le journal."""
    from .models import JournalEdition, JournalMedia
    if request.method == 'POST':
        fichier = request.FILES.get('fichier')
        if not fichier:
            return JsonResponse({'success': False, 'error': 'Aucun fichier.'})

        edition_pk = request.POST.get('edition_pk')
        legende = request.POST.get('legende', '').strip()

        # Détecter le type
        nom = fichier.name.lower()
        if nom.endswith(('.mp4', '.webm', '.mov', '.avi', '.mkv')):
            type_media = 'video'
        else:
            type_media = 'image'

        media = JournalMedia(
            type=type_media,
            fichier=fichier,
            legende=legende,
        )
        if edition_pk:
            try:
                media.edition = JournalEdition.objects.get(pk=edition_pk)
            except JournalEdition.DoesNotExist:
                pass
        media.save()

        return JsonResponse({
            'success': True,
            'pk': media.pk,
            'url': media.fichier.url,
            'type': media.type,
            'legende': media.legende,
            'nom': fichier.name,
        })

    return JsonResponse({'success': False, 'error': 'POST requis.'})

@login_required
@user_passes_test(is_agent)
def dashboard_journal_media_liste(request):
    """Liste des médias pour l'éditeur."""
    from .models import JournalEdition, JournalMedia
    edition_pk = request.GET.get('edition_pk')
    qs = JournalMedia.objects.all().order_by('-created_at')
    if edition_pk:
        qs = qs.filter(
            Q(edition__pk=edition_pk) | Q(edition__isnull=True)
        )
    medias = []
    for m in qs[:60]:
        medias.append({
            'pk': m.pk,
            'type': m.type,
            'url': m.fichier.url if m.fichier else '',
            'legende': m.legende,
        })
    return JsonResponse({'medias': medias})


@login_required
@user_passes_test(is_agent)
def dashboard_journal_media_supprimer(request, pk):
    from .models import JournalMedia
    media = get_object_or_404(JournalMedia, pk=pk)
    if request.method == 'POST':
        if media.fichier:
            try:
                import os
                if os.path.exists(media.fichier.path):
                    os.remove(media.fichier.path)
            except Exception:
                pass
        media.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def api_journal_sauvegarder_page(request):
    """API AJAX — sauvegarde le contenu d'une page."""
    from .models import JournalPage
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST requis'})
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'})

    page_id = data.get('page_id')
    contenu = data.get('contenu', [])
    layout = data.get('layout', 'col2')
    couleur_fond = data.get('couleur_fond', '#FFFEF7')

    try:
        page = JournalPage.objects.get(pk=page_id)
    except JournalPage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Page introuvable'})

    page.contenu = contenu
    page.layout = layout
    page.couleur_fond = couleur_fond
    page.save(update_fields=['contenu', 'layout', 'couleur_fond'])

    return JsonResponse({
        'success': True,
        'page_id': page.pk,
        'nb_blocs': len(contenu),
    })

@login_required
@user_passes_test(is_agent)
def dashboard_site_stats_manuelles(request, pk):
    """Gestion des statistiques manuelles d'un site."""
    from .models import SiteStatistiquesManuelle
    site = get_object_or_404(SiteFoncier, pk=pk)
    stats, created = SiteStatistiquesManuelle.objects.get_or_create(site=site)

    if request.method == 'POST':
        try:
            stats.total_parcelles_manuel = int(request.POST.get('total_parcelles_manuel', 0))
            stats.vendues_manuel         = int(request.POST.get('vendues_manuel', 0))
            stats.disponibles_manuel     = int(request.POST.get('disponibles_manuel', 0))
            stats.reservees_manuel       = int(request.POST.get('reservees_manuel', 0))
            stats.indisponibles_manuel   = int(request.POST.get('indisponibles_manuel', 0))
            stats.notes                  = request.POST.get('notes', '')
            stats.updated_by             = request.user

            prix_min = request.POST.get('prix_min_manuel', '').strip()
            prix_max = request.POST.get('prix_max_manuel', '').strip()
            prix_moy = request.POST.get('prix_moyen_manuel', '').strip()
            sup_min  = request.POST.get('superficie_min', '').strip()
            sup_max  = request.POST.get('superficie_max', '').strip()

            stats.prix_min_manuel  = float(prix_min.replace(' ','').replace(',','')) if prix_min else None
            stats.prix_max_manuel  = float(prix_max.replace(' ','').replace(',','')) if prix_max else None
            stats.prix_moyen_manuel = float(prix_moy.replace(' ','').replace(',','')) if prix_moy else None
            stats.superficie_min   = float(sup_min) if sup_min else None
            stats.superficie_max   = float(sup_max) if sup_max else None

            # Mise à jour auto du site parent
            if stats.prix_min_manuel and not site.prix_min:
                site.prix_min = stats.prix_min_manuel
            if stats.prix_max_manuel and not site.prix_max:
                site.prix_max = stats.prix_max_manuel
            if stats.total_parcelles_manuel and not site.superficie_totale and stats.superficie_max:
                pass  # calcul optionnel
            site.save()
            stats.save()

            messages.success(request, f'Statistiques de "{site.nom}" mises à jour.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'total': site.nb_parcelles_total,
                    'vendues': site.nb_vendues,
                    'disponibles': site.nb_disponibles,
                    'pourcentage': site.pourcentage_vendu,
                })
            return redirect('dashboard_site_stats_manuelles', pk=pk)
        except Exception as e:
            messages.error(request, f'Erreur : {e}')

    # Stats réelles des parcelles créées
    stats_reelles = {
        'total': site.parcelles.filter(is_active=True).count(),
        'vendues': site.parcelles.filter(statut='vendue').count(),
        'disponibles': site.parcelles.filter(statut='disponible').count(),
        'reservees': site.parcelles.filter(statut='reservee').count(),
    }

    return render(request, 'eden/dashboard/site_stats_manuelles.html', {
        'site': site,
        'stats': stats,
        'stats_reelles': stats_reelles,
    })

# ══════════════════════════════════════════════
# HOME CONFIG DASHBOARD
# ══════════════════════════════════════════════



@login_required
@user_passes_test(is_agent)
def dashboard_home_config(request):
    """Vue d'ensemble de la configuration de la page d'accueil."""
    return render(request, 'eden/dashboard/home_config.html', {
        'hero': HeroConfig.get_config(),
        'nb_services': ServiceItem.objects.filter(is_active=True).count(),
        'nb_etapes': EtapeAcquisition.objects.filter(is_active=True).count(),
        'nb_actualites': ActualiteHome.objects.filter(is_active=True).count(),
        'nb_commentaires': CommentaireHome.objects.filter(is_active=True).count(),
        'nb_stats': StatistiqueHome.objects.filter(is_active=True).count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_hero_form(request):
    """Modifier le hero de la page d'accueil."""
    hero = HeroConfig.get_config()
    if request.method == 'POST':
        for field in ['eyebrow', 'titre_ligne1', 'titre_ligne2', 'description',
                      'badge_site_nom', 'badge_site_lieu', 'btn1_texte', 'btn2_texte']:
            val = request.POST.get(field, '').strip()
            if val:
                setattr(hero, field, val)
        if request.FILES.get('image_fond'):
            hero.image_fond = request.FILES['image_fond']
        hero.save()
        messages.success(request, 'Hero mis à jour avec succès !')
        return redirect('dashboard_hero_form')
    return render(request, 'eden/dashboard/hero_form.html', {'hero': hero})


@login_required
@user_passes_test(is_agent)
def dashboard_services(request):
    services = ServiceItem.objects.all().order_by('ordre')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            ServiceItem.objects.create(
                titre=request.POST.get('titre', 'Nouveau service'),
                description=request.POST.get('description', ''),
                icone=request.POST.get('icone', '🏡'),
                ordre=ServiceItem.objects.count(),
            )
            messages.success(request, 'Service ajouté.')
        elif action == 'supprimer':
            pk = request.POST.get('pk')
            ServiceItem.objects.filter(pk=pk).delete()
            messages.success(request, 'Service supprimé.')
        elif action == 'modifier':
            pk = request.POST.get('pk')
            s = get_object_or_404(ServiceItem, pk=pk)
            s.titre = request.POST.get('titre', s.titre)
            s.description = request.POST.get('description', s.description)
            s.icone = request.POST.get('icone', s.icone)
            s.ordre = int(request.POST.get('ordre', s.ordre))
            s.is_active = request.POST.get('is_active') == 'on'
            s.save()
            messages.success(request, 'Service modifié.')
        return redirect('dashboard_services')
    return render(request, 'eden/dashboard/services.html', {'services': services})


@login_required
@user_passes_test(is_agent)
def dashboard_etapes(request):
    from .models import EtapeAcquisition, HeroConfig
    etapes = EtapeAcquisition.objects.all().order_by('numero')

    if request.method == 'POST':
        action = request.POST.get('action')

        # Gestion de l'image technicien séparée
        if action == 'upload_technicien':
            if request.FILES.get('etapes_image'):
                hero = HeroConfig.get_config()
                hero.etapes_image = request.FILES['etapes_image']
                hero.save()
                messages.success(request, 'Image du technicien mise à jour.')
            return redirect('dashboard_etapes')

        if action == 'supprimer_technicien':
            hero = HeroConfig.get_config()
            if hero.etapes_image:
                hero.etapes_image.delete(save=True)
            messages.success(request, 'Image supprimée.')
            return redirect('dashboard_etapes')

        if action == 'ajouter':
            dernier = etapes.last()
            EtapeAcquisition.objects.create(
                numero=int(request.POST.get('numero', (dernier.numero + 1) if dernier else 1)),
                titre=request.POST.get('titre', 'Nouvelle étape'),
                description=request.POST.get('description', ''),
                couleur=request.POST.get('couleur', 'blue'),
            )
            messages.success(request, 'Étape ajoutée.')

        elif action == 'supprimer':
            pk = request.POST.get('pk')
            EtapeAcquisition.objects.filter(pk=pk).delete()
            messages.success(request, 'Étape supprimée.')

        elif action == 'modifier':
            pk = request.POST.get('pk')
            e = get_object_or_404(EtapeAcquisition, pk=pk)
            e.titre = request.POST.get('titre', e.titre)
            e.description = request.POST.get('description', e.description)
            e.numero = int(request.POST.get('numero', e.numero))
            e.couleur = request.POST.get('couleur', e.couleur)
            e.is_active = request.POST.get('is_active') == 'on'
            e.save()
            messages.success(request, 'Étape modifiée.')

        return redirect('dashboard_etapes')

    hero = HeroConfig.get_config()
    return render(request, 'eden/dashboard/etapes.html', {
        'etapes': etapes,
        'hero': hero,
    })

@login_required
@user_passes_test(is_agent)
def dashboard_livret_form(request):
    livret, _ = SectionLivret.objects.get_or_create(pk=1)
    if request.method == 'POST':
        for field in ['titre_principal', 'sous_titre', 'badge_texte', 'btn_texte', 'btn_lien']:
            val = request.POST.get(field, '').strip()
            if val:
                setattr(livret, field, val)
        livret.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('image'):
            livret.image = request.FILES['image']
        livret.save()
        # Avantages
        avantages = request.POST.getlist('avantage')
        livret.avantages.all().delete()
        for i, a in enumerate(avantages):
            if a.strip():
                from .models import AvantagesLivret
                AvantagesLivret.objects.create(livret=livret, texte=a.strip(), ordre=i)
        messages.success(request, 'Section Livret mise à jour.')
        return redirect('dashboard_livret_form')
    avantages = list(livret.avantages.values_list('texte', flat=True))
    return render(request, 'eden/dashboard/livret_form.html', {
        'livret': livret, 'avantages': avantages
    })


@login_required
@user_passes_test(is_agent)
def dashboard_actualites(request):
    actualites = ActualiteHome.objects.all().order_by('-date_evenement')
    return render(request, 'eden/dashboard/actualites.html', {'actualites': actualites})


@login_required
@user_passes_test(is_agent)
def dashboard_actualite_form(request, pk=None):
    obj = get_object_or_404(ActualiteHome, pk=pk) if pk else None
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
        else:
            if not obj:
                obj = ActualiteHome()
            obj.titre = titre
            obj.description = request.POST.get('description', '').strip()
            obj.lien = request.POST.get('lien', '#').strip()
            obj.ordre = int(request.POST.get('ordre', 0))
            obj.is_active = request.POST.get('is_active') == 'on'
            date_str = request.POST.get('date_evenement', '')
            if date_str:
                from datetime import date
                try:
                    obj.date_evenement = date.fromisoformat(date_str)
                except Exception:
                    pass
            if request.FILES.get('image'):
                obj.image = request.FILES['image']
            obj.save()
            messages.success(request, 'Actualité enregistrée.')
            return redirect('dashboard_actualites')
    return render(request, 'eden/dashboard/actualite_form.html', {'obj': obj})


@login_required
@user_passes_test(is_agent)
def dashboard_actualite_supprimer(request, pk):
    obj = get_object_or_404(ActualiteHome, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Actualité supprimée.')
        return redirect('dashboard_actualites')
    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': obj, 'retour': 'dashboard_actualites'
    })


@login_required
@user_passes_test(is_agent)
def dashboard_commentaires(request):
    commentaires = CommentaireHome.objects.all().order_by('ordre')
    return render(request, 'eden/dashboard/commentaires.html', {'commentaires': commentaires})


@login_required
@user_passes_test(is_agent)
def dashboard_commentaire_form(request, pk=None):
    obj = get_object_or_404(CommentaireHome, pk=pk) if pk else None
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        texte = request.POST.get('texte', '').strip()
        if not nom or not texte:
            messages.error(request, 'Nom et commentaire obligatoires.')
        else:
            if not obj:
                obj = CommentaireHome()
            obj.nom = nom
            obj.role = request.POST.get('role', '').strip()
            obj.texte = texte
            obj.note = int(request.POST.get('note', 5))
            obj.ordre = int(request.POST.get('ordre', 0))
            obj.is_active = request.POST.get('is_active') == 'on'
            if request.FILES.get('avatar'):
                obj.avatar = request.FILES['avatar']
            obj.save()
            messages.success(request, 'Commentaire enregistré.')
            return redirect('dashboard_commentaires')
    return render(request, 'eden/dashboard/commentaire_form.html', {'obj': obj})


@login_required
@user_passes_test(is_agent)
def dashboard_commentaire_supprimer(request, pk):
    obj = get_object_or_404(CommentaireHome, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Commentaire supprimé.')
        return redirect('dashboard_commentaires')
    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': obj, 'retour': 'dashboard_commentaires'
    })


@login_required
@user_passes_test(is_agent)
def dashboard_stats_home(request):
    stats = StatistiqueHome.objects.all().order_by('ordre')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            StatistiqueHome.objects.create(
                valeur=request.POST.get('valeur', '0'),
                label=request.POST.get('label', ''),
                icone=request.POST.get('icone', '📊'),
                ordre=StatistiqueHome.objects.count(),
            )
            messages.success(request, 'Statistique ajoutée.')
        elif action == 'supprimer':
            StatistiqueHome.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'Statistique supprimée.')
        elif action == 'modifier':
            pk = request.POST.get('pk')
            s = get_object_or_404(StatistiqueHome, pk=pk)
            s.valeur = request.POST.get('valeur', s.valeur)
            s.label = request.POST.get('label', s.label)
            s.icone = request.POST.get('icone', s.icone)
            s.ordre = int(request.POST.get('ordre', s.ordre))
            s.is_active = request.POST.get('is_active') == 'on'
            s.save()
            messages.success(request, 'Statistique modifiée.')
        return redirect('dashboard_stats_home')
    return render(request, 'eden/dashboard/stats_home.html', {'stats': stats})

@login_required
@user_passes_test(is_agent)
def dashboard_hero_slides(request):
    from .models import HeroSlide
    slides = HeroSlide.objects.all().order_by('ordre')
    if request.method == 'POST':
        if request.FILES.get('image'):
            HeroSlide.objects.create(
                image=request.FILES['image'],
                titre=request.POST.get('titre', '').strip(),
                sous_titre=request.POST.get('sous_titre', '').strip(),
                ordre=HeroSlide.objects.count(),
                is_active=True,
            )
            messages.success(request, 'Slide ajoutée.')
        return redirect('dashboard_hero_slides')
    return render(request, 'eden/dashboard/hero_slides.html', {'slides': slides})


@login_required
@user_passes_test(is_agent)
def dashboard_hero_slide_supprimer(request, pk):
    from .models import HeroSlide
    slide = get_object_or_404(HeroSlide, pk=pk)
    if request.method == 'POST':
        slide.delete()
        messages.success(request, 'Slide supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    return redirect('dashboard_hero_slides')


@login_required
@user_passes_test(is_agent)
def dashboard_hero_slide_toggle(request, pk):
    from .models import HeroSlide
    if request.method == 'POST':
        slide = get_object_or_404(HeroSlide, pk=pk)
        slide.is_active = not slide.is_active
        slide.save()
        return JsonResponse({'success': True, 'is_active': slide.is_active})
    return JsonResponse({'success': False})

@login_required
@user_passes_test(is_agent)
def dashboard_journal_page_supprimer(request, edition_pk, page_num):
    from .models import JournalEdition, JournalPage
    edition = get_object_or_404(JournalEdition, pk=edition_pk)
    page = get_object_or_404(JournalPage, edition=edition, numero=page_num)
    if request.method == 'POST':
        page.delete()
        # Renuméroter les pages restantes
        for i, p in enumerate(edition.pages.order_by('numero'), 1):
            if p.numero != i:
                p.numero = i
                p.save(update_fields=['numero'])
        messages.success(request, f'Page {page_num} supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'total': edition.pages.count()})
        return redirect('dashboard_journal')
    return JsonResponse({'success': False}, status=405)


# ══════════════════════════════════════════════
# MODULE UNE & ÉVÉNEMENTS
# ══════════════════════════════════════════════


def une_evenements_accueil(request):
    """Page d'accueil du module Une & Événements."""
    a_la_une = UneEvenement.objects.filter(
        categorie='une', statut='publie'
    ).order_by('ordre', '-created_at').first()

    evenements_avenir = UneEvenement.objects.filter(
        categorie='evenement_avenir', statut='publie'
    ).order_by('date_evenement')[:12]

    evenements_passes = UneEvenement.objects.filter(
        categorie='evenement_passe', statut='publie'
    ).order_by('-date_evenement')[:12]

    actualites = UneEvenement.objects.filter(
        categorie='actualite', statut='publie'
    ).order_by('-date_evenement', '-created_at')[:4]

    return render(request, 'eden/une_evenements/accueil.html', {
        'a_la_une': a_la_une,
        'evenements_avenir': evenements_avenir,
        'evenements_passes': evenements_passes,
        'actualites': actualites,
    })


def une_evenement_detail(request, pk):
    """Lecture d'un article."""
    article = get_object_or_404(UneEvenement, pk=pk, statut='publie')
    return render(request, 'eden/une_evenements/detail.html', {
        'article': article,
        'contenu_json': json.dumps(article.contenu),
    })


def une_evenements_liste(request, cat):
    """Liste d'une catégorie complète."""
    labels = {
        'une': 'À la Une',
        'evenement_avenir': 'Événements à venir',
        'evenement_passe': 'Événements passés',
        'actualite': 'Actualités',
    }
    articles = UneEvenement.objects.filter(
        categorie=cat, statut='publie'
    ).order_by('-date_evenement', '-created_at')
    return render(request, 'eden/une_evenements/liste.html', {
        'articles': articles,
        'categorie': cat,
        'categorie_label': labels.get(cat, cat),
    })


# ── Dashboard ──

@login_required
@user_passes_test(is_agent)
def dashboard_une_liste(request):
    from .models import UneEvenement
    articles = UneEvenement.objects.all().order_by('-created_at')
    cat_f = request.GET.get('cat', '')
    q = request.GET.get('q', '')
    if cat_f:
        articles = articles.filter(categorie=cat_f)
    if q:
        articles = articles.filter(Q(titre__icontains=q))
    paginator = Paginator(articles, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'eden/dashboard/une_liste.html', {
        'articles': page,
        'cat_f': cat_f, 'q': q,
        'total': UneEvenement.objects.count(),
        'nb_une': UneEvenement.objects.filter(categorie='une').count(),
        'nb_avenir': UneEvenement.objects.filter(categorie='evenement_avenir').count(),
        'nb_passe': UneEvenement.objects.filter(categorie='evenement_passe').count(),
        'nb_actu': UneEvenement.objects.filter(categorie='actualite').count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_une_form(request, pk=None):
    from .models import UneEvenement
    article = get_object_or_404(UneEvenement, pk=pk) if pk else None
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/une_form.html', {'article': article})
        if not article:
            article = UneEvenement()
        article.titre = titre
        article.sous_titre = request.POST.get('sous_titre', '').strip()
        article.categorie = request.POST.get('categorie', 'actualite')
        article.lieu = request.POST.get('lieu', '').strip()
        article.statut = request.POST.get('statut', 'brouillon')
        article.ordre = int(request.POST.get('ordre', 0))
        article.created_by = request.user
        date_str = request.POST.get('date_evenement', '')
        date_fin_str = request.POST.get('date_fin_evenement', '')
        if date_str:
            from datetime import date
            try:
                article.date_evenement = date.fromisoformat(date_str)
            except Exception:
                pass
        else:
            article.date_evenement = None
        if date_fin_str:
            from datetime import date
            try:
                article.date_fin_evenement = date.fromisoformat(date_fin_str)
            except Exception:
                pass
        else:
            article.date_fin_evenement = None
        if request.FILES.get('image_couverture'):
            article.image_couverture = request.FILES['image_couverture']
        article.save()
        messages.success(request, f'Article "{article.titre}" enregistré.')
        if request.POST.get('action') == 'editeur':
            return redirect('dashboard_une_editeur', pk=article.pk)
        return redirect('dashboard_une_liste')
    return render(request, 'eden/dashboard/une_form.html', {'article': article})


@login_required
@user_passes_test(is_agent)
def dashboard_une_supprimer(request, pk):
    from .models import UneEvenement
    article = get_object_or_404(UneEvenement, pk=pk)
    if request.method == 'POST':
        titre = article.titre
        article.delete()
        messages.success(request, f'"{titre}" supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_une_liste')
    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': article, 'retour': 'dashboard_une_liste'
    })


@login_required
@user_passes_test(is_agent)
def dashboard_une_publier(request, pk):
    from .models import UneEvenement
    article = get_object_or_404(UneEvenement, pk=pk)
    if request.method == 'POST':
        if article.statut == 'publie':
            article.statut = 'brouillon'
        else:
            article.statut = 'publie'
        article.save()
        return JsonResponse({'success': True, 'statut': article.statut})
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_agent)
def dashboard_une_editeur(request, pk):
    from .models import UneEvenement
    article = get_object_or_404(UneEvenement, pk=pk)
    return render(request, 'eden/dashboard/une_editeur.html', {
        'article': article,
        'contenu_json': json.dumps(article.contenu),
    })


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_une_sauvegarder(request):
    from .models import UneEvenement
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pk = data.get('pk')
            article = get_object_or_404(UneEvenement, pk=pk)
            article.contenu = data.get('contenu', [])
            article.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_agent)
def dashboard_une_media_upload(request):
    if request.method == 'POST' and request.FILES.get('fichier'):
        f = request.FILES['fichier']
        import os
        from django.core.files.storage import default_storage
        path = default_storage.save(f'une_evenements/medias/{f.name}', f)
        url = request.build_absolute_uri(default_storage.url(path))
        t = 'image' if f.content_type.startswith('image') else 'video'
        return JsonResponse({'success': True, 'url': url, 'type': t})
    return JsonResponse({'success': False})

# ══════════════════════════════════════════════
# MODULE NOS PROJETS
# ══════════════════════════════════════════════

def nos_projets(request):
    """Page principale Nos Projets."""
    from .models import Projet, ProjetImage, ProjetInfrastructure, EtapeProjet, SousEtapeProjet

    filtre = request.GET.get('filtre', '')

    # Tous les projets actifs
    tous_actifs = Projet.objects.filter(is_active=True)

    # Projets filtrés pour l'affichage de la grille
    if filtre and filtre in ['en_cours', 'livre', 'futur']:
        projets = tous_actifs.filter(statut=filtre).order_by('ordre', '-created_at')
    else:
        # Par défaut : afficher EN COURS uniquement
        projets = tous_actifs.filter(statut='en_cours').order_by('ordre', '-created_at')
        filtre = 'en_cours'  # forcer pour que le filtre actif soit bien affiché

    # Stats globales (toujours sur tous les projets)
    stats = {
        'en_cours': tous_actifs.filter(statut='en_cours').count(),
        'livres': tous_actifs.filter(statut='livre').count(),
        'futurs': tous_actifs.filter(statut='futur').count(),
        'proprietaires': sum(p.nb_proprietaires for p in tous_actifs),
    }

    # Projet vedette (détail à afficher)
    projet_vedette = None
    slug_detail = request.GET.get('projet', '')
    if slug_detail:
        projet_vedette = Projet.objects.filter(
            slug=slug_detail, is_active=True
        ).prefetch_related(
            'galerie', 'etapes__sous_etapes', 'infrastructures'
        ).first()

    return render(request, 'eden/nos_projets.html', {
        'projets': projets,
        'projet_vedette': projet_vedette,
        'stats': stats,
        'filtre': filtre,
        'tous_projets': tous_actifs.order_by('ordre', '-created_at'),
    })


def projet_detail(request, slug):
    """Page détail d'un projet (redirection vers nos_projets avec param)."""
    from django.shortcuts import redirect
    return redirect(f"{request.build_absolute_uri('/projets/')}?projet={slug}")


def api_projet_etapes(request, slug):
    projet = get_object_or_404(Projet, slug=slug, is_active=True)
    data = []
    for etape in projet.etapes.all().prefetch_related('sous_etapes'):
        data.append({
            'id': etape.pk,
            'nom': etape.nom,
            'description': etape.description,   # ← AJOUTEZ
            'icone': etape.icone,
            'couleur': etape.couleur,
            'progression': etape.progression_globale,
            'sous_etapes': [
                {'nom': s.nom, 'avancement': s.avancement}
                for s in etape.sous_etapes.all()
            ]
        })
    return JsonResponse({'etapes': data})


# ── Dashboard Projets ──

@login_required
@user_passes_test(is_agent)
def dashboard_projets_liste(request):
    projets = Projet.objects.all().order_by('ordre', '-created_at')
    return render(request, 'eden/dashboard/projets_liste.html', {
        'projets': projets,
        'nb_en_cours': Projet.objects.filter(statut='en_cours').count(),
        'nb_livres': Projet.objects.filter(statut='livre').count(),
        'nb_futurs': Projet.objects.filter(statut='futur').count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_projet_form(request, pk=None):
    projet = get_object_or_404(Projet, pk=pk) if pk else None
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        if not nom:
            messages.error(request, 'Le nom est obligatoire.')
            return render(request, 'eden/dashboard/projet_form.html', {'projet': projet})
        if not projet:
            projet = Projet()
        projet.nom = nom
        projet.statut = request.POST.get('statut', 'en_cours')
        projet.type_projet = request.POST.get('type_projet', 'lotissement')
        projet.localisation = request.POST.get('localisation', '').strip()
        projet.description = request.POST.get('description', '').strip()
        projet.description_courte = request.POST.get('description_courte', '').strip()
        projet.superficie_totale = request.POST.get('superficie_totale', '').strip()
        projet.nb_lots = int(request.POST.get('nb_lots', 0) or 0)
        projet.surface_lots = request.POST.get('surface_lots', '').strip()
        projet.lots_disponibles = int(request.POST.get('lots_disponibles', 0) or 0)
        projet.lots_reserves = int(request.POST.get('lots_reserves', 0) or 0)
        projet.lots_vendus = int(request.POST.get('lots_vendus', 0) or 0)
        projet.nb_proprietaires = int(request.POST.get('nb_proprietaires', 0) or 0)
        projet.annee_livraison = request.POST.get('annee_livraison', '').strip()
        projet.ordre = int(request.POST.get('ordre', 0) or 0)
        projet.is_active = request.POST.get('is_active') == 'on'
        prix = request.POST.get('prix_min', '').strip()
        if prix:
            try:
                projet.prix_min = float(prix.replace(' ', '').replace(',', ''))
            except Exception:
                pass
        for field in ['brochure', 'plan_cadastral', 'grille_tarifaire', 'dossier_technique']:
            if request.FILES.get(field):
                setattr(projet, field, request.FILES[field])
        if request.FILES.get('image_principale'):
            projet.image_principale = request.FILES['image_principale']
        projet.save()
        messages.success(request, f'Projet "{projet.nom}" enregistré.')
        return redirect('dashboard_projets_liste')
    return render(request, 'eden/dashboard/projet_form.html', {'projet': projet})


@login_required
@user_passes_test(is_agent)
def dashboard_projet_supprimer(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    if request.method == 'POST':
        nom = projet.nom
        projet.delete()
        messages.success(request, f'Projet "{nom}" supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_projets_liste')
    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': projet, 'retour': 'dashboard_projets_liste'
    })


@login_required
@user_passes_test(is_agent)
def dashboard_projet_etapes(request, pk):
    """Gestion des étapes et sous-étapes d'un projet."""
    projet = get_object_or_404(Projet, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'ajouter_etape':
            EtapeProjet.objects.create(
                projet=projet,
                nom=request.POST.get('nom', 'Nouvelle étape'),
                description=request.POST.get('description', ''),
                icone=request.POST.get('icone', '🔵'),
                couleur=request.POST.get('couleur', '#1B4FDB'),
                ordre=projet.etapes.count(),
            )
            messages.success(request, 'Étape ajoutée.')

        elif action == 'modifier_etape':
            etape = get_object_or_404(EtapeProjet, pk=request.POST.get('etape_pk'), projet=projet)
            etape.nom = request.POST.get('nom', etape.nom)
            etape.description = request.POST.get('description', etape.description)
            etape.icone = request.POST.get('icone', etape.icone)
            etape.couleur = request.POST.get('couleur', etape.couleur)
            etape.ordre = int(request.POST.get('ordre', etape.ordre))
            etape.save()
            messages.success(request, 'Étape modifiée.')

        elif action == 'supprimer_etape':
            EtapeProjet.objects.filter(pk=request.POST.get('etape_pk'), projet=projet).delete()
            messages.success(request, 'Étape supprimée.')

        elif action == 'ajouter_sous_etape':
            etape = get_object_or_404(EtapeProjet, pk=request.POST.get('etape_pk'), projet=projet)
            SousEtapeProjet.objects.create(
                etape=etape,
                nom=request.POST.get('nom', 'Nouvelle sous-étape'),
                avancement=int(request.POST.get('avancement', 0)),
                ordre=etape.sous_etapes.count(),
            )
            messages.success(request, 'Sous-étape ajoutée.')

        elif action == 'modifier_sous_etape':
            sous = get_object_or_404(SousEtapeProjet, pk=request.POST.get('sous_pk'))
            sous.nom = request.POST.get('nom', sous.nom)
            sous.avancement = int(request.POST.get('avancement', sous.avancement))
            sous.ordre = int(request.POST.get('ordre', sous.ordre))
            sous.save()
            messages.success(request, 'Sous-étape modifiée.')

        elif action == 'supprimer_sous_etape':
            SousEtapeProjet.objects.filter(pk=request.POST.get('sous_pk')).delete()
            messages.success(request, 'Sous-étape supprimée.')

        return redirect('dashboard_projet_etapes', pk=pk)

    etapes = projet.etapes.all().prefetch_related('sous_etapes')
    return render(request, 'eden/dashboard/projet_etapes.html', {
        'projet': projet, 'etapes': etapes
    })


@login_required
@user_passes_test(is_agent)
def dashboard_projet_galerie(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    if request.method == 'POST' and request.FILES.getlist('images'):
        ordre_start = projet.galerie.count()
        for i, img in enumerate(request.FILES.getlist('images')):
            ProjetImage.objects.create(
                projet=projet,
                image=img,
                legende=request.POST.get(f'legende_{i}', ''),
                ordre=ordre_start + i,
            )
        messages.success(request, f'{len(request.FILES.getlist("images"))} image(s) ajoutée(s).')
        return redirect('dashboard_projet_galerie', pk=pk)
    return render(request, 'eden/dashboard/projet_galerie.html', {
        'projet': projet,
        'images': projet.galerie.order_by('ordre'),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_projet_image_supprimer(request, pk, img_pk):
    projet = get_object_or_404(Projet, pk=pk)
    img = get_object_or_404(ProjetImage, pk=img_pk, projet=projet)
    if request.method == 'POST':
        img.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'Image supprimée.')
    return redirect('dashboard_projet_galerie', pk=pk)


@login_required
@user_passes_test(is_agent)
def dashboard_projet_infrastructures(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            ProjetInfrastructure.objects.create(
                projet=projet,
                nom=request.POST.get('nom', '').strip(),
                is_realise=request.POST.get('is_realise') == 'on',
                ordre=projet.infrastructures.count(),
            )
            messages.success(request, 'Infrastructure ajoutée.')
        elif action == 'modifier':
            infra = get_object_or_404(ProjetInfrastructure, pk=request.POST.get('infra_pk'), projet=projet)
            infra.nom = request.POST.get('nom', infra.nom)
            infra.is_realise = request.POST.get('is_realise') == 'on'
            infra.ordre = int(request.POST.get('ordre', infra.ordre))
            infra.save()
            messages.success(request, 'Infrastructure modifiée.')
        elif action == 'supprimer':
            ProjetInfrastructure.objects.filter(pk=request.POST.get('infra_pk'), projet=projet).delete()
            messages.success(request, 'Infrastructure supprimée.')
        return redirect('dashboard_projet_infrastructures', pk=pk)
    return render(request, 'eden/dashboard/projet_infrastructures.html', {
        'projet': projet,
        'infrastructures': projet.infrastructures.order_by('ordre'),
    })

# ══════════════════════════════════════════════
# MODULE NOS AGENCES
# ══════════════════════════════════════════════


def nos_agences(request):
    agences = Agence.objects.filter(is_active=True).prefetch_related('services').order_by('ordre')
    
    # Récupérer le siège
    siege = agences.filter(type_agence='siege').first()
    
    # Créer la liste des agences pour le carrousel (siège en premier)
    agences_list = []
    if siege:
        agences_list.append(siege)
    # Ajouter les autres agences (hors siège)
    agences_list.extend(agences.filter(type_agence__in=['agence', 'bureau']).order_by('ordre'))
    
    # Créer des slides de 3 agences avec décalage pour carrousel circulaire
    agences_slides = []
    n = len(agences_list)
    if n > 0:
        # Créer des slides avec décalage : 0,1,2 puis 1,2,3 puis 2,3,4 ...
        for i in range(n):
            slide = []
            for j in range(3):
                idx = (i + j) % n
                slide.append(agences_list[idx])
            agences_slides.append(slide)
    else:
        agences_slides = [[]]
    
    # Image fixe pour la colonne 2 (URL directe)
    stats_image_url = "/static/images/cameroun.png" # À personnaliser
    
    # Stats
    stats = StatAgence.objects.filter(is_active=True).order_by('ordre')
    stats_defaults = [
        {'valeur': str(agences.filter(type_agence__in=['siege','agence']).count()), 'label': 'Agences principales', 'icone': '🏢'},
        {'valeur': str(agences.filter(type_agence='bureau').count()) + '+', 'label': 'Bureaux relais', 'icone': '🏪'},
        {'valeur': '50+', 'label': 'Collaborateurs à votre service', 'icone': '👥'},
        {'valeur': '20+', 'label': "Ans d'expérience", 'icone': '🏆'},
    ]

    return render(request, 'eden/nos_agences.html', {
        'agences': agences,
        'agences_slides': agences_slides,
        'siege': siege,
        'stats_image_url': stats_image_url,  # URL de l'image fixe
        'stats': stats if stats.exists() else stats_defaults,
        'stats_are_objects': stats.exists(),
    })



@login_required
@user_passes_test(is_agent)
def dashboard_agences_liste(request):
    agences = Agence.objects.all().order_by('ordre')
    return render(request, 'eden/dashboard/agences_liste.html', {
        'agences': agences,
        'nb_siege': agences.filter(type_agence='siege').count(),
        'nb_agence': agences.filter(type_agence='agence').count(),
        'nb_bureau': agences.filter(type_agence='bureau').count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_agence_form(request, pk=None):
    agence = get_object_or_404(Agence, pk=pk) if pk else None
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        if not nom:
            messages.error(request, 'Le nom est obligatoire.')
            return render(request, 'eden/dashboard/agence_form.html', {'agence': agence})
        if not agence:
            agence = Agence()
        agence.nom = nom
        agence.type_agence = request.POST.get('type_agence', 'agence')
        agence.ville = request.POST.get('ville', '').strip()
        agence.adresse = request.POST.get('adresse', '').strip()
        agence.telephone = request.POST.get('telephone', '').strip()
        agence.whatsapp = request.POST.get('whatsapp', '').strip()
        agence.email = request.POST.get('email', '').strip()
        agence.horaires = request.POST.get('horaires', '').strip()
        agence.description = request.POST.get('description', '').strip()
        agence.lien_itineraire = request.POST.get('lien_itineraire', '').strip()
        agence.ordre = int(request.POST.get('ordre', 0) or 0)
        agence.is_active = request.POST.get('is_active') == 'on'
        lat = request.POST.get('latitude', '').strip()
        lng = request.POST.get('longitude', '').strip()
        if lat:
            try:
                agence.latitude = float(lat)
            except Exception:
                pass
        if lng:
            try:
                agence.longitude = float(lng)
            except Exception:
                pass
        if request.FILES.get('image'):
            agence.image = request.FILES['image']
        agence.save()

        # Services
        agence.services.all().delete()
        services = request.POST.getlist('service')
        for i, s in enumerate(services):
            if s.strip():
                AgenceService.objects.create(agence=agence, nom=s.strip(), ordre=i)

        messages.success(request, f'Agence "{agence.nom}" enregistrée.')
        return redirect('dashboard_agences_liste')
    services = list(agence.services.values_list('nom', flat=True)) if agence else []
    return render(request, 'eden/dashboard/agence_form.html', {
        'agence': agence,
        'services': services,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_agence_supprimer(request, pk):
    agence = get_object_or_404(Agence, pk=pk)
    if request.method == 'POST':
        nom = agence.nom
        agence.delete()
        messages.success(request, f'Agence "{nom}" supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_agences_liste')
    return redirect('dashboard_agences_liste')


@login_required
@user_passes_test(is_agent)
def dashboard_agences_stats(request):
    stats = StatAgence.objects.all().order_by('ordre')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            StatAgence.objects.create(
                valeur=request.POST.get('valeur', '0'),
                label=request.POST.get('label', ''),
                icone=request.POST.get('icone', '🏢'),
                ordre=StatAgence.objects.count(),
            )
            messages.success(request, 'Statistique ajoutée.')
        elif action == 'supprimer':
            StatAgence.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'Statistique supprimée.')
        elif action == 'modifier':
            s = get_object_or_404(StatAgence, pk=request.POST.get('pk'))
            s.valeur = request.POST.get('valeur', s.valeur)
            s.label = request.POST.get('label', s.label)
            s.icone = request.POST.get('icone', s.icone)
            s.ordre = int(request.POST.get('ordre', s.ordre))
            s.is_active = request.POST.get('is_active') == 'on'
            s.save()
            messages.success(request, 'Statistique modifiée.')
        return redirect('dashboard_agences_stats')
    return render(request, 'eden/dashboard/agences_stats.html', {'stats': stats})

# ══════════════════════════════════════════════
# MODULE NOS SERVICES
# ══════════════════════════════════════════════

import json

def escape_js(text):
    """Échappe une chaîne pour l'utiliser dans du JavaScript."""
    if not text:
        return ''
    return json.dumps(text)[1:-1]




def nos_services(request):
    """Page des services avec affichage dynamique"""
    
    all_services = Service.objects.filter(is_active=True).order_by('ordre', 'numero')
    
    # ═══ Vérifier si c'est une requête AJAX ═══
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        service_id = request.GET.get('service', '')
        
        if service_id and service_id != 'tous':
            try:
                service = all_services.filter(id=service_id).first()
            except (ValueError, TypeError):
                service = None
            
            if service:
                description_longue = service.description_longue or service.description or ''
                lien_detail = service.lien_detail if service.lien_detail and service.lien_detail != '#' else '#'
                
                html = f'''
                <div style="padding:0;">
                    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
                        <div style="width:64px;height:64px;border-radius:16px;background:var(--blue-pale);display:flex;align-items:center;justify-content:center;font-size:2rem;">{service.icone}</div>
                        <div>
                            <div style="font-size:0.7rem;font-weight:700;color:var(--g400);letter-spacing:1px;text-transform:uppercase;">SERVICE 0{service.numero}</div>
                            <div style="font-size:1.5rem;font-weight:900;color:var(--g800);">{service.nom}</div>
                        </div>
                    </div>
                    <div style="font-size:0.9rem;color:var(--g600);line-height:1.8;margin-bottom:1.5rem;">{description_longue}</div>
                    <div style="display:flex;gap:0.8rem;flex-wrap:wrap;">
                        <button class="btn-modal-primary" onclick="showToast('📅','Notre équipe vous contactera sous 24h.')" style="background:var(--red);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;font-family:'Outfit',sans-serif;">📅 Demander ce service</button>
                        <a href="{lien_detail}" class="btn-modal-secondary" style="padding:12px 24px;background:var(--g50);border:1.5px solid var(--g200);border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Outfit',sans-serif;color:var(--g600);text-decoration:none;display:inline-flex;align-items:center;gap:6px;">En savoir plus →</a>
                    </div>
                </div>
                '''
                return JsonResponse({'html': html, 'type': 'detail'})
            else:
                html = '''
                <div style="text-align:center;padding:4rem;color:var(--g400);">
                    <div style="font-size:3rem;margin-bottom:0.8rem;">🔍</div>
                    <div style="font-size:15px;font-weight:600;color:var(--g800);margin-bottom:0.4rem;">Service non trouvé</div>
                </div>
                '''
                return JsonResponse({'html': html, 'type': 'empty'})
        
        # ═══ Grille de tous les services ═══
        html_cartes = ''
        for srv in all_services:
            # ═══ Utiliser json.dumps pour échapper correctement ═══
            nom_esc = json.dumps(srv.nom)
            desc_esc = json.dumps(srv.description or '')
            ico_esc = json.dumps(srv.icone or '')
            description = truncate_text(srv.description, 120)
            lien_detail = srv.lien_detail if srv.lien_detail and srv.lien_detail != '#' else '#'
            
            # ═══ Utiliser des guillemets simples pour l'attribut onclick ═══
            html_cartes += f'''
            <div class="service-card" onclick='ouvrirDetailService({nom_esc},{desc_esc},{ico_esc},{srv.numero})'>
                <div class="sc-num">0{srv.numero}</div>
                <div class="sc-ico-box">{srv.icone}</div>
                <div class="sc-nom">{srv.nom}</div>
                <div class="sc-desc">{description}</div>
                <a class="sc-lire" href="{lien_detail}" onclick="event.stopPropagation();">En savoir plus →</a>
            </div>
            '''
        
        if not html_cartes:
            html_cartes = '''
            <div style="grid-column:1/-1;text-align:center;padding:4rem;color:var(--g400);">
                <div style="font-size:3rem;margin-bottom:0.8rem;">🔍</div>
                <div style="font-size:15px;font-weight:600;color:var(--g800);margin-bottom:0.4rem;">Aucun service</div>
                <div style="font-size:13px;">Aucun service disponible pour le moment.</div>
            </div>
            '''
        
        return JsonResponse({'html': html_cartes, 'type': 'grid'})
    
    # ═══ Requête normale (page complète) ═══
    services_carousel = Service.objects.filter(
        is_active=True,
        image__isnull=False
    ).exclude(image='').order_by('ordre', 'numero')[:10]
    
    if not services_carousel:
        class PlaceholderService:
            def __init__(self):
                self.nom = "EDEN GROUP"
                self.image = None
        services_carousel = [PlaceholderService()]

    etapes = EtapeProcessus.objects.filter(is_active=True).order_by('ordre', 'numero')
    engagements = EngagementService.objects.filter(is_active=True).order_by('ordre')

    engagements_defaults = [
        {'icone': '🔒', 'titre': 'Sécurité garantie', 'description': 'Tous nos terrains sont sécurisés avec titres fonciers authentiques.', 'couleur': 'blue'},
        {'icone': '👤', 'titre': 'Accompagnement personnalisé', 'description': 'Un conseiller dédié pour un suivi rigoureux de votre projet.', 'couleur': 'red'},
        {'icone': '📊', 'titre': 'Transparence totale', 'description': 'Des informations claires et des procédures transparentes.', 'couleur': 'green'},
        {'icone': '⭐', 'titre': 'Qualité & Professionnalisme', 'description': 'Une équipe d\'experts à votre service.', 'couleur': 'purple'},
    ]

    context = {
        'services': all_services,
        'services_carousel': services_carousel,
        'etapes': etapes,
        'engagements': engagements if engagements.exists() else engagements_defaults,
        'engagements_are_objects': engagements.exists(),
    }
    
    return render(request, 'eden/nos_services.html', context)


def truncate_text(text, length=120):
    """Tronque un texte à une longueur donnée."""
    if not text:
        return ''
    if len(text) > length:
        return text[:length] + '...'
    return text

def service_detail(request, slug):
    cat = get_object_or_404(ServiceCategorie, slug=slug, is_active=True)
    services = cat.services.filter(is_active=True).order_by('ordre', 'numero')
    return render(request, 'eden/nos_services.html', {
        'categories': ServiceCategorie.objects.filter(is_active=True).order_by('ordre'),
        'services': services,
        'etapes': EtapeProcessus.objects.filter(is_active=True).order_by('ordre'),
        'engagements': EngagementService.objects.filter(is_active=True).order_by('ordre'),
        'engagements_are_objects': True,
        'cat_actif': slug,
    })


# ── Dashboard ──

@login_required
@user_passes_test(is_agent)
def dashboard_services_liste(request):
    services = Service.objects.all().order_by('ordre', 'numero')
    return render(request, 'eden/dashboard/services_liste.html', {
        'services': services,
        'nb_actifs': services.filter(is_active=True).count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_service_form(request, pk=None):
    service = get_object_or_404(Service, pk=pk) if pk else None
    categories = ServiceCategorie.objects.filter(is_active=True).order_by('ordre')
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        if not nom:
            messages.error(request, 'Le nom est obligatoire.')
            return render(request, 'eden/dashboard/service_form.html', {
                'service': service, 'categories': categories
            })
        if not service:
            service = Service()
        service.nom = nom
        service.numero = int(request.POST.get('numero', 0) or 0)
        service.icone = request.POST.get('icone', '🏠').strip()
        service.description = request.POST.get('description', '').strip()
        service.description_longue = request.POST.get('description_longue', '').strip()
        service.lien_detail = request.POST.get('lien_detail', '#').strip()
        service.ordre = int(request.POST.get('ordre', 0) or 0)
        service.is_active = request.POST.get('is_active') == 'on'
        cat_pk = request.POST.get('categorie', '')
        if cat_pk:
            service.categorie = ServiceCategorie.objects.filter(pk=cat_pk).first()
        if request.FILES.get('image'):
            service.image = request.FILES['image']
        service.save()
        messages.success(request, f'Service "{service.nom}" enregistré.')
        return redirect('dashboard_services_liste')
    return render(request, 'eden/dashboard/service_form.html', {
        'service': service, 'categories': categories
    })


@login_required
@user_passes_test(is_agent)
def dashboard_service_supprimer(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        nom = service.nom
        service.delete()
        messages.success(request, f'Service "{nom}" supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_services_liste')
    return redirect('dashboard_services_liste')


@login_required
@user_passes_test(is_agent)
def dashboard_services_categories(request):
    categories = ServiceCategorie.objects.all().order_by('ordre')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            from django.utils.text import slugify
            nom = request.POST.get('nom', '').strip()
            if nom:
                slug = slugify(nom)
                base = slug
                i = 1
                while ServiceCategorie.objects.filter(slug=slug).exists():
                    slug = f"{base}-{i}"; i += 1
                ServiceCategorie.objects.create(
                    nom=nom, icone=request.POST.get('icone', '🔵'),
                    slug=slug, ordre=ServiceCategorie.objects.count()
                )
                messages.success(request, 'Catégorie ajoutée.')
        elif action == 'modifier':
            cat = get_object_or_404(ServiceCategorie, pk=request.POST.get('pk'))
            cat.nom = request.POST.get('nom', cat.nom)
            cat.icone = request.POST.get('icone', cat.icone)
            cat.ordre = int(request.POST.get('ordre', cat.ordre))
            cat.is_active = request.POST.get('is_active') == 'on'
            cat.save()
            messages.success(request, 'Catégorie modifiée.')
        elif action == 'supprimer':
            ServiceCategorie.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'Catégorie supprimée.')
        return redirect('dashboard_services_categories')
    return render(request, 'eden/dashboard/services_categories.html', {'categories': categories})


@login_required
@user_passes_test(is_agent)
def dashboard_services_processus(request):
    etapes = EtapeProcessus.objects.all().order_by('ordre', 'numero')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            EtapeProcessus.objects.create(
                numero=int(request.POST.get('numero', 0) or 0),
                titre=request.POST.get('titre', '').strip(),
                description=request.POST.get('description', '').strip(),
                icone=request.POST.get('icone', '✅'),
                ordre=EtapeProcessus.objects.count(),
            )
            messages.success(request, 'Étape ajoutée.')
        elif action == 'modifier':
            e = get_object_or_404(EtapeProcessus, pk=request.POST.get('pk'))
            e.numero = int(request.POST.get('numero', e.numero) or e.numero)
            e.titre = request.POST.get('titre', e.titre)
            e.description = request.POST.get('description', e.description)
            e.icone = request.POST.get('icone', e.icone)
            e.ordre = int(request.POST.get('ordre', e.ordre))
            e.is_active = request.POST.get('is_active') == 'on'
            e.save()
            messages.success(request, 'Étape modifiée.')
        elif action == 'supprimer':
            EtapeProcessus.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'Étape supprimée.')
        return redirect('dashboard_services_processus')
    return render(request, 'eden/dashboard/services_processus.html', {'etapes': etapes})


@login_required
@user_passes_test(is_agent)
def dashboard_services_engagements(request):
    engagements = EngagementService.objects.all().order_by('ordre')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            EngagementService.objects.create(
                icone=request.POST.get('icone', '🔒'),
                titre=request.POST.get('titre', '').strip(),
                description=request.POST.get('description', '').strip(),
                couleur=request.POST.get('couleur', 'blue'),
                ordre=EngagementService.objects.count(),
            )
            messages.success(request, 'Engagement ajouté.')
        elif action == 'modifier':
            eng = get_object_or_404(EngagementService, pk=request.POST.get('pk'))
            eng.icone = request.POST.get('icone', eng.icone)
            eng.titre = request.POST.get('titre', eng.titre)
            eng.description = request.POST.get('description', eng.description)
            eng.couleur = request.POST.get('couleur', eng.couleur)
            eng.ordre = int(request.POST.get('ordre', eng.ordre))
            eng.is_active = request.POST.get('is_active') == 'on'
            eng.save()
            messages.success(request, 'Engagement modifié.')
        elif action == 'supprimer':
            EngagementService.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'Engagement supprimé.')
        return redirect('dashboard_services_engagements')
    return render(request, 'eden/dashboard/services_engagements.html', {'engagements': engagements})

# =============================================
# API AJAX - Calcul dynamique pour le panneau flottant
# =============================================

def api_calcul_parcelles(request):
    """
    API AJAX pour le panneau flottant.
    Reçoit : budget, superficie, site_slug, statut
    Retourne : résultats calculés par site basés UNIQUEMENT sur prix_morcellable ou prix_min
    """
    from .models import SiteFoncier

    budget = request.GET.get('budget', '').strip()
    superficie = request.GET.get('superficie', '').strip()
    site_slug = request.GET.get('site', '').strip()
    statut = request.GET.get('statut', '').strip()

    results = []

    # Récupérer les sites actifs
    sites_qs = SiteFoncier.objects.filter(is_active=True)

    if site_slug:
        sites_qs = sites_qs.filter(slug=site_slug)

    if statut == 'disponible':
        sites_qs = sites_qs.filter(statut='disponible')
    elif statut == 'en_cours':
        sites_qs = sites_qs.filter(statut='en_cours')
    elif statut == 'promo':
        sites_qs = sites_qs.filter(en_promotion=True)

    # Convertir les valeurs
    budget_val = float(budget) if budget else None
    superficie_val = float(superficie) if superficie else None

    # Si aucun critère n'est fourni, retourner vide
    if not budget_val and not superficie_val and not site_slug and not statut:
        return JsonResponse({'results': [], 'count': 0})

    for site in sites_qs:
        # ═══ PRIX AU M² = prix_morcellable OU prix_min DU SITE ═══
        # Utiliser prix_morcellable s'il existe, sinon prix_min
        if site.prix_morcellable:
            prix_m2 = float(site.prix_morcellable)
        else:
            prix_m2 = float(site.prix_min) if site.prix_min else 0

        if prix_m2 == 0:
            continue

        # ═══ SUPERFICIE MINIMALE = superficie_morcellable OU calculée ═══
        superficie_min = site.superficie_min_effective

        # Préparer les infos de base
        info = {
            'nom': site.nom,
            'slug': site.slug,
            'url': site.get_absolute_url(),
            'prix_m2': round(prix_m2, 0),
            'nb_dispo': site.nb_disponibles,
            'statut': site.statut,
            'en_promotion': site.en_promotion,
            'superficie_min': round(superficie_min, 2),
        }

        # ─── CAS 1 : Budget seul ───────────────────────────────
        if budget_val and not superficie_val:
            superficie_possible = budget_val / prix_m2
            info['superficie_possible'] = round(superficie_possible, 2)
            
            if superficie_possible >= superficie_min:
                info['message'] = (
                    f"💰 Avec <strong>{format_fcfa(budget_val)} FCFA</strong> → "
                    f"<strong>{format_sup(superficie_possible)} m²</strong>"
                )
            else:
                manque = (prix_m2 * superficie_min) - budget_val
                info['message'] = (
                    f"⚠️ Budget insuffisant pour {format_sup(superficie_min)} m² minimum"
                )
                info['detail'] = (
                    f"💡 Avec <strong>{format_fcfa(budget_val)} FCFA</strong>, "
                    f"vous pouvez avoir <strong>{format_sup(superficie_possible)} m²</strong>\n"
                    f"💰 Il vous manque <strong>{format_fcfa(manque)} FCFA</strong> "
                    f"pour atteindre {format_sup(superficie_min)} m²"
                )
            info['detail'] = f"📐 Prix au m² : {format_fcfa(prix_m2)} FCFA/m²"
            results.append(info)

        # ─── CAS 2 : Superficie seule ─────────────────────────
        elif superficie_val and not budget_val:
            prix_total = superficie_val * prix_m2
            
            if superficie_val >= superficie_min:
                info['prix_total'] = round(prix_total, 0)
                info['message'] = (
                    f"📐 <strong>{format_sup(superficie_val)} m²</strong> → "
                    f"<strong>{format_fcfa(prix_total)} FCFA</strong>"
                )
                info['detail'] = f"📐 Prix au m² : {format_fcfa(prix_m2)} FCFA/m²"
            else:
                prix_pour_min = prix_m2 * superficie_min
                info['message'] = (
                    f"⚠️ La superficie minimale est de <strong>{format_sup(superficie_min)} m²</strong>"
                )
                info['detail'] = (
                    f"💡 {format_sup(superficie_min)} m² → <strong>{format_fcfa(prix_pour_min)} FCFA</strong>\n"
                    f"📐 Prix au m² : {format_fcfa(prix_m2)} FCFA/m²"
                )
            results.append(info)

        # ─── CAS 3 : Budget + Superficie ──────────────────────
        elif budget_val and superficie_val:
            prix_total = superficie_val * prix_m2
            
            if superficie_val < superficie_min:
                prix_pour_min = prix_m2 * superficie_min
                info['message'] = (
                    f"⚠️ La superficie minimale est de <strong>{format_sup(superficie_min)} m²</strong>"
                )
                info['detail'] = (
                    f"💡 {format_sup(superficie_min)} m² → <strong>{format_fcfa(prix_pour_min)} FCFA</strong>\n"
                    f"📐 Prix au m² : {format_fcfa(prix_m2)} FCFA/m²"
                )
                results.append(info)
            elif budget_val >= prix_total:
                reste = budget_val - prix_total
                info['compatible'] = True
                info['prix_total'] = round(prix_total, 0)
                info['reste'] = round(reste, 0)
                info['message'] = (
                    f"✅ <strong>{format_sup(superficie_val)} m²</strong> = "
                    f"<strong>{format_fcfa(prix_total)} FCFA</strong> "
                    f"(reste {format_fcfa(reste)} FCFA)"
                )
                info['detail'] = f"📐 Prix au m² : {format_fcfa(prix_m2)} FCFA/m²"
                results.append(info)
            else:
                superficie_possible = budget_val / prix_m2
                manque = prix_total - budget_val
                info['compatible'] = False
                info['superficie_possible'] = round(superficie_possible, 2)
                info['manque'] = round(manque, 0)
                
                if superficie_possible >= superficie_min:
                    info['message'] = (
                        f"⚠️ Budget insuffisant pour {format_sup(superficie_val)} m²"
                    )
                    info['detail'] = (
                        f"💡 Avec <strong>{format_fcfa(budget_val)} FCFA</strong>, "
                        f"vous pouvez avoir <strong>{format_sup(superficie_possible)} m²</strong>\n"
                        f"💰 Il vous manque <strong>{format_fcfa(manque)} FCFA</strong>\n"
                        f"📐 Prix au m² : {format_fcfa(prix_m2)} FCFA/m²"
                    )
                else:
                    manque_min = (prix_m2 * superficie_min) - budget_val
                    info['message'] = (
                        f"⚠️ Budget insuffisant pour atteindre {format_sup(superficie_min)} m²"
                    )
                    info['detail'] = (
                        f"💡 Avec <strong>{format_fcfa(budget_val)} FCFA</strong>, "
                        f"vous pouvez avoir <strong>{format_sup(superficie_possible)} m²</strong>\n"
                        f"💰 Il vous manque <strong>{format_fcfa(manque_min)} FCFA</strong> "
                        f"pour atteindre {format_sup(superficie_min)} m²"
                    )
                results.append(info)

        # ─── CAS 4 : Site seul sélectionné ────────────────────
        elif site_slug and site.slug == site_slug:
            info['message'] = f"📐 Prix au m² : <strong>{format_fcfa(prix_m2)} FCFA/m²</strong>"
            info['detail'] = (
                f"📏 Superficie minimale : <strong>{format_sup(superficie_min)} m²</strong>\n"
                f"💡 {format_sup(superficie_min)} m² → <strong>{format_fcfa(prix_m2 * superficie_min)} FCFA</strong>\n"
                f"💡 1000 m² → <strong>{format_fcfa(prix_m2 * 1000)} FCFA</strong>"
            )
            results.append(info)

    # Trier
    if budget_val and superficie_val:
        results.sort(key=lambda x: (
            not x.get('compatible', False),
            x.get('prix_m2', float('inf'))
        ))
    else:
        results.sort(key=lambda x: x.get('prix_m2', float('inf')))

    return JsonResponse({
        'results': results,
        'count': len(results),
        'budget': budget_val,
        'superficie': superficie_val
    })
    

# ══════════════════════════════════════════════
# MODULE ACADÉMIE — VERSION 2
# ══════════════════════════════════════════════

from .models import (
    AcademieDocument, AcademieVideo, AcademieEtapeParcours,
    AcademieFAQ, AcademieStatistique, AcademieCategorie,
    JournalEdition
)


def academie_accueil(request):
    """Page principale de l'Académie."""
    docs_publie = AcademieDocument.objects.filter(statut='publie')
    editions_publiees = JournalEdition.objects.filter(statut='publie')

    contexte = {
        # Articles = éditions de type 'article'
        'articles': editions_publiees.filter(type_academie='article').order_by('-date_parution')[:6],
        # Revues = éditions de type 'revue'
        'revues': editions_publiees.filter(type_academie='revue').order_by('-date_parution')[:4],
        # Guides = éditions de type 'guide'
        'guides': editions_publiees.filter(type_academie='guide').order_by('-date_parution')[:4],
        # Textes de loi
        'textes_loi': docs_publie.filter(categorie='texte_loi').order_by('ordre')[:3],
        # Lexique
        'lexique': docs_publie.filter(categorie='lexique').order_by('ordre'),
        # Galerie
        'galerie': docs_publie.filter(categorie='galerie').order_by('ordre')[:8],
        # Ressources (tout le contenu)
        'ressources': docs_publie.filter(categorie='ressource').order_by('ordre')[:6],
        # Vidéos
        'video_moment': AcademieVideo.objects.filter(statut='publie', est_video_moment=True).first(),
        'videos': AcademieVideo.objects.filter(statut='publie').order_by('ordre')[:8],
        # FAQ
        'faq_featured': AcademieFAQ.objects.filter(statut='publie', est_featured=True).first(),
        'faqs': AcademieFAQ.objects.filter(statut='publie').order_by('ordre')[:10],
        # Parcours
        'etapes_parcours': AcademieEtapeParcours.objects.filter(is_active=True).order_by('ordre'),
        # Stats
        'stats': AcademieStatistique.objects.filter(is_active=True).order_by('ordre'),
        # À la une = édition mise en avant OU doc mis en une
        'a_la_une_edition': editions_publiees.filter(
            type_academie__in=['article','revue','guide']
        ).order_by('-date_parution').first(),
        # Revue featured pour encart
        'revue_featured': editions_publiees.filter(type_academie='revue').order_by('-date_parution').first(),
        # Guide featured
        'guide_featured': editions_publiees.filter(type_academie='guide').order_by('-date_parution').first(),
        # Compteurs sidebar
        'nb_textes': docs_publie.filter(categorie='texte_loi').count(),
        'nb_articles': editions_publiees.filter(type_academie='article').count(),
        'nb_revues': editions_publiees.filter(type_academie='revue').count(),
        'nb_guides': editions_publiees.filter(type_academie='guide').count(),
        'nb_videos': AcademieVideo.objects.filter(statut='publie').count(),
        'nb_galerie': docs_publie.filter(categorie='galerie').count(),
        'nb_faqs': AcademieFAQ.objects.filter(statut='publie').count(),
        'nb_lexique': docs_publie.filter(categorie='lexique').count(),
    }
    return render(request, 'eden/academie/accueil.html', contexte)


def academie_recherche(request):
    """Recherche globale dans toute l'Académie."""
    q = request.GET.get('q', '').strip()
    resultats = {'q': q, 'docs': [], 'editions': [], 'videos': [], 'faqs': [], 'lexique': []}

    if q and len(q) >= 2:
        resultats['docs'] = AcademieDocument.objects.filter(
            statut='publie'
        ).filter(
            Q(titre__icontains=q) | Q(description__icontains=q) | Q(reference_officielle__icontains=q)
        ).order_by('categorie')[:20]

        resultats['editions'] = JournalEdition.objects.filter(
            statut='publie',
            type_academie__in=['article', 'revue', 'guide']
        ).filter(
            Q(titre__icontains=q) | Q(sous_titre__icontains=q)
        )[:10]

        resultats['videos'] = AcademieVideo.objects.filter(
            statut='publie'
        ).filter(
            Q(titre__icontains=q) | Q(description__icontains=q)
        )[:6]

        resultats['faqs'] = AcademieFAQ.objects.filter(
            statut='publie'
        ).filter(
            Q(question__icontains=q) | Q(reponse__icontains=q)
        )[:6]

        resultats['lexique'] = AcademieDocument.objects.filter(
            statut='publie', categorie='lexique'
        ).filter(
            Q(titre__icontains=q) | Q(description__icontains=q)
        )[:10]

    return render(request, 'eden/academie/recherche.html', resultats)


def academie_categorie(request, cat):
    """Liste complète d'une catégorie."""
    origine = request.GET.get('from', 'academie')
    label_map = {
        'texte_loi': 'Textes de loi',
        'article': 'Articles',
        'revue': 'Revues',
        'guide': 'Guides pratiques',
        'lexique': 'Lexique du foncier',
        'galerie': 'Galerie',
        'ressource': 'Centre de ressources',
        'video': 'Vidéothèque',
        'faq': 'Questions fréquentes',
    }
    label = label_map.get(cat, cat)

    if cat == 'video':
        items = AcademieVideo.objects.filter(statut='publie').order_by('ordre')
        return render(request, 'eden/academie/liste_videos.html', {
            'items': items, 'categorie': cat, 'categorie_label': label, 'origine': origine
        })

    if cat == 'faq':
        items = AcademieFAQ.objects.filter(statut='publie').order_by('ordre')
        return render(request, 'eden/academie/liste_faq.html', {
            'items': items, 'categorie': cat, 'categorie_label': label, 'origine': origine
        })

    if cat in ['article', 'revue', 'guide']:
        # Ce sont des éditions Journal
        items = JournalEdition.objects.filter(
            statut='publie', type_academie=cat
        ).order_by('-date_parution')
        return render(request, 'eden/academie/liste_editions.html', {
            'items': items, 'categorie': cat, 'categorie_label': label, 'origine': origine
        })

    if cat == 'lexique':
        items = AcademieDocument.objects.filter(statut='publie', categorie='lexique').order_by('titre')
        return render(request, 'eden/academie/lexique.html', {
            'items': items, 'categorie': cat, 'categorie_label': label, 'origine': origine
        })

    if cat == 'ressource':
        # Centre de ressources = TOUT le contenu
        editions = JournalEdition.objects.filter(
            statut='publie', type_academie__in=['article','revue','guide']
        ).order_by('-date_parution')
        docs = AcademieDocument.objects.filter(statut='publie').order_by('categorie', 'ordre')
        videos = AcademieVideo.objects.filter(statut='publie').order_by('ordre')
        return render(request, 'eden/academie/centre_ressources.html', {
            'editions': editions, 'docs': docs, 'videos': videos,
            'categorie': cat, 'categorie_label': label, 'origine': origine
        })

    # Textes loi, galerie
    docs = AcademieDocument.objects.filter(statut='publie', categorie=cat).order_by('ordre', '-date_publication')
    return render(request, 'eden/academie/liste_documents.html', {
        'documents': docs, 'categorie': cat, 'categorie_label': label, 'origine': origine
    })


def academie_telecharger(request, pk):
    from django.http import FileResponse, Http404
    doc = get_object_or_404(AcademieDocument, pk=pk, statut='publie')
    if not doc.fichier_pdf:
        raise Http404("Fichier non disponible.")
    doc.incrementer_telechargements()
    response = FileResponse(doc.fichier_pdf.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{doc.fichier_pdf.name.split("/")[-1]}"'
    return response


def academie_voir_video(request, pk):
    from django.http import FileResponse, Http404
    video = get_object_or_404(AcademieVideo, pk=pk, statut='publie')
    if not video.fichier_video:
        raise Http404("Vidéo non disponible.")
    video.nb_vues += 1
    video.save(update_fields=['nb_vues'])
    response = FileResponse(video.fichier_video.open('rb'), content_type='video/mp4')
    response['Content-Disposition'] = f'inline; filename="{video.fichier_video.name.split("/")[-1]}"'
    return response


# ── Dashboard Académie ──

@login_required
@user_passes_test(is_agent)
def dashboard_academie_liste(request):
    docs = AcademieDocument.objects.all().order_by('-created_at')
    cat = request.GET.get('cat', '')
    if cat:
        docs = docs.filter(categorie=cat)
    return render(request, 'eden/dashboard/academie_liste.html', {
        'docs': docs,
        'cat': cat,
        'categories': AcademieCategorie.choices,
        'nb_total': AcademieDocument.objects.count(),
        'nb_publie': AcademieDocument.objects.filter(statut='publie').count(),
        # ✅ Ajouté
        'nb_lexique': AcademieDocument.objects.filter(categorie='lexique').count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_academie_form(request, pk=None):
    doc = get_object_or_404(AcademieDocument, pk=pk) if pk else None
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/academie_form.html', {
                'doc': doc, 'categories': AcademieCategorie.choices
            })
        if not doc:
            doc = AcademieDocument()
        doc.titre = titre
        doc.sous_titre = request.POST.get('sous_titre', '').strip()
        doc.categorie = request.POST.get('categorie', 'article')
        doc.description = request.POST.get('description', '').strip()
        doc.auteur = request.POST.get('auteur', '').strip()
        doc.reference_officielle = request.POST.get('reference_officielle', '').strip()
        doc.numero_revue = request.POST.get('numero_revue', '').strip()
        doc.temps_lecture = request.POST.get('temps_lecture', '').strip()
        doc.statut = request.POST.get('statut', 'brouillon')
        doc.est_a_la_une = request.POST.get('est_a_la_une') == 'on'
        doc.est_featured = request.POST.get('est_featured') == 'on'
        doc.ordre = int(request.POST.get('ordre', 0) or 0)
        date_str = request.POST.get('date_publication', '')
        if date_str:
            from datetime import date
            try:
                doc.date_publication = date.fromisoformat(date_str)
            except Exception:
                pass
        nb_p = request.POST.get('nb_pages', '')
        if nb_p:
            try:
                doc.nb_pages = int(nb_p)
            except Exception:
                pass
        if request.FILES.get('image_couverture'):
            doc.image_couverture = request.FILES['image_couverture']
        if request.FILES.get('fichier_pdf'):
            doc.fichier_pdf = request.FILES['fichier_pdf']
        doc.save()
        messages.success(request, f'"{doc.titre}" enregistré.')
        return redirect('dashboard_academie_liste')
    return render(request, 'eden/dashboard/academie_form.html', {
        'doc': doc, 'categories': AcademieCategorie.choices
    })


@login_required
@user_passes_test(is_agent)
def dashboard_academie_supprimer(request, pk):
    doc = get_object_or_404(AcademieDocument, pk=pk)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Document supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_academie_liste')
    return redirect('dashboard_academie_liste')


@login_required
@user_passes_test(is_agent)
def dashboard_academie_videos(request):
    videos = AcademieVideo.objects.all().order_by('ordre', '-created_at')
    return render(request, 'eden/dashboard/academie_videos.html', {'videos': videos})


@login_required
@user_passes_test(is_agent)
def dashboard_academie_video_form(request, pk=None):
    video = get_object_or_404(AcademieVideo, pk=pk) if pk else None
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/academie_video_form.html', {'video': video})
        if not video:
            video = AcademieVideo()
        video.titre = titre
        video.description = request.POST.get('description', '').strip()
        video.auteur = request.POST.get('auteur', '').strip()
        video.duree = request.POST.get('duree', '').strip()
        video.statut = request.POST.get('statut', 'brouillon')
        video.est_video_moment = request.POST.get('est_video_moment') == 'on'
        video.ordre = int(request.POST.get('ordre', 0) or 0)
        date_str = request.POST.get('date_publication', '')
        if date_str:
            from datetime import date
            try:
                video.date_publication = date.fromisoformat(date_str)
            except Exception:
                pass
        if request.FILES.get('fichier_video'):
            video.fichier_video = request.FILES['fichier_video']
        if request.FILES.get('image_miniature'):
            video.image_miniature = request.FILES['image_miniature']
        video.save()
        messages.success(request, f'Vidéo "{video.titre}" enregistrée.')
        return redirect('dashboard_academie_videos')
    return render(request, 'eden/dashboard/academie_video_form.html', {'video': video})


@login_required
@user_passes_test(is_agent)
def dashboard_academie_video_supprimer(request, pk):
    video = get_object_or_404(AcademieVideo, pk=pk)
    if request.method == 'POST':
        video.delete()
        messages.success(request, 'Vidéo supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_academie_videos')
    return redirect('dashboard_academie_videos')


@login_required
@user_passes_test(is_agent)
def dashboard_academie_faq(request):
    faqs = AcademieFAQ.objects.all().order_by('ordre')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            AcademieFAQ.objects.create(
                question=request.POST.get('question', '').strip(),
                reponse=request.POST.get('reponse', '').strip(),
                categorie_faq=request.POST.get('categorie_faq', '').strip(),
                temps_reponse=request.POST.get('temps_reponse', '').strip(),
                est_featured=request.POST.get('est_featured') == 'on',
                statut=request.POST.get('statut', 'publie'),
                ordre=AcademieFAQ.objects.count(),
            )
            messages.success(request, 'FAQ ajoutée.')
        elif action == 'modifier':
            faq = get_object_or_404(AcademieFAQ, pk=request.POST.get('pk'))
            faq.question = request.POST.get('question', faq.question)
            faq.reponse = request.POST.get('reponse', faq.reponse)
            faq.categorie_faq = request.POST.get('categorie_faq', faq.categorie_faq)
            faq.temps_reponse = request.POST.get('temps_reponse', faq.temps_reponse)
            faq.est_featured = request.POST.get('est_featured') == 'on'
            faq.statut = request.POST.get('statut', faq.statut)
            faq.ordre = int(request.POST.get('ordre', faq.ordre))
            faq.save()
            messages.success(request, 'FAQ modifiée.')
        elif action == 'supprimer':
            AcademieFAQ.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'FAQ supprimée.')
        return redirect('dashboard_academie_faq')
    return render(request, 'eden/dashboard/academie_faq.html', {'faqs': faqs})


@login_required
@user_passes_test(is_agent)
def dashboard_academie_parcours(request):
    etapes = AcademieEtapeParcours.objects.all().order_by('ordre', 'numero')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            AcademieEtapeParcours.objects.create(
                numero=int(request.POST.get('numero', 0) or 0),
                titre=request.POST.get('titre', '').strip(),
                icone=request.POST.get('icone', '📋'),
                description=request.POST.get('description', '').strip(),
                ordre=AcademieEtapeParcours.objects.count(),
            )
            messages.success(request, 'Étape ajoutée.')
        elif action == 'modifier':
            e = get_object_or_404(AcademieEtapeParcours, pk=request.POST.get('pk'))
            e.numero = int(request.POST.get('numero', e.numero) or e.numero)
            e.titre = request.POST.get('titre', e.titre)
            e.icone = request.POST.get('icone', e.icone)
            e.description = request.POST.get('description', e.description)
            e.ordre = int(request.POST.get('ordre', e.ordre))
            e.is_active = request.POST.get('is_active') == 'on'
            e.save()
            messages.success(request, 'Étape modifiée.')
        elif action == 'supprimer':
            AcademieEtapeParcours.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'Étape supprimée.')
        return redirect('dashboard_academie_parcours')
    return render(request, 'eden/dashboard/academie_parcours.html', {'etapes': etapes})


@login_required
@user_passes_test(is_agent)
def dashboard_academie_stats(request):
    stats = AcademieStatistique.objects.all().order_by('ordre')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            AcademieStatistique.objects.create(
                valeur=request.POST.get('valeur', '0'),
                label=request.POST.get('label', ''),
                icone=request.POST.get('icone', '📋'),
                ordre=AcademieStatistique.objects.count(),
            )
            messages.success(request, 'Stat ajoutée.')
        elif action == 'modifier':
            s = get_object_or_404(AcademieStatistique, pk=request.POST.get('pk'))
            s.valeur = request.POST.get('valeur', s.valeur)
            s.label = request.POST.get('label', s.label)
            s.icone = request.POST.get('icone', s.icone)
            s.ordre = int(request.POST.get('ordre', s.ordre))
            s.is_active = request.POST.get('is_active') == 'on'
            s.save()
            messages.success(request, 'Stat modifiée.')
        elif action == 'supprimer':
            AcademieStatistique.objects.filter(pk=request.POST.get('pk')).delete()
            messages.success(request, 'Stat supprimée.')
        return redirect('dashboard_academie_stats')
    return render(request, 'eden/dashboard/academie_stats.html', {'stats': stats})


# ══════════════════════════════════════════════
# CRÉATION ARTICLES / REVUES / GUIDES
# (via le système Journal existant)
# ══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_journal_article_form(request, pk=None):
    from .models import JournalEdition
    import uuid as uuid_module

    edition = get_object_or_404(JournalEdition, pk=pk) if pk else None

    url_name = request.resolver_match.url_name
    if 'revue' in url_name:
        type_defaut = 'revue'
    elif 'guide' in url_name:
        type_defaut = 'guide'
    else:
        type_defaut = 'article'

    if edition:
        type_defaut = edition.type_academie

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/academie_publication_form.html', {
                'edition': edition, 'type_defaut': type_defaut
            })

        if not edition:
            edition = JournalEdition()

        edition.titre = titre
        edition.sous_titre = request.POST.get('sous_titre', '').strip()
        edition.type_academie = request.POST.get('type_academie', type_defaut)
        edition.statut = request.POST.get('statut', 'brouillon')

        # ── Numéro : toujours unique ──
        numero = request.POST.get('numero', '').strip()

        if not numero:
            # Générer un numéro unique avec uuid court
            prefix = {
                'article': 'ART',
                'revue': 'REV',
                'guide': 'GUI',
                'journal': 'JNL',
            }.get(edition.type_academie, 'PUB')
            # Boucle pour garantir l'unicité
            for _ in range(20):
                short = str(uuid_module.uuid4())[:8].upper()
                candidat = f"{prefix}-{short}"
                if not JournalEdition.objects.filter(numero=candidat).exclude(
                    pk=edition.pk if edition.pk else None
                ).exists():
                    numero = candidat
                    break
            else:
                # Fallback timestamp
                import time
                numero = f"{prefix}-{int(time.time())}"

        # Vérifier unicité si numéro saisi manuellement
        qs = JournalEdition.objects.filter(numero=numero)
        if edition.pk:
            qs = qs.exclude(pk=edition.pk)
        if qs.exists():
            messages.error(
                request,
                f'Le numéro "{numero}" existe déjà. '
                f'Laissez le champ vide pour un numéro automatique.'
            )
            return render(request, 'eden/dashboard/academie_publication_form.html', {
                'edition': edition, 'type_defaut': type_defaut
            })

        edition.numero = numero

        date_str = request.POST.get('date_parution', '')
        if date_str:
            from datetime import date
            try:
                edition.date_parution = date.fromisoformat(date_str)
            except Exception:
                pass

        if request.FILES.get('image_une'):
            edition.image_une = request.FILES['image_une']

        edition.save()

        # Créer une première page vide si c'est une nouvelle édition
        if not edition.pages.exists():
            from .models import JournalPage
            JournalPage.objects.create(
                edition=edition,
                numero=1,
                contenu=[],
                layout='libre'
            )

        messages.success(request, f'"{edition.titre}" enregistré (N° {edition.numero}).')

        if request.POST.get('action') == 'editeur':
            return redirect('dashboard_journal_page_editer',
                            edition_pk=edition.pk, page_num=1)

        return redirect('dashboard_academie_publications')

    return render(request, 'eden/dashboard/academie_publication_form.html', {
        'edition': edition,
        'type_defaut': type_defaut,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_academie_publications(request):
    """Liste des articles, revues et guides."""
    from .models import JournalEdition
    type_f = request.GET.get('type', '')
    publications = JournalEdition.objects.filter(
        type_academie__in=['article', 'revue', 'guide']
    ).order_by('-created_at')

    if type_f:
        publications = publications.filter(type_academie=type_f)

    return render(request, 'eden/dashboard/academie_publications.html', {
        'publications': publications,
        'type_f': type_f,
        'nb_articles': JournalEdition.objects.filter(type_academie='article').count(),
        'nb_revues': JournalEdition.objects.filter(type_academie='revue').count(),
        'nb_guides': JournalEdition.objects.filter(type_academie='guide').count(),
    })


# ══════════════════════════════════════════════
# GALERIE ACADÉMIE
# ══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_academie_galerie(request):
    items = AcademieDocument.objects.filter(
        categorie='galerie'
    ).order_by('ordre', '-created_at')
    return render(request, 'eden/dashboard/academie_galerie.html', {
        'items': items,
        'nb': items.count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_academie_galerie_form(request, pk=None):
    item = get_object_or_404(AcademieDocument, pk=pk, categorie='galerie') if pk else None

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/academie_galerie_form.html', {'item': item})

        if not item:
            item = AcademieDocument()
            item.categorie = 'galerie'

        item.titre = titre
        item.description = request.POST.get('description', '').strip()
        item.statut = request.POST.get('statut', 'publie')
        item.ordre = int(request.POST.get('ordre', 0) or 0)

        if request.FILES.get('image_couverture'):
            item.image_couverture = request.FILES['image_couverture']

        item.save()
        messages.success(request, f'Image "{item.titre}" enregistrée.')
        return redirect('dashboard_academie_galerie')

    return render(request, 'eden/dashboard/academie_galerie_form.html', {'item': item})


@login_required
@user_passes_test(is_agent)
def dashboard_academie_galerie_supprimer(request, pk):
    item = get_object_or_404(AcademieDocument, pk=pk, categorie='galerie')
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Image supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_academie_galerie')
    return redirect('dashboard_academie_galerie')

# ══════════════════════════════════════════════
# LEXIQUE FONCIER
# ══════════════════════════════════════════════

def academie_lexique(request):
    """Page publique du lexique foncier — dictionnaire A-Z."""
    q = request.GET.get('q', '').strip()
    lettre = request.GET.get('lettre', '').upper()

    items = AcademieDocument.objects.filter(
        statut='publie', categorie='lexique'
    ).order_by('titre')

    if q:
        items = items.filter(
            Q(titre__icontains=q) | Q(description__icontains=q)
        )
    if lettre:
        items = items.filter(titre__istartswith=lettre)

    # Grouper par lettre
    from collections import OrderedDict
    grouped = OrderedDict()
    for item in items:
        l = item.titre[0].upper() if item.titre else '#'
        if l not in grouped:
            grouped[l] = []
        grouped[l].append(item)

    # Lettres disponibles pour la navigation
    lettres_dispo = sorted(set(
        doc.titre[0].upper()
        for doc in AcademieDocument.objects.filter(
            statut='publie', categorie='lexique'
        )
        if doc.titre
    ))

    return render(request, 'eden/academie/lexique.html', {
        'grouped': grouped,
        'lettres_dispo': lettres_dispo,
        'q': q,
        'lettre': lettre,
        'nb_total': AcademieDocument.objects.filter(
            statut='publie', categorie='lexique'
        ).count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_lexique(request):
    """Liste des entrées du lexique."""
    items = AcademieDocument.objects.filter(
        categorie='lexique'
    ).order_by('titre')
    q = request.GET.get('q', '')
    if q:
        items = items.filter(
            Q(titre__icontains=q) | Q(description__icontains=q)
        )
    return render(request, 'eden/dashboard/lexique_liste.html', {
        'items': items,
        'q': q,
        'nb': items.count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_lexique_form(request, pk=None):
    """Créer ou modifier une entrée du lexique."""
    item = get_object_or_404(
        AcademieDocument, pk=pk, categorie='lexique'
    ) if pk else None

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le terme est obligatoire.')
            return render(request, 'eden/dashboard/lexique_form.html', {
                'item': item
            })

        if not item:
            item = AcademieDocument()
            item.categorie = 'lexique'

        item.titre = titre
        item.description = request.POST.get('description', '').strip()
        item.sous_titre = request.POST.get('sous_titre', '').strip()
        item.auteur = request.POST.get('auteur', '').strip()
        item.statut = request.POST.get('statut', 'publie')
        item.ordre = int(request.POST.get('ordre', 0) or 0)

        if request.FILES.get('fichier_pdf'):
            item.fichier_pdf = request.FILES['fichier_pdf']

        item.save()
        messages.success(request, f'"{item.titre}" enregistré.')
        return redirect('dashboard_lexique')

    return render(request, 'eden/dashboard/lexique_form.html', {
        'item': item
    })


@login_required
@user_passes_test(is_agent)
def dashboard_lexique_supprimer(request, pk):
    item = get_object_or_404(AcademieDocument, pk=pk, categorie='lexique')
    if request.method == 'POST':
        titre = item.titre
        item.delete()
        messages.success(request, f'"{titre}" supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_lexique')
    return redirect('dashboard_lexique')

@login_required
@user_passes_test(is_agent)
def dashboard_video_globale(request):
    """Gestion de la vidéo globale"""
    videos = VideoGlobale.objects.all().order_by('ordre')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'ajouter':
            titre = request.POST.get('titre', '').strip()
            if titre and request.FILES.get('video'):
                VideoGlobale.objects.create(
                    titre=titre,
                    video=request.FILES['video'],
                    position=request.POST.get('position', 'bottom-right'),
                    largeur=int(request.POST.get('largeur', 500)),
                    hauteur=int(request.POST.get('hauteur', 280)),  # ✅ AJOUT
                    is_active=request.POST.get('is_active') == 'on',
                    ordre=VideoGlobale.objects.count(),
                )
                messages.success(request, 'Vidéo ajoutée.')
            else:
                messages.error(request, 'Titre et fichier vidéo obligatoires.')
        
        elif action == 'modifier':
            pk = request.POST.get('pk')
            video = get_object_or_404(VideoGlobale, pk=pk)
            video.titre = request.POST.get('titre', video.titre)
            video.position = request.POST.get('position', video.position)
            video.largeur = int(request.POST.get('largeur', video.largeur))
            video.hauteur = int(request.POST.get('hauteur', video.hauteur))  # ✅ AJOUT
            video.is_active = request.POST.get('is_active') == 'on'
            if request.FILES.get('video'):
                video.video = request.FILES['video']
            video.save()
            messages.success(request, 'Vidéo modifiée.')
        
        elif action == 'supprimer':
            pk = request.POST.get('pk')
            VideoGlobale.objects.filter(pk=pk).delete()
            messages.success(request, 'Vidéo supprimée.')
        
        elif action == 'toggle':
            pk = request.POST.get('pk')
            video = get_object_or_404(VideoGlobale, pk=pk)
            video.is_active = not video.is_active
            video.save()
            messages.success(request, f'Vidéo {"activée" if video.is_active else "désactivée"}.')
        
        return redirect('dashboard_video_globale')
    
    return render(request, 'eden/dashboard/video_globale.html', {
        'videos': videos,
        'positions': VideoGlobale._meta.get_field('position').choices,
    })

# ══════════════════════════════════════════════
# MODULE À PROPOS — DASHBOARD
# ══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_apropos(request):
    """Tableau de bord du module À Propos."""
    from .models import (
        AProposSection, AProposElement, AProposIndicateur,
        AProposTableau, AProposEtape,
    )

    sections = AProposSection.objects.all().order_by('ordre')

    sections_data = []
    for s in sections:
        nb_elements = 0
        if s.type_section in ['presentation', 'activites', 'valeurs', 'equipe']:
            nb_elements = s.elements.count()
        elif s.type_section == 'histoire':
            nb_elements = s.etapes.count()
        elif s.type_section == 'chiffres':
            nb_elements = s.indicateurs.count() + s.tableaux.count()
        sections_data.append({'section': s, 'nb_elements': nb_elements})

    return render(request, 'eden/dashboard/apropos/index.html', {
        'sections_data': sections_data,
        'nb_sections': sections.count(),
        'nb_actives': sections.filter(is_active=True).count(),
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_section_form(request, pk=None):
    """Créer/modifier une section À Propos."""
    from .models import AProposSection

    section = get_object_or_404(AProposSection, pk=pk) if pk else None

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        type_section = request.POST.get('type_section', '').strip()

        if not titre or not type_section:
            messages.error(request, 'Le type et le titre sont obligatoires.')
            return render(request, 'eden/dashboard/apropos/section_form.html', {
                'section': section,
                'types': AProposSection.TYPE_CHOICES,
            })

        # Vérifier qu'on ne crée pas de doublon de type
        if not section:
            existing = AProposSection.objects.filter(type_section=type_section).first()
            if existing:
                messages.error(request, f'Une section "{existing.get_type_section_display()}" existe déjà. Modifiez-la au lieu d\'en créer une nouvelle.')
                return redirect('dashboard_apropos')

        if not section:
            section = AProposSection()

        section.type_section = type_section
        section.titre = titre
        section.titre_accent = request.POST.get('titre_accent', '').strip()
        section.description = request.POST.get('description', '').strip()
        section.ordre = int(request.POST.get('ordre', 0) or 0)
        section.is_active = request.POST.get('is_active') == 'on'
        section.save()

        messages.success(request, f'Section "{section.titre}" enregistrée.')
        return redirect('dashboard_apropos')

    return render(request, 'eden/dashboard/apropos/section_form.html', {
        'section': section,
        'types': AProposSection.TYPE_CHOICES,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_section_supprimer(request, pk):
    from .models import AProposSection
    section = get_object_or_404(AProposSection, pk=pk)
    if request.method == 'POST':
        titre = section.titre
        section.delete()
        messages.success(request, f'Section "{titre}" supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    return redirect('dashboard_apropos')


# ══════════════════════════════════════════════
# ÉLÉMENTS
# ══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_apropos_elements(request, section_pk):
    from .models import AProposSection, AProposElement

    section = get_object_or_404(AProposSection, pk=section_pk)
    elements = section.elements.all().order_by('ordre')

    return render(request, 'eden/dashboard/apropos/elements_liste.html', {
        'section': section,
        'elements': elements,
        'is_equipe': section.type_section == 'equipe',
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_element_form(request, section_pk=None, pk=None):
    from .models import AProposSection, AProposElement

    element = get_object_or_404(AProposElement, pk=pk) if pk else None

    if element:
        section = element.section
    elif section_pk:
        section = get_object_or_404(AProposSection, pk=section_pk)
    else:
        messages.error(request, 'Section introuvable.')
        return redirect('dashboard_apropos')

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/apropos/element_form.html', {
                'section': section,
                'element': element,
                'is_equipe': section.type_section == 'equipe',
            })

        if not element:
            element = AProposElement(section=section)

        element.icone = request.POST.get('icone', '').strip()
        element.initiales = request.POST.get('initiales', '').strip()
        element.titre = titre
        element.sous_titre = request.POST.get('sous_titre', '').strip()
        element.description = request.POST.get('description', '').strip()
        element.couleur_debut = request.POST.get('couleur_debut', '#1B4FDB').strip()
        element.couleur_fin = request.POST.get('couleur_fin', '#7B20B4').strip()
        element.ordre = int(request.POST.get('ordre', 0) or 0)
        element.is_active = request.POST.get('is_active') == 'on'
        element.save()

        messages.success(request, f'Élément "{element.titre}" enregistré.')
        return redirect('dashboard_apropos_elements', section_pk=section.pk)

    return render(request, 'eden/dashboard/apropos/element_form.html', {
        'section': section,
        'element': element,
        'is_equipe': section.type_section == 'equipe',
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_element_supprimer(request, pk):
    from .models import AProposElement
    element = get_object_or_404(AProposElement, pk=pk)
    section_pk = element.section.pk

    if request.method == 'POST':
        element.delete()
        messages.success(request, 'Élément supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_apropos_elements', section_pk=section_pk)

    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': element,
        'retour': 'dashboard_apropos_elements',
    })


# ══════════════════════════════════════════════
# INDICATEURS
# ══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_apropos_indicateurs(request, section_pk):
    from .models import AProposSection, AProposIndicateur

    section = get_object_or_404(AProposSection, pk=section_pk)
    indicateurs = section.indicateurs.all().order_by('ordre')

    return render(request, 'eden/dashboard/apropos/indicateurs_liste.html', {
        'section': section,
        'indicateurs': indicateurs,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_indicateur_form(request, section_pk=None, pk=None):
    from .models import AProposSection, AProposIndicateur

    indicateur = get_object_or_404(AProposIndicateur, pk=pk) if pk else None

    if indicateur:
        section = indicateur.section
    elif section_pk:
        section = get_object_or_404(AProposSection, pk=section_pk)
    else:
        messages.error(request, 'Section introuvable.')
        return redirect('dashboard_apropos')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        label = request.POST.get('label', '').strip()

        if not nombre or not label:
            messages.error(request, 'Valeur et label sont obligatoires.')
            return render(request, 'eden/dashboard/apropos/indicateur_form.html', {
                'section': section,
                'indicateur': indicateur,
                'icons': AProposIndicateur.ICON_CHOICES,
            })

        if not indicateur:
            indicateur = AProposIndicateur(section=section)

        indicateur.icone = request.POST.get('icone', 'fa-calendar')
        indicateur.nombre = nombre
        indicateur.suffixe = request.POST.get('suffixe', '').strip()
        indicateur.label = label
        indicateur.ordre = int(request.POST.get('ordre', 0) or 0)
        indicateur.is_active = request.POST.get('is_active') == 'on'
        indicateur.save()

        messages.success(request, f'Indicateur "{indicateur.label}" enregistré.')
        return redirect('dashboard_apropos_indicateurs', section_pk=section.pk)

    return render(request, 'eden/dashboard/apropos/indicateur_form.html', {
        'section': section,
        'indicateur': indicateur,
        'icons': AProposIndicateur.ICON_CHOICES,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_indicateur_supprimer(request, pk):
    from .models import AProposIndicateur
    indicateur = get_object_or_404(AProposIndicateur, pk=pk)
    section_pk = indicateur.section.pk

    if request.method == 'POST':
        indicateur.delete()
        messages.success(request, 'Indicateur supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_apropos_indicateurs', section_pk=section_pk)

    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': indicateur,
        'retour': 'dashboard_apropos_indicateurs',
    })


# ══════════════════════════════════════════════
# ÉTAPES TIMELINE
# ══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_apropos_etapes(request, section_pk):
    from .models import AProposSection, AProposEtape

    section = get_object_or_404(AProposSection, pk=section_pk)
    etapes = section.etapes.all().order_by('ordre')

    return render(request, 'eden/dashboard/apropos/etapes_liste.html', {
        'section': section,
        'etapes': etapes,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_etape_form(request, section_pk=None, pk=None):
    from .models import AProposSection, AProposEtape

    etape = get_object_or_404(AProposEtape, pk=pk) if pk else None

    if etape:
        section = etape.section
    elif section_pk:
        section = get_object_or_404(AProposSection, pk=section_pk)
    else:
        messages.error(request, 'Section introuvable.')
        return redirect('dashboard_apropos')

    if request.method == 'POST':
        annee = request.POST.get('annee', '').strip()
        description = request.POST.get('description', '').strip()

        if not annee or not description:
            messages.error(request, 'Année et description sont obligatoires.')
            return render(request, 'eden/dashboard/apropos/etape_form.html', {
                'section': section,
                'etape': etape,
            })

        if not etape:
            etape = AProposEtape(section=section)

        etape.annee = annee
        etape.description = description
        etape.position = request.POST.get('position', 'gauche')
        etape.ordre = int(request.POST.get('ordre', 0) or 0)
        etape.is_active = request.POST.get('is_active') == 'on'
        etape.save()

        messages.success(request, f'Étape {etape.annee} enregistrée.')
        return redirect('dashboard_apropos_etapes', section_pk=section.pk)

    return render(request, 'eden/dashboard/apropos/etape_form.html', {
        'section': section,
        'etape': etape,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_etape_supprimer(request, pk):
    from .models import AProposEtape
    etape = get_object_or_404(AProposEtape, pk=pk)
    section_pk = etape.section.pk

    if request.method == 'POST':
        etape.delete()
        messages.success(request, 'Étape supprimée.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_apropos_etapes', section_pk=section_pk)

    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': etape,
        'retour': 'dashboard_apropos_etapes',
    })


# ══════════════════════════════════════════════
# TABLEAUX
# ══════════════════════════════════════════════

@login_required
@user_passes_test(is_agent)
def dashboard_apropos_tableaux(request, section_pk):
    from .models import AProposSection, AProposTableau

    section = get_object_or_404(AProposSection, pk=section_pk)
    tableaux = section.tableaux.all().order_by('ordre')

    return render(request, 'eden/dashboard/apropos/tableaux_liste.html', {
        'section': section,
        'tableaux': tableaux,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_tableau_form(request, section_pk=None, pk=None):
    from .models import AProposSection, AProposTableau

    tableau = get_object_or_404(AProposTableau, pk=pk) if pk else None

    if tableau:
        section = tableau.section
    elif section_pk:
        section = get_object_or_404(AProposSection, pk=section_pk)
    else:
        messages.error(request, 'Section introuvable.')
        return redirect('dashboard_apropos')

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        if not titre:
            messages.error(request, 'Le titre est obligatoire.')
            return render(request, 'eden/dashboard/apropos/tableau_form.html', {
                'section': section,
                'tableau': tableau,
            })

        if not tableau:
            tableau = AProposTableau(section=section)

        tableau.titre = titre
        tableau.est_pour_graphique = request.POST.get('est_pour_graphique') == 'on'
        tableau.ordre = int(request.POST.get('ordre', 0) or 0)
        tableau.save()

        messages.success(request, f'Tableau "{tableau.titre}" enregistré.')
        return redirect('dashboard_apropos_tableau_editer', pk=tableau.pk)

    return render(request, 'eden/dashboard/apropos/tableau_form.html', {
        'section': section,
        'tableau': tableau,
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_tableau_supprimer(request, pk):
    from .models import AProposTableau
    tableau = get_object_or_404(AProposTableau, pk=pk)
    section_pk = tableau.section.pk

    if request.method == 'POST':
        tableau.delete()
        messages.success(request, 'Tableau supprimé.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('dashboard_apropos_tableaux', section_pk=section_pk)

    return render(request, 'eden/dashboard/confirm_delete.html', {
        'objet': tableau,
        'retour': 'dashboard_apropos_tableaux',
    })


@login_required
@user_passes_test(is_agent)
def dashboard_apropos_tableau_editer(request, pk):
    """Éditeur interactif de tableau."""
    from .models import AProposTableau, AProposColonne, AProposLigne, AProposCellule

    tableau = get_object_or_404(AProposTableau, pk=pk)
    colonnes = list(tableau.colonnes.all().order_by('ordre'))
    lignes = list(tableau.lignes.all().order_by('ordre'))

    # ═══ CONSTRUIRE UNE MATRICE PRÊTE POUR LE TEMPLATE ═══
    matrice = []
    for ligne in lignes:
        valeurs = []
        for colonne in colonnes:
            cellule = AProposCellule.objects.filter(
                ligne=ligne, colonne=colonne
            ).first()
            valeurs.append({
                'colonne_id': colonne.pk,
                'ligne_id': ligne.pk,
                'valeur': cellule.valeur if cellule else '',
            })
        matrice.append({
            'ligne': ligne,
            'valeurs': valeurs,
        })

    return render(request, 'eden/dashboard/apropos/tableau_editeur.html', {
        'tableau': tableau,
        'section': tableau.section,
        'colonnes': colonnes,
        'lignes': lignes,
        'matrice': matrice,  # ⬅️ NOUVEAU
    })

# ══════════════════════════════════════════════
# API AJAX — Colonnes / Lignes / Cellules
# ══════════════════════════════════════════════

@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_apropos_colonne_ajouter(request):
    from .models import AProposTableau, AProposColonne
    if request.method != 'POST':
        return JsonResponse({'success': False})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'})

    tableau_id = data.get('tableau_id')
    titre = data.get('titre', '').strip()

    if not tableau_id or not titre:
        return JsonResponse({'success': False, 'error': 'Titre requis'})

    tableau = get_object_or_404(AProposTableau, pk=tableau_id)
    ordre = tableau.colonnes.count()
    colonne = AProposColonne.objects.create(
        tableau=tableau, titre=titre, ordre=ordre
    )

    return JsonResponse({
        'success': True,
        'colonne': {
            'id': colonne.pk,
            'titre': colonne.titre,
            'ordre': colonne.ordre,
        }
    })


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_apropos_colonne_supprimer(request, pk):
    from .models import AProposColonne
    if request.method != 'POST':
        return JsonResponse({'success': False})

    colonne = get_object_or_404(AProposColonne, pk=pk)
    colonne.delete()

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_apropos_colonne_renommer(request, pk):
    from .models import AProposColonne
    if request.method != 'POST':
        return JsonResponse({'success': False})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})

    titre = data.get('titre', '').strip()
    if not titre:
        return JsonResponse({'success': False})

    colonne = get_object_or_404(AProposColonne, pk=pk)
    colonne.titre = titre
    colonne.save()

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_apropos_ligne_ajouter(request):
    from .models import AProposTableau, AProposLigne
    if request.method != 'POST':
        return JsonResponse({'success': False})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'})

    tableau_id = data.get('tableau_id')
    label = data.get('label', '').strip()

    if not tableau_id or not label:
        return JsonResponse({'success': False, 'error': 'Label requis'})

    tableau = get_object_or_404(AProposTableau, pk=tableau_id)
    ordre = tableau.lignes.count()
    ligne = AProposLigne.objects.create(
        tableau=tableau, label=label, ordre=ordre
    )

    return JsonResponse({
        'success': True,
        'ligne': {
            'id': ligne.pk,
            'label': ligne.label,
            'ordre': ligne.ordre,
        }
    })


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_apropos_ligne_supprimer(request, pk):
    from .models import AProposLigne
    if request.method != 'POST':
        return JsonResponse({'success': False})

    ligne = get_object_or_404(AProposLigne, pk=pk)
    ligne.delete()

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_apropos_ligne_renommer(request, pk):
    from .models import AProposLigne
    if request.method != 'POST':
        return JsonResponse({'success': False})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})

    label = data.get('label', '').strip()
    if not label:
        return JsonResponse({'success': False})

    ligne = get_object_or_404(AProposLigne, pk=pk)
    ligne.label = label
    ligne.save()

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
@user_passes_test(is_agent)
def api_apropos_cellule_sauvegarder(request):
    from .models import AProposLigne, AProposColonne, AProposCellule
    if request.method != 'POST':
        return JsonResponse({'success': False})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})

    ligne_id = data.get('ligne_id')
    colonne_id = data.get('colonne_id')
    valeur = str(data.get('valeur', '')).strip()

    if not ligne_id or not colonne_id:
        return JsonResponse({'success': False})

    try:
        ligne = AProposLigne.objects.get(pk=ligne_id)
        colonne = AProposColonne.objects.get(pk=colonne_id)
    except (AProposLigne.DoesNotExist, AProposColonne.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Ligne ou colonne introuvable'})

    cellule, created = AProposCellule.objects.update_or_create(
        ligne=ligne, colonne=colonne,
        defaults={'valeur': valeur}
    )

    return JsonResponse({'success': True, 'valeur': cellule.valeur})