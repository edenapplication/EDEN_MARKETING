from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random
import string


class SiteFoncier(models.Model):
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('en_cours', 'En cours de vente'),
        ('complet', 'Complet'),
        ('prochainement', 'Prochainement'),
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
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')
    prix_min = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="Prix minimum (FCFA)")
    prix_max = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="Prix maximum (FCFA)")
    superficie_totale = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
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
        return self.parcelles.filter(is_active=True).count()

    @property
    def nb_vendues(self):
        return self.parcelles.filter(statut='vendue', is_active=True).count()

    @property
    def nb_disponibles(self):
        return self.parcelles.filter(statut='disponible', is_active=True).count()

    @property
    def nb_reservees(self):
        return self.parcelles.filter(statut='reservee', is_active=True).count()

    @property
    def pourcentage_vendu(self):
        total = self.nb_parcelles_total
        if total == 0:
            return 0
        return round((self.nb_vendues / total) * 100, 1)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('site_detail', kwargs={'slug': self.slug})


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