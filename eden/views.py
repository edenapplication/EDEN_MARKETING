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

from .models import (
    SiteFoncier, ImageSite, Parcelle, ImageParcelle,
    Temoignage, DemandeContact, Reservation, VisiteProgrammee
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

def home(request):
    sites = SiteFoncier.objects.filter(is_active=True).prefetch_related('images', 'parcelles')
    temoignages = Temoignage.objects.filter(is_active=True).order_by('ordre', '-created_at')[:6]
    promos = Parcelle.objects.filter(is_active=True, en_promotion=True, statut='disponible').select_related('site')[:4]
    total_p = Parcelle.objects.filter(is_active=True).count()
    vendues = Parcelle.objects.filter(statut='vendue').count()
    stats = {
        'sites': SiteFoncier.objects.filter(is_active=True).count(),
        'vendues': vendues,
        'disponibles': Parcelle.objects.filter(statut='disponible').count(),
        'pourcentage': round((vendues / total_p * 100), 1) if total_p else 0,
    }
    if request.method == 'POST':
        form = DemandeContactForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ip_address = request.META.get('REMOTE_ADDR')
            obj.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Votre demande a ete envoyee !')
            return redirect('home')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': str(form.errors)})
    form = DemandeContactForm()
    return render(request, 'eden/home.html', {
        'sites': sites, 'temoignages': temoignages, 'promos': promos,
        'stats': stats, 'form': form, 'WHATSAPP_NUMBER': '237600000000',
    })


def sites_list(request):
    qs = SiteFoncier.objects.filter(is_active=True).prefetch_related('images', 'parcelles')
    q = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(ville__icontains=q) | Q(localisation__icontains=q))
    if statut:
        qs = qs.filter(statut=statut)
    villes = SiteFoncier.objects.filter(is_active=True).values_list('ville', flat=True).distinct()
    return render(request, 'eden/sites_list.html', {'sites': qs, 'villes': villes, 'q': q, 'statut': statut})


def site_detail(request, slug):
    site = get_object_or_404(SiteFoncier, slug=slug, is_active=True)
    parcelles = site.parcelles.filter(is_active=True).prefetch_related('images')
    similaires = SiteFoncier.objects.filter(is_active=True, ville=site.ville).exclude(id=site.id)[:3]
    form = DemandeContactForm(initial={'site': site})
    if request.method == 'POST':
        form = DemandeContactForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ip_address = request.META.get('REMOTE_ADDR')
            obj.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Demande envoyee !')
            return redirect('site_detail', slug=slug)
    return render(request, 'eden/site_detail.html', {
        'site': site, 'parcelles': parcelles, 'similaires': similaires, 'form': form,
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
    temoignages = Temoignage.objects.filter(is_active=True)
    return render(request, 'eden/a_propos.html', {'temoignages': temoignages})


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