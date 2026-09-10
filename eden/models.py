from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random
import string


class SiteFoncier(models.Model):
    STATUT_CHOICES = [
        ('disponible', '🟢 Terrain Disponible'),
        ('site_titre', '🔵 Terrain titré'),
        ('en_cours_immatriculation', '🟡 Terrain En cours d\'immatriculation'),
        ('titre_et_lotis', '🟣 Terrain Titré et lotis'),
        ('complet', '🔴 Complet'),
        ('prochainement', '🔷 Prochainement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=200, verbose_name="Nom du site")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(verbose_name="Description complete")
    description_courte = models.CharField(max_length=300, verbose_name="Description courte")
    localisation = models.CharField(max_length=200, verbose_name="Localisation")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    quartier = models.CharField(max_length=100, blank=True, verbose_name="Quartier")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    zoom_carte = models.PositiveSmallIntegerField(default=16)
    image_principale = models.ImageField(upload_to='sites/images/', blank=True, null=True, verbose_name="Image principale")
    video_drone = models.URLField(blank=True, verbose_name="Video drone (URL)")
    statut = models.CharField(max_length=40, choices=STATUT_CHOICES, default='disponible')
    prix_min = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="Prix minimum (FCFA)")
    prix_max = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="Prix maximum (FCFA)")
    superficie_totale = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Superficie totale",
        help_text="Ex: 2 500 m², 1.5 Ha, 500 m²"
    )
    
    # ═══ NOUVEAUX CHAMPS ═══
    morcellement = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Morcellement (m²)",
        help_text="Superficie minimale de morcellement en m²"
    )
    
    # ═══ CHAMP TEXTE LIBRE ═══
    popularite = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Popularité du site",
        help_text="Ex: Site du moment, Site en vogue, Site demandé, Site rare..."
    )
    superficie_minimale_affichage = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    null=True,
    blank=True,
    verbose_name="Superficie minimale d'affichage (m²)",
    help_text="À partir de cette superficie, le site apparaît dans les résultats."
)
    
    featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    en_promotion = models.BooleanField(default=False, verbose_name="En promotion")
    promotion_description = models.CharField(max_length=200, blank=True)
    promotion_fin = models.DateTimeField(null=True, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site foncier"
        verbose_name_plural = "Sites fonciers"
        ordering = ['ordre', '-featured', '-created_at']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.nom)
            slug = base
            counter = 1
            while SiteFoncier.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = "%s-%d" % (base, counter)
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def nb_parcelles_total(self):
        if hasattr(self, 'stats_manuelles') and self.stats_manuelles.total_parcelles_manuel > 0:
            return self.stats_manuelles.total_parcelles_manuel + self.parcelles.filter(is_active=True).count()
        return self.parcelles.filter(is_active=True).count()

    @property
    def nb_vendues(self):
        base = self.parcelles.filter(statut='vendue', is_active=True).count()
        if hasattr(self, 'stats_manuelles'):
            return self.stats_manuelles.vendues_manuel + base
        return base

    @property
    def nb_disponibles(self):
        base = self.parcelles.filter(statut='disponible', is_active=True).count()
        if hasattr(self, 'stats_manuelles'):
            return self.stats_manuelles.disponibles_manuel + base
        return base

    @property
    def nb_reservees(self):
        base = self.parcelles.filter(statut='reservee', is_active=True).count()
        if hasattr(self, 'stats_manuelles'):
            return self.stats_manuelles.reservees_manuel + base
        return base

    @property
    def pourcentage_vendu(self):
        total = self.nb_parcelles_total
        if total == 0:
            return 0
        return round((self.nb_vendues / total) * 100, 1)
    
    @property
    def prix_m2_max(self):
        try:
            sm = self.stats_manuelles
            if sm.prix_max and sm.superficie_max and sm.superficie_max > 0:
                return round(sm.prix_max / sm.superficie_max)
        except Exception:
            pass
        p = self.parcelles.filter(
            is_active=True, statut='disponible'
        ).order_by('-prix').first()
        if p and p.prix and p.superficie and p.superficie > 0:
            return round(p.prix / p.superficie)
        return 0
    
    @property
    def superficie_min_effective(self):
        if self.morcellement:
            return float(self.morcellement)
        try:
            sm = self.stats_manuelles
            if sm.superficie_min:
                return float(sm.superficie_min)
        except Exception:
            pass
        p = self.parcelles.filter(is_active=True).order_by('superficie').first()
        if p and p.superficie:
            return float(p.superficie)
        return 500.0

    @property
    def prix_min_effectif(self):
        if hasattr(self, 'stats_manuelles') and self.stats_manuelles.prix_min_manuel:
            return self.stats_manuelles.prix_min_manuel
        return self.prix_min

    @property
    def prix_max_effectif(self):
        if hasattr(self, 'stats_manuelles') and self.stats_manuelles.prix_max_manuel:
            return self.stats_manuelles.prix_max_manuel
        return self.prix_max

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('site_detail', kwargs={'slug': self.slug})
    @property
    def superficie_affichage(self):
        if self.superficie_minimale_affichage:
            return float(self.superficie_minimale_affichage)
        return float(self.morcellement or 0)


class ImageSite(models.Model):
    site = models.ForeignKey(SiteFoncier, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='sites/gallery/')
    legende = models.CharField(max_length=200, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', 'created_at']
        verbose_name = "Image du site"
        verbose_name_plural = "Images du site"

    def __str__(self):
        return "Image %d - %s" % (self.ordre, self.site.nom)


class Parcelle(models.Model):
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservee', 'Reservee'),
        ('vendue', 'Vendue'),
        ('indisponible', 'Indisponible'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(SiteFoncier, on_delete=models.CASCADE, related_name='parcelles', verbose_name="Site")
    numero = models.CharField(max_length=20, verbose_name="Numero de parcelle")
    superficie = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Superficie (m2)")
    longueur = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    largeur = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    prix = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Prix (FCFA)")
    prix_negocie = models.BooleanField(default=False, verbose_name="Prix negotiable")
    en_promotion = models.BooleanField(default=False, verbose_name="En promotion")
    prix_promo = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    promo_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    geojson = models.JSONField(null=True, blank=True, verbose_name="GeoJSON polygone")
    description = models.TextField(blank=True, verbose_name="Description")
    caracteristiques = models.JSONField(default=dict, blank=True)
    featured = models.BooleanField(default=False)
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parcelle"
        verbose_name_plural = "Parcelles"
        ordering = ['site', 'numero']
        unique_together = [['site', 'numero']]

    def __str__(self):
        return "Parcelle %s - %s" % (self.numero, self.site.nom)

    @property
    def prix_affiche(self):
        if self.en_promotion and self.prix_promo:
            return self.prix_promo
        return self.prix

    @property
    def reduction_pct(self):
        if self.en_promotion and self.prix_promo and self.prix > 0:
            return round(((self.prix - self.prix_promo) / self.prix) * 100)
        return 0

    @property
    def couleur_statut(self):
        colors = {
            'disponible': '#22c55e',
            'reservee': '#3b82f6',
            'vendue': '#ef4444',
            'indisponible': '#6b7280',
        }
        return colors.get(self.statut, '#6b7280')

    @property
    def prix_m2(self):
        if self.superficie and float(self.superficie) > 0:
            return round(float(self.prix_affiche) / float(self.superficie))
        return 0

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('parcelle_detail', kwargs={'site_slug': self.site.slug, 'numero': self.numero})


class ImageParcelle(models.Model):
    parcelle = models.ForeignKey(Parcelle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='parcelles/images/')
    legende = models.CharField(max_length=200, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Image parcelle"
        verbose_name_plural = "Images parcelle"

    def __str__(self):
        return "Image - Parcelle %s" % self.parcelle.numero


class Temoignage(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom du client")
    role = models.CharField(max_length=100, blank=True, verbose_name="Profession / Ville")
    avatar = models.ImageField(upload_to='temoignages/', blank=True, null=True)
    texte = models.TextField(verbose_name="Temoignage")
    note = models.PositiveSmallIntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    site = models.ForeignKey(SiteFoncier, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='temoignages')
    is_active = models.BooleanField(default=True, verbose_name="Visible")
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Temoignage"
        verbose_name_plural = "Temoignages"
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return "%s - %d etoiles" % (self.nom, self.note)


class DemandeContact(models.Model):
    TYPE_CHOICES = [
        ('achat', "Demande d'achat"),
        ('visite', 'Demande de visite'),
        ('information', "Demande d'information"),
        ('reservation', 'Reservation'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours'),
        ('traite', 'Traite'),
        ('ferme', 'Ferme'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    telephone = models.CharField(max_length=20, verbose_name="Telephone")
    whatsapp = models.CharField(max_length=20, blank=True)
    type_demande = models.CharField(max_length=20, choices=TYPE_CHOICES, default='information')
    message = models.TextField(verbose_name="Message")
    site = models.ForeignKey(SiteFoncier, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='demandes')
    parcelle = models.ForeignKey(Parcelle, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='demandes')
    budget = models.CharField(max_length=50, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='nouveau')
    notes_internes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Demande de contact"
        verbose_name_plural = "Demandes de contact"
        ordering = ['-created_at']

    def __str__(self):
        return "%s - %s" % (self.nom, self.get_type_demande_display())


class Reservation(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmee'),
        ('acompte_verse', 'Acompte verse'),
        ('payee', 'Entierement payee'),
        ('annulee', 'Annulee'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=20, unique=True, blank=True)
    parcelle = models.ForeignKey(Parcelle, on_delete=models.PROTECT, related_name='reservations')
    nom_client = models.CharField(max_length=150, verbose_name="Nom client")
    email_client = models.EmailField(verbose_name="Email client")
    telephone_client = models.CharField(max_length=20, verbose_name="Telephone")
    montant_total = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Montant total (FCFA)")
    montant_acompte = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ['-created_at']

    def __str__(self):
        return "Reservation %s - %s" % (self.reference, self.parcelle)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'EG-' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)


class VisiteProgrammee(models.Model):
    STATUT_CHOICES = [
        ('demandee', 'Demandee'),
        ('confirmee', 'Confirmee'),
        ('effectuee', 'Effectuee'),
        ('annulee', 'Annulee'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom_client = models.CharField(max_length=150)
    telephone_client = models.CharField(max_length=20)
    email_client = models.EmailField()
    site = models.ForeignKey(SiteFoncier, on_delete=models.CASCADE, related_name='visites')
    date_visite = models.DateTimeField()
    notes = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='demandee')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Visite programmee"
        verbose_name_plural = "Visites programmees"
        ordering = ['-date_visite']

    def __str__(self):
        return "Visite - %s - %s" % (self.nom_client, self.site.nom)
    
# ─────────────────────────────────────────────
# GROUPY — Base de connaissances chatbot
# ─────────────────────────────────────────────

class GroupyCategorie(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Catégorie")
    emoji = models.CharField(max_length=10, default="💬")
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Catégorie GROUPY"
        verbose_name_plural = "Catégories GROUPY"
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"{self.emoji} {self.nom}"


class GroupyQR(models.Model):
    """Question-Réponse pour GROUPY."""
    categorie = models.ForeignKey(
        GroupyCategorie, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='questions'
    )
    question = models.TextField(verbose_name="Question (ou variantes séparées par |)")
    reponse = models.TextField(verbose_name="Réponse")
    mots_cles = models.TextField(
        blank=True,
        verbose_name="Mots-clés déclencheurs (séparés par virgule)",
        help_text="Ex: prix, tarif, coût, combien"
    )
    priorite = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Priorité (plus haut = vérifié en premier)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    nb_utilisations = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Q&R GROUPY"
        verbose_name_plural = "Base de connaissances GROUPY"
        ordering = ['-priorite', '-nb_utilisations']

    def __str__(self):
        return self.question[:80]

    def get_mots_cles_list(self):
        if not self.mots_cles:
            return []
        return [m.strip().lower() for m in self.mots_cles.split(',') if m.strip()]

    def get_questions_list(self):
        return [q.strip().lower() for q in self.question.split('|') if q.strip()]
    
# ─────────────────────────────────────────────
# JOURNAL EDEN GROUP
# ─────────────────────────────────────────────
class JournalEdition(models.Model):
    TYPE_ACADEMIE_CHOICES = [
        ('journal', 'Journal EDEN'),
        ('article', 'Article Académie'),
        ('revue', 'Revue Académie'),
        ('guide', 'Guide Pratique'),
    ]

    titre = models.CharField(max_length=300)
    # ✅ CORRIGÉ : CharField unique, pas IntegerField
    numero = models.CharField(max_length=30, unique=True)
    sous_titre = models.CharField(max_length=400, blank=True)
    image_une = models.ImageField(upload_to='journal/unes/', null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=[('brouillon','Brouillon'),('publie','Publié'),('archive','Archivé')],
        default='brouillon'
    )
    date_parution = models.DateField(null=True, blank=True)
    type_academie = models.CharField(
        max_length=20,
        choices=TYPE_ACADEMIE_CHOICES,
        default='journal',
        verbose_name="Type de publication"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Édition Journal"
        verbose_name_plural = "Éditions Journal"
        ordering = ['-date_parution', '-created_at']

    def __str__(self):
        return f"[{self.get_type_academie_display()}] N°{self.numero} — {self.titre}"

    @property
    def nb_pages(self):
        return self.pages.count()


class JournalPage(models.Model):
    edition = models.ForeignKey(
        JournalEdition, on_delete=models.CASCADE, related_name='pages'
    )
    numero = models.PositiveSmallIntegerField(verbose_name="Numéro de page")
    contenu = models.JSONField(default=list, blank=True)
    layout = models.CharField(
        max_length=20,
        choices=[
            ('une', 'Une (pleine page)'),
            ('col1', '1 colonne'),
            ('col2', '2 colonnes'),
            ('col3', '3 colonnes'),
        ],
        default='col2'
    )
    couleur_fond = models.CharField(max_length=20, default='#FFFEF7')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['numero']
        unique_together = [['edition', 'numero']]
        verbose_name = "Page du journal"

    def __str__(self):
        return f"Page {self.numero} — {self.edition}"


class JournalMedia(models.Model):
    """Médiathèque — images et vidéos locales pour le journal."""
    TYPE_CHOICES = [('image', 'Image'), ('video', 'Vidéo locale')]

    edition = models.ForeignKey(
        JournalEdition, on_delete=models.CASCADE,
        null=True, blank=True, related_name='medias'
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='image')
    # ✅ CORRIGÉ : fichier local seulement, pas URL YouTube
    fichier = models.FileField(
        upload_to='journal/medias/',
        null=True, blank=True,
        help_text="Image (JPG/PNG) ou vidéo locale (MP4/WebM)"
    )
    legende = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Média journal"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} — {self.legende or str(self.fichier)}"

    @property
    def url(self):
        if self.fichier:
            return self.fichier.url
        return ''

    @property
    def est_video(self):
        return self.type == 'video'

class SiteStatistiquesManuelle(models.Model):
    """
    Permet de saisir manuellement les stats d'un site
    sans avoir à créer chaque parcelle individuellement.
    Pour les grands sites (20 000+ parcelles).
    """
    site = models.OneToOneField(
        SiteFoncier, on_delete=models.CASCADE,
        related_name='stats_manuelles'
    )
    # Compteurs manuels
    total_parcelles_manuel = models.PositiveIntegerField(
        default=0,
        verbose_name="Total parcelles (saisi manuellement)"
    )
    vendues_manuel = models.PositiveIntegerField(
        default=0, verbose_name="Parcelles vendues"
    )
    disponibles_manuel = models.PositiveIntegerField(
        default=0, verbose_name="Parcelles disponibles"
    )
    reservees_manuel = models.PositiveIntegerField(
        default=0, verbose_name="Parcelles réservées"
    )
    indisponibles_manuel = models.PositiveIntegerField(
        default=0, verbose_name="Parcelles indisponibles"
    )
    # Prix
    prix_min_manuel = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name="Prix minimum (FCFA)"
    )
    prix_max_manuel = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name="Prix maximum (FCFA)"
    )
    prix_moyen_manuel = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name="Prix moyen (FCFA)"
    )
    # Superficie
    superficie_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Superficie min (m²)"
    )
    superficie_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Superficie max (m²)"
    )
    # Notes
    notes = models.TextField(blank=True, verbose_name="Notes internes")
    derniere_maj = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Statistiques manuelles site"

    def __str__(self):
        return f"Stats manuelles — {self.site.nom}"

    @property
    def pourcentage_vendu(self):
        total = self.total_parcelles_manuel
        if total <= 0:
            return 0
        return round((self.vendues_manuel / total) * 100, 1)
    
# ─────────────────────────────────────────────
# HOME PAGE — Configuration admin complète
# ─────────────────────────────────────────────

class HeroConfig(models.Model):
    """Configuration du hero (bannière principale) — modifiable par l'admin."""
    image_fond = models.ImageField(
        upload_to='hero/', null=True, blank=True,
        verbose_name="Image de fond du hero"
    )
    eyebrow = models.CharField(
        max_length=200, blank=True,
        default="Plateforme Foncière N°1 — Afrique Centrale",
        verbose_name="Texte au-dessus du titre"
    )
    titre_ligne1 = models.CharField(
        max_length=200, blank=True,
        default="Investissez aujourd'hui",
        verbose_name="Titre ligne 1"
    )
    titre_ligne2 = models.CharField(
        max_length=200, blank=True,
        default="dans un avenir sécurisé.",
        verbose_name="Titre ligne 2 (accentuée en rouge)"
    )
    description = models.TextField(
        blank=True,
        default="EDEN GROUP vous accompagne dans l'acquisition, l'aménagement et la sécurisation de vos terrains avec professionnalisme et transparence.",
        verbose_name="Description sous le titre"
    )
    badge_site_nom = models.CharField(
        max_length=100, blank=True,
        default="Site : MVÉ 1",
        verbose_name="Nom du site dans le badge hero"
    )
    badge_site_lieu = models.CharField(
        max_length=100, blank=True,
        default="Yaoundé - voie de contournement",
        verbose_name="Lieu dans le badge hero"
    )
    btn1_texte = models.CharField(max_length=80, blank=True, default="Découvrir nos terrains")
    btn2_texte = models.CharField(max_length=80, blank=True, default="Visite des sites")
    updated_at = models.DateTimeField(auto_now=True)

    etapes_image = models.ImageField(
    upload_to='etapes/', null=True, blank=True,
    verbose_name="Image technicien (section étapes d'acquisition)"
    )

    class Meta:
        verbose_name = "Configuration Hero (page d'accueil)"

    def __str__(self):
        return "Configuration de la page d'accueil"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ServiceItem(models.Model):
    """Services affichés sur la page d'accueil (section 'Nos services')."""
    titre = models.CharField(max_length=150, verbose_name="Titre du service")
    description = models.TextField(verbose_name="Description")
    icone = models.CharField(
        max_length=10, default="🏡",
        verbose_name="Icône emoji",
        help_text="Ex: 🏡 🗺 🔒 ⚡ 📄"
    )
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['ordre']

    def __str__(self):
        return f"{self.icone} {self.titre}"


class EtapeAcquisition(models.Model):
    """Étapes du processus d'acquisition affichées sur la home."""
    numero = models.PositiveSmallIntegerField(verbose_name="Numéro d'étape")
    titre = models.CharField(max_length=100, verbose_name="Titre de l'étape")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description courte")
    couleur = models.CharField(
        max_length=20, default="blue",
        choices=[('blue', 'Bleu'), ('red', 'Rouge')],
        verbose_name="Couleur du cercle"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Étape d'acquisition"
        verbose_name_plural = "Étapes d'acquisition"
        ordering = ['numero']

    def __str__(self):
        return f"Étape {self.numero} — {self.titre}"


class SectionLivret(models.Model):
    """Section 'Livret de sécurité' configurable par l'admin."""
    titre_principal = models.CharField(
        max_length=200,
        default="Le Livret de Sécurité EDEN GROUP",
        verbose_name="Titre principal"
    )
    sous_titre = models.CharField(
        max_length=300, blank=True,
        default="Un système unique garantissant la sécurisation physique et numérique de tous vos documents fonciers.",
        verbose_name="Sous-titre"
    )
    image = models.ImageField(
        upload_to='livret/', null=True, blank=True,
        verbose_name="Image du livret"
    )
    badge_texte = models.CharField(
        max_length=100, blank=True,
        default="Notre engagement",
        verbose_name="Texte du badge"
    )
    btn_texte = models.CharField(
        max_length=80, blank=True,
        default="Découvrir le Livret",
        verbose_name="Texte du bouton"
    )
    btn_lien = models.CharField(
        max_length=200, blank=True, default="#",
        verbose_name="Lien du bouton"
    )
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Section Livret de Sécurité"

    def __str__(self):
        return "Section Livret de Sécurité"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class AvantagesLivret(models.Model):
    """Avantages listés dans la section Livret."""
    livret = models.ForeignKey(
        SectionLivret, on_delete=models.CASCADE,
        related_name='avantages'
    )
    texte = models.CharField(max_length=200, verbose_name="Avantage")
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Avantage du livret"
        verbose_name_plural = "Avantages du livret"

    def __str__(self):
        return self.texte


class ActualiteHome(models.Model):
    """Actualités & Événements affichés sur la page d'accueil."""
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description courte")
    image = models.ImageField(
        upload_to='actualites/', null=True, blank=True,
        verbose_name="Image"
    )
    date_evenement = models.DateField(null=True, blank=True, verbose_name="Date de l'événement")
    lien = models.CharField(max_length=200, blank=True, default="#", verbose_name="Lien 'En savoir plus'")
    is_active = models.BooleanField(default=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Actualité / Événement"
        verbose_name_plural = "Actualités & Événements"
        ordering = ['-date_evenement', 'ordre']

    def __str__(self):
        return self.titre


class CommentaireHome(models.Model):
    """Commentaires clients affichés sur la home (section 'Ils nous font confiance')."""
    nom = models.CharField(max_length=100, verbose_name="Nom du client")
    role = models.CharField(max_length=100, blank=True, verbose_name="Rôle / Ville")
    avatar = models.ImageField(
        upload_to='commentaires/', null=True, blank=True,
        verbose_name="Photo du client"
    )
    texte = models.TextField(verbose_name="Commentaire")
    note = models.PositiveSmallIntegerField(
        default=5, choices=[(i, i) for i in range(1, 6)],
        verbose_name="Note (étoiles)"
    )
    is_active = models.BooleanField(default=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Commentaire client (home)"
        verbose_name_plural = "Commentaires clients (home)"
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return f"{self.nom} — {self.note}★"


class StatistiqueHome(models.Model):
    """Statistiques affichées dans la bande chiffres-clés (20+, 10 000+, etc.)."""
    valeur = models.CharField(
        max_length=20, verbose_name="Valeur affichée",
        help_text="Ex: 20+, 10 000+, 100%, 50+"
    )
    label = models.CharField(max_length=80, verbose_name="Label")
    icone = models.CharField(max_length=10, blank=True, default="📊", verbose_name="Icône emoji")
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Statistique (bande chiffres)"
        verbose_name_plural = "Statistiques (bande chiffres)"
        ordering = ['ordre']

    def __str__(self):
        return f"{self.valeur} {self.label}"
    
class HeroSlide(models.Model):
    """Slides du carrousel hero — image de fond avec texte optionnel."""
    image = models.ImageField(upload_to='hero/slides/', verbose_name="Image de fond")
    titre = models.CharField(max_length=200, blank=True, verbose_name="Titre (optionnel)")
    sous_titre = models.CharField(max_length=300, blank=True, verbose_name="Sous-titre (optionnel)")
    is_active = models.BooleanField(default=True, verbose_name="Visible sur le site")
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Slide Hero"
        verbose_name_plural = "Slides Hero (carrousel)"
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return f"Slide {self.ordre} — {self.titre or self.image.name}"
    

# ─────────────────────────────────────────────
# MODULE UNE & ÉVÉNEMENTS
# ─────────────────────────────────────────────

class UneEvenementCategorie(models.TextChoices):
    UNE = 'une', 'À la Une'
    EVENEMENT_AVENIR = 'evenement_avenir', 'Événement à venir'
    EVENEMENT_PASSE = 'evenement_passe', 'Événement passé'
    ACTUALITE = 'actualite', 'Actualité'


class UneEvenement(models.Model):
    """Articles du module Une & Événements."""
    categorie = models.CharField(
        max_length=30,
        choices=UneEvenementCategorie.choices,
        default=UneEvenementCategorie.ACTUALITE,
        verbose_name="Catégorie"
    )
    titre = models.CharField(max_length=300, verbose_name="Titre")
    sous_titre = models.CharField(max_length=400, blank=True, verbose_name="Sous-titre / Accroche")
    image_couverture = models.ImageField(
        upload_to='une_evenements/couvertures/',
        null=True, blank=True,
        verbose_name="Image de couverture"
    )
    date_evenement = models.DateField(
        null=True, blank=True,
        verbose_name="Date de l'événement"
    )
    date_fin_evenement = models.DateField(
        null=True, blank=True,
        verbose_name="Date de fin (optionnel)"
    )
    lieu = models.CharField(max_length=200, blank=True, verbose_name="Lieu")
    statut = models.CharField(
        max_length=20,
        choices=[('brouillon', 'Brouillon'), ('publie', 'Publié'), ('archive', 'Archivé')],
        default='brouillon'
    )
    ordre = models.PositiveSmallIntegerField(default=0)
    contenu = models.JSONField(
        default=list, blank=True,
        verbose_name="Contenu de la page (blocs libres)"
    )
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='une_evenements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Une & Événement"
        verbose_name_plural = "Une & Événements"
        ordering = ['-date_evenement', '-created_at']

    def __str__(self):
        return f"[{self.get_categorie_display()}] {self.titre}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('une_evenement_detail', kwargs={'pk': self.pk})
    
# ─────────────────────────────────────────────
# MODULE NOS PROJETS
# ─────────────────────────────────────────────

class Projet(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('livre', 'Livré'),
        ('futur', 'Projet futur'),
    ]
    TYPE_CHOICES = [
        ('lotissement', 'Lotissement'),
        ('mini_cite', 'Mini-cité'),
        ('residence', 'Résidence'),
        ('autre', 'Autre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=200, verbose_name="Nom du projet")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    type_projet = models.CharField(max_length=20, choices=TYPE_CHOICES, default='lotissement')
    localisation = models.CharField(max_length=200, verbose_name="Localisation")
    description = models.TextField(verbose_name="Description")
    description_courte = models.CharField(max_length=300, blank=True)

    # Image principale
    image_principale = models.ImageField(upload_to='projets/images/', null=True, blank=True)

    # Informations principales
    superficie_totale = models.CharField(max_length=50, blank=True, verbose_name="Superficie totale")
    nb_lots = models.PositiveIntegerField(default=0, verbose_name="Nombre de lots")
    surface_lots = models.CharField(max_length=100, blank=True, verbose_name="Surface des lots")
    lots_disponibles = models.PositiveIntegerField(default=0)
    lots_reserves = models.PositiveIntegerField(default=0)
    lots_vendus = models.PositiveIntegerField(default=0)
    nb_proprietaires = models.PositiveIntegerField(default=0, verbose_name="Propriétaires")

    # Fichiers téléchargeables
    brochure = models.FileField(upload_to='projets/docs/', null=True, blank=True, verbose_name="Brochure PDF")
    plan_cadastral = models.FileField(upload_to='projets/docs/', null=True, blank=True)
    grille_tarifaire = models.FileField(upload_to='projets/docs/', null=True, blank=True)
    dossier_technique = models.FileField(upload_to='projets/docs/', null=True, blank=True)

    # Infos complémentaires
    annee_livraison = models.CharField(max_length=10, blank=True, verbose_name="Année de livraison")
    prix_min = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return f"{self.nom} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.nom)
            slug = base
            i = 1
            while Projet.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def taux_commercialisation(self):
        total = self.lots_disponibles + self.lots_reserves + self.lots_vendus
        if total == 0:
            return 0
        return round(((self.lots_reserves + self.lots_vendus) / total) * 100)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('projet_detail', kwargs={'slug': self.slug})


class ProjetImage(models.Model):
    """Galerie d'images d'un projet."""
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='galerie')
    image = models.ImageField(upload_to='projets/galerie/')
    legende = models.CharField(max_length=200, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Image galerie"

    def __str__(self):
        return f"Image {self.ordre} — {self.projet.nom}"


class ProjetInfrastructure(models.Model):
    """Infrastructures réalisées d'un projet."""
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='infrastructures')
    nom = models.CharField(max_length=150, verbose_name="Nom de l'infrastructure")
    is_realise = models.BooleanField(default=True, verbose_name="Réalisée")
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Infrastructure"

    def __str__(self):
        return f"{self.nom} ({'✓' if self.is_realise else '✗'}) — {self.projet.nom}"


class EtapeProjet(models.Model):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='etapes')
    nom = models.CharField(max_length=100, verbose_name="Nom de l'étape")
    description = models.TextField(blank=True, verbose_name="Description de l'étape")  # ← AJOUTEZ
    icone = models.CharField(max_length=10, default="🔵", verbose_name="Icône emoji")
    ordre = models.PositiveSmallIntegerField(default=0)
    couleur = models.CharField(max_length=20, default="#1B4FDB", verbose_name="Couleur (hex)")

    class Meta:
        ordering = ['ordre']
        verbose_name = "Grande étape"
        verbose_name_plural = "Grandes étapes"

    def __str__(self):
        return f"{self.nom} — {self.projet.nom}"

    @property
    def progression_globale(self):
        sous = self.sous_etapes.all()
        if not sous.exists():
            return 0
        return round(sum(s.avancement for s in sous) / sous.count())

class SousEtapeProjet(models.Model):
    """Sous-étape d'une grande étape (avec pourcentage d'avancement)."""
    etape = models.ForeignKey(EtapeProjet, on_delete=models.CASCADE, related_name='sous_etapes')
    nom = models.CharField(max_length=150, verbose_name="Nom de la sous-étape")
    avancement = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Avancement (%)",
        help_text="Entre 0 et 100"
    )
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Sous-étape"

    def __str__(self):
        return f"{self.nom} ({self.avancement}%) — {self.etape.nom}"
    

# ─────────────────────────────────────────────
# MODULE NOS AGENCES
# ─────────────────────────────────────────────

class Agence(models.Model):
    TYPE_CHOICES = [
        ('siege', 'Siège Social'),
        ('agence', 'Agence principale'),
        ('bureau', 'Bureau relais'),
    ]

    nom = models.CharField(max_length=200, verbose_name="Nom de l'agence")
    type_agence = models.CharField(max_length=20, choices=TYPE_CHOICES, default='agence')
    ville = models.CharField(max_length=100, verbose_name="Ville")
    adresse = models.CharField(max_length=300, verbose_name="Adresse complète")
    telephone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    whatsapp = models.CharField(max_length=30, blank=True, verbose_name="WhatsApp")
    email = models.CharField(max_length=150, blank=True, verbose_name="Email")
    horaires = models.CharField(
        max_length=200, blank=True,
        default="Lun - Sam : 8h00 - 17h00",
        verbose_name="Horaires"
    )
    image = models.ImageField(
        upload_to='agences/', null=True, blank=True,
        verbose_name="Photo de l'agence"
    )
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="Latitude GPS"
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="Longitude GPS"
    )
    lien_itineraire = models.URLField(
        blank=True,
        verbose_name="Lien Google Maps itinéraire"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Agence"
        verbose_name_plural = "Agences"
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return f"{self.get_type_agence_display()} — {self.nom}"

    @property
    def badge_label(self):
        labels = {
            'siege': 'SIÈGE SOCIAL',
            'agence': 'AGENCE',
            'bureau': 'BUREAU RELAIS',
        }
        return labels.get(self.type_agence, 'AGENCE')

    @property
    def badge_color(self):
        colors = {
            'siege': '#C8102E',
            'agence': '#1B4FDB',
            'bureau': '#7B20B4',
        }
        return colors.get(self.type_agence, '#1B4FDB')


class AgenceService(models.Model):
    """Services proposés par une agence."""
    agence = models.ForeignKey(Agence, on_delete=models.CASCADE, related_name='services')
    nom = models.CharField(max_length=150, verbose_name="Service")
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"{self.nom} — {self.agence.nom}"


class StatAgence(models.Model):
    """Statistiques globales EDEN GROUP en chiffres."""
    valeur = models.CharField(max_length=20, verbose_name="Valeur (ex: 3, 7+, 50+)")
    label = models.CharField(max_length=100, verbose_name="Label")
    icone = models.CharField(max_length=10, default="🏢", verbose_name="Icône emoji")
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Statistique agence"

    def __str__(self):
        return f"{self.valeur} {self.label}"
    
# ─────────────────────────────────────────────
# MODULE NOS SERVICES
# ─────────────────────────────────────────────

class ServiceCategorie(models.Model):
    """Catégorie/domaine de service (menu gauche)."""
    nom = models.CharField(max_length=150, verbose_name="Nom")
    icone = models.CharField(max_length=10, default="🔵", verbose_name="Icône emoji")
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Catégorie de service"
        verbose_name_plural = "Catégories de services"
        ordering = ['ordre']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class Service(models.Model):
    """Un service proposé par EDEN GROUP."""
    categorie = models.ForeignKey(
        ServiceCategorie, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='services',
        verbose_name="Catégorie"
    )
    numero = models.PositiveSmallIntegerField(
        default=0, verbose_name="Numéro (affiché)"
    )
    nom = models.CharField(max_length=200, verbose_name="Nom du service")
    icone = models.CharField(max_length=10, default="🏠", verbose_name="Icône emoji")
    description = models.TextField(verbose_name="Description")
    description_longue = models.TextField(
        blank=True, verbose_name="Description longue (page détail)"
    )
    image = models.ImageField(
        upload_to='services/', null=True, blank=True,
        verbose_name="Image du service"
    )
    lien_detail = models.CharField(
        max_length=200, blank=True, default="#",
        verbose_name="Lien 'En savoir plus'"
    )
    is_active = models.BooleanField(default=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['ordre', 'numero']

    def __str__(self):
        return f"{self.numero:02d}. {self.nom}"


class EtapeProcessus(models.Model):
    """Étapes du processus d'accompagnement (section milieu de page)."""
    numero = models.PositiveSmallIntegerField(default=0)
    titre = models.CharField(max_length=150, verbose_name="Titre de l'étape")
    description = models.CharField(max_length=300, blank=True, verbose_name="Description courte")
    icone = models.CharField(max_length=10, default="✅", verbose_name="Icône emoji")
    is_active = models.BooleanField(default=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Étape du processus"
        verbose_name_plural = "Étapes du processus"
        ordering = ['ordre', 'numero']

    def __str__(self):
        return f"{self.numero}. {self.titre}"


class EngagementService(models.Model):
    """Engagements EDEN GROUP (bande du bas)."""
    icone = models.CharField(max_length=10, default="🔒", verbose_name="Icône emoji")
    titre = models.CharField(max_length=150, verbose_name="Titre")
    description = models.CharField(max_length=300, verbose_name="Description")
    couleur = models.CharField(
        max_length=20, default="blue",
        choices=[('blue','Bleu'),('red','Rouge'),('green','Vert'),('purple','Violet')],
        verbose_name="Couleur de l'icône"
    )
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Engagement"
        verbose_name_plural = "Engagements"
        ordering = ['ordre']

    def __str__(self):
        return self.titre
    
# ─────────────────────────────────────────────
# MODULE ACADÉMIE EDEN GROUP
# ─────────────────────────────────────────────

class AcademieCategorie(models.TextChoices):
    TEXTE_LOI = 'texte_loi', 'Textes de loi'
    LEXIQUE = 'lexique', 'Lexique du foncier'
    VIDEO = 'video', 'Vidéothèque'
    GALERIE = 'galerie', 'Galerie'
    FAQ = 'faq', 'Questions fréquentes'
    RESSOURCE = 'ressource', 'Centre de ressources'


class AcademieDocument(models.Model):
    """Textes de loi, lexique, ressources — PAS les articles/revues/guides (= Journal)."""
    categorie = models.CharField(
        max_length=30,
        choices=AcademieCategorie.choices,
        default=AcademieCategorie.TEXTE_LOI,
        verbose_name="Catégorie"
    )
    titre = models.CharField(max_length=300, verbose_name="Titre")
    sous_titre = models.CharField(max_length=400, blank=True)
    description = models.TextField(blank=True)
    image_couverture = models.ImageField(
        upload_to='academie/couvertures/', null=True, blank=True
    )
    fichier_pdf = models.FileField(
        upload_to='academie/documents/', null=True, blank=True,
        verbose_name="Fichier PDF (textes de loi)"
    )
    auteur = models.CharField(max_length=200, blank=True)
    date_publication = models.DateField(null=True, blank=True)
    nb_pages = models.PositiveIntegerField(null=True, blank=True)
    temps_lecture = models.CharField(max_length=30, blank=True)
    reference_officielle = models.CharField(max_length=300, blank=True)
    # Pour galerie : titre + image + description
    lien_externe = models.URLField(blank=True, verbose_name="Lien externe (optionnel)")
    statut = models.CharField(
        max_length=20,
        choices=[('brouillon','Brouillon'),('publie','Publié'),('archive','Archivé')],
        default='brouillon'
    )
    est_a_la_une = models.BooleanField(default=False)
    est_featured = models.BooleanField(default=False)
    nb_telechargements = models.PositiveIntegerField(default=0)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document Académie"
        verbose_name_plural = "Documents Académie"
        ordering = ['-date_publication', '-created_at']

    def __str__(self):
        return f"[{self.get_categorie_display()}] {self.titre}"

    def incrementer_telechargements(self):
        self.nb_telechargements += 1
        self.save(update_fields=['nb_telechargements'])


class AcademieVideo(models.Model):
    """Vidéo de la vidéothèque."""
    titre = models.CharField(max_length=300, verbose_name="Titre")
    description = models.TextField(blank=True)
    fichier_video = models.FileField(
        upload_to='academie/videos/',
        verbose_name="Fichier vidéo"
    )
    image_miniature = models.ImageField(
        upload_to='academie/miniatures/',
        null=True, blank=True,
        verbose_name="Miniature / Vignette"
    )
    duree = models.CharField(max_length=20, blank=True, verbose_name="Durée (ex: 08:34)")
    auteur = models.CharField(max_length=200, blank=True)
    date_publication = models.DateField(null=True, blank=True)
    est_video_moment = models.BooleanField(default=False, verbose_name="Vidéo du moment")
    statut = models.CharField(
        max_length=20,
        choices=[('brouillon','Brouillon'),('publie','Publié')],
        default='brouillon'
    )
    nb_vues = models.PositiveIntegerField(default=0)
    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vidéo Académie"
        verbose_name_plural = "Vidéos Académie"
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return self.titre


class AcademieEtapeParcours(models.Model):
    """Étapes du parcours de l'investisseur."""
    numero = models.PositiveSmallIntegerField()
    titre = models.CharField(max_length=150)
    icone = models.CharField(max_length=10, default="📋")
    description = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'numero']
        verbose_name = "Étape parcours"

    def __str__(self):
        return f"{self.numero}. {self.titre}"


class AcademieFAQ(models.Model):
    """Question / Réponse fréquente."""
    question = models.CharField(max_length=400)
    reponse = models.TextField()
    categorie_faq = models.CharField(max_length=100, blank=True, verbose_name="Catégorie FAQ")
    temps_reponse = models.CharField(max_length=100, blank=True, verbose_name="Temps estimé")
    est_featured = models.BooleanField(default=False, verbose_name="Question featured")
    ordre = models.PositiveSmallIntegerField(default=0)
    statut = models.CharField(
        max_length=20,
        choices=[('brouillon','Brouillon'),('publie','Publié')],
        default='publie'
    )

    class Meta:
        ordering = ['ordre', '-id']
        verbose_name = "FAQ"

    def __str__(self):
        return self.question[:80]


class AcademieStatistique(models.Model):
    """Statistiques affichées en haut de la page Académie."""
    valeur = models.CharField(max_length=20, verbose_name="Valeur (ex: 150+)")
    label = models.CharField(max_length=100, verbose_name="Label")
    icone = models.CharField(max_length=10, default="📋")
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Statistique Académie"

    def __str__(self):
        return f"{self.valeur} {self.label}"


# Dans eden/models.py

class VideoGlobale(models.Model):
    titre = models.CharField(max_length=200, verbose_name="Titre")
    video = models.FileField(
        upload_to='videos/globale/', 
        verbose_name="Fichier vidéo",
        help_text="Formats acceptés : MP4, WebM"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activer l'affichage")
    position = models.CharField(
        max_length=20,
        choices=[
            ('bottom-right', 'En bas à droite'),
            ('bottom-left', 'En bas à gauche'),
            ('top-right', 'En haut à droite'),
            ('top-left', 'En haut à gauche'),
        ],
        default='bottom-right',
        verbose_name="Position à l'écran"
    )
    largeur = models.PositiveIntegerField(
        default=500, 
        verbose_name="Largeur (px)",
        help_text="Largeur de la vidéo en pixels"
    )
    # ✅ NOUVEAU CHAMP HAUTEUR
    hauteur = models.PositiveIntegerField(
        default=280,
        verbose_name="Hauteur (px)",
        help_text="Hauteur de la vidéo en pixels"
    )
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vidéo globale"
        verbose_name_plural = "Vidéos globales"
        ordering = ['ordre']

    def __str__(self):
        return f"{self.titre} ({'Active' if self.is_active else 'Inactive'}) - {self.largeur}x{self.hauteur}"