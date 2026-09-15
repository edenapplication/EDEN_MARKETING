from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteFoncier, ImageSite, Parcelle, ImageParcelle,
    Temoignage, DemandeContact, Reservation, VisiteProgrammee, GroupyCategorie, GroupyQR, HeroConfig, ServiceItem, EtapeAcquisition,
    SectionLivret, AvantagesLivret, ActualiteHome,
    CommentaireHome, StatistiqueHome,AProposSection, AProposElement, AProposIndicateur,
        AProposTableau, AProposColonne, AProposLigne, AProposCellule,
        AProposEtape,
)


class ImageSiteInline(admin.TabularInline):
    model = ImageSite
    extra = 2
    fields = ['image', 'legende', 'ordre']


@admin.register(SiteFoncier)
class SiteFoncierAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ville', 'statut_color', 'pct_badge', 'nb_disponibles',
                    'prix_min', 'featured', 'en_promotion', 'is_active']
    list_filter = ['statut', 'ville', 'featured', 'en_promotion', 'is_active']
    search_fields = ['nom', 'localisation', 'ville']
    prepopulated_fields = {'slug': ('nom',)}
    readonly_fields = ['created_at', 'updated_at', 'pourcentage_vendu',
                       'nb_vendues', 'nb_disponibles', 'nb_reservees']
    inlines = [ImageSiteInline]
    list_editable = ['featured', 'is_active']

    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'slug', 'description', 'description_courte', 'statut', 'featured', 'ordre', 'is_active')
        }),
        ('Localisation', {
            'fields': ('localisation', 'ville', 'quartier', 'latitude', 'longitude', 'zoom_carte')
        }),
        ('Medias', {
            'fields': ('image_principale', 'video_drone')
        }),
        ('Tarification', {
            'fields': ('prix_min', 'prix_max', 'superficie_totale')
        }),
        ('Promotion', {
            'fields': ('en_promotion', 'promotion_description', 'promotion_fin'),
            'classes': ('collapse',)
        }),
        ('Statistiques auto', {
            'fields': ('pourcentage_vendu', 'nb_vendues', 'nb_disponibles', 'nb_reservees'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def statut_color(self, obj):
        c = {
            'disponible': '#16a34a', 'en_cours': '#d97706',
            'complet': '#dc2626', 'prochainement': '#2563eb'
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            c.get(obj.statut, '#000'), obj.get_statut_display()
        )
    statut_color.short_description = 'Statut'

    def pct_badge(self, obj):
        p = obj.pourcentage_vendu
        c = '#16a34a' if p < 50 else '#d97706' if p < 80 else '#dc2626'
        return format_html('<b style="color:{}">{:.1f}%</b>', c, p)
    pct_badge.short_description = '% vendu'


class ImageParcelleInline(admin.TabularInline):
    model = ImageParcelle
    extra = 2


@admin.register(Parcelle)
class ParcelleAdmin(admin.ModelAdmin):
    list_display = ['numero', 'site', 'superficie', 'prix_display', 'statut_color',
                    'en_promotion', 'geojson_ok', 'is_active','statut']
    list_filter = ['statut', 'site', 'en_promotion', 'is_active']
    search_fields = ['numero', 'site__nom']
    list_editable = ['statut', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'prix_m2', 'reduction_pct']
    inlines = [ImageParcelleInline]

    fieldsets = (
        ('Identification', {
            'fields': ('site', 'numero', 'statut', 'description', 'is_active', 'featured', 'ordre')
        }),
        ('Dimensions', {
            'fields': ('superficie', 'longueur', 'largeur')
        }),
        ('Tarification', {
            'fields': ('prix', 'prix_negocie', 'en_promotion', 'prix_promo', 'promo_fin', 'prix_m2', 'reduction_pct')
        }),
        ('Cartographie', {
            'fields': ('latitude', 'longitude', 'geojson')
        }),
        ('Caracteristiques', {
            'fields': ('caracteristiques',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def statut_color(self, obj):
        c = {
            'disponible': '#16a34a', 'reservee': '#2563eb',
            'vendue': '#dc2626', 'indisponible': '#6b7280'
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            c.get(obj.statut, '#000'), obj.get_statut_display()
        )
    statut_color.short_description = 'Statut'

    def prix_display(self, obj):
        return format_html('{:,.0f} FCFA', float(obj.prix_affiche))
    prix_display.short_description = 'Prix'

    def geojson_ok(self, obj):
        return format_html('✅' if obj.geojson else '—')
    geojson_ok.short_description = 'GeoJSON'


@admin.register(Temoignage)
class TemoignageAdmin(admin.ModelAdmin):
    list_display = ['nom', 'role', 'note', 'site', 'is_active', 'ordre']
    list_filter = ['note', 'is_active']
    list_editable = ['is_active', 'ordre']


@admin.register(DemandeContact)
class DemandeContactAdmin(admin.ModelAdmin):
    list_display = ['nom', 'email', 'telephone', 'type_demande', 'statut', 'site', 'created_at']
    list_filter = ['type_demande', 'statut', 'created_at']
    search_fields = ['nom', 'email', 'telephone']
    list_editable = ['statut']
    readonly_fields = ['created_at', 'updated_at', 'ip_address']
    date_hierarchy = 'created_at'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reference', 'nom_client', 'telephone_client', 'parcelle', 'montant_total', 'statut', 'created_at']
    list_filter = ['statut', 'created_at']
    search_fields = ['reference', 'nom_client', 'email_client']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(VisiteProgrammee)
class VisiteProgrammeeAdmin(admin.ModelAdmin):
    list_display = ['nom_client', 'telephone_client', 'site', 'date_visite', 'statut']
    list_filter = ['statut', 'site']
    ordering = ['-date_visite']



@admin.register(GroupyCategorie)
class GroupyCategorieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'emoji', 'ordre', 'is_active']
    list_editable = ['ordre', 'is_active']


@admin.register(GroupyQR)
class GroupyQRAdmin(admin.ModelAdmin):
    list_display = ['question_courte', 'categorie', 'priorite', 'nb_utilisations', 'is_active', 'updated_at']
    list_filter = ['categorie', 'is_active']
    list_editable = ['priorite', 'is_active']
    search_fields = ['question', 'reponse', 'mots_cles']
    readonly_fields = ['nb_utilisations', 'created_at', 'updated_at']

    fieldsets = (
        ('Question', {'fields': ('question', 'categorie', 'priorite', 'is_active')}),
        ('Réponse', {'fields': ('reponse',)}),
        ('Déclencheurs', {'fields': ('mots_cles',), 'description': 'Mots-clés séparés par virgule. Ex: prix, tarif, combien, coût'}),
        ('Stats', {'fields': ('nb_utilisations', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def question_courte(self, obj):
        return obj.question[:60] + '...' if len(obj.question) > 60 else obj.question
    question_courte.short_description = 'Question'

# ─────────────────────────────────────────────
# ADMIN — Home page configurables
# ─────────────────────────────────────────────
@admin.register(HeroConfig)
class HeroConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('🖼 Image de fond', {
            'description': 'Cette image prend toute la largeur de la page et la barre de navigation est par-dessus.',
            'fields': ('image_fond',)
        }),
        ('✏ Textes du hero', {
            'fields': ('eyebrow', 'titre_ligne1', 'titre_ligne2', 'description')
        }),
        ('📌 Badge hero (coin haut droite)', {
            'fields': ('badge_site_nom', 'badge_site_lieu')
        }),
        ('🔘 Boutons', {
            'fields': ('btn1_texte', 'btn2_texte')
        }),
    )

    def has_add_permission(self, request):
        return not HeroConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ['icone', 'titre', 'ordre', 'is_active']
    list_editable = ['ordre', 'is_active']
    list_display_links = ['titre']


@admin.register(EtapeAcquisition)
class EtapeAcquisitionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'titre', 'description', 'couleur', 'is_active']
    list_editable = ['is_active']
    ordering = ['numero']


class AvantagesLivretInline(admin.TabularInline):
    model = AvantagesLivret
    extra = 3
    fields = ['texte', 'ordre']


@admin.register(SectionLivret)
class SectionLivretAdmin(admin.ModelAdmin):
    inlines = [AvantagesLivretInline]
    fieldsets = (
        ('Textes', {'fields': ('badge_texte', 'titre_principal', 'sous_titre')}),
        ('Image', {'fields': ('image',)}),
        ('Bouton', {'fields': ('btn_texte', 'btn_lien')}),
        ('Visibilité', {'fields': ('is_active',)}),
    )

    def has_add_permission(self, request):
        return not SectionLivret.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ActualiteHome)
class ActualiteHomeAdmin(admin.ModelAdmin):
    list_display = ['titre', 'date_evenement', 'ordre', 'is_active']
    list_editable = ['ordre', 'is_active']
    list_filter = ['is_active']
    search_fields = ['titre']


@admin.register(CommentaireHome)
class CommentaireHomeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'role', 'note', 'ordre', 'is_active']
    list_editable = ['ordre', 'is_active']
    list_filter = ['note', 'is_active']


@admin.register(StatistiqueHome)
class StatistiqueHomeAdmin(admin.ModelAdmin):
    list_display = ['icone', 'valeur', 'label', 'ordre', 'is_active']
    list_editable = ['ordre', 'is_active']



# ══════════════════════════════════════════════
# INLINES
# ══════════════════════════════════════════════

class AProposElementInline(admin.TabularInline):
    model = AProposElement
    extra = 1
    fields = ('ordre', 'icone', 'initiales', 'titre', 'sous_titre', 'description', 'is_active')
    ordering = ['ordre']


class AProposIndicateurInline(admin.TabularInline):
    model = AProposIndicateur
    extra = 1
    fields = ('ordre', 'icone', 'nombre', 'suffixe', 'label', 'is_active')
    ordering = ['ordre']


class AProposEtapeInline(admin.TabularInline):
    model = AProposEtape
    extra = 1
    fields = ('ordre', 'annee', 'description', 'position', 'is_active')
    ordering = ['ordre']


class AProposColonneInline(admin.TabularInline):
    model = AProposColonne
    extra = 1
    fields = ('ordre', 'titre')
    ordering = ['ordre']


class AProposLigneInline(admin.TabularInline):
    model = AProposLigne
    extra = 1
    fields = ('ordre', 'label')
    ordering = ['ordre']


# ══════════════════════════════════════════════
# ADMIN SECTION (point d'entrée principal)
# ══════════════════════════════════════════════

@admin.register(AProposSection)
class AProposSectionAdmin(admin.ModelAdmin):
    list_display = ('type_section_display', 'titre', 'ordre', 'is_active', 'updated_at')
    list_editable = ('ordre', 'is_active')
    ordering = ['ordre']
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Type de section', {
            'fields': ('type_section', 'ordre', 'is_active')
        }),
        ('Contenu', {
            'fields': ('titre', 'titre_accent', 'description')
        }),
    )

    def type_section_display(self, obj):
        return obj.get_type_section_display()
    type_section_display.short_description = "Section"

    def get_inlines(self, request, obj=None):
        """Retourner les inlines adaptés au type de section."""
        if not obj:
            return []

        if obj.type_section in ('presentation', 'activites', 'valeurs', 'equipe'):
            return [AProposElementInline]
        elif obj.type_section == 'histoire':
            return [AProposEtapeInline]
        elif obj.type_section == 'chiffres':
            return [AProposIndicateurInline]

        return []

    class Media:
        css = {'all': ('admin/css/apropos.css',)}


# ══════════════════════════════════════════════
# ADMIN TABLEAUX
# ══════════════════════════════════════════════

@admin.register(AProposTableau)
class AProposTableauAdmin(admin.ModelAdmin):
    list_display = ('titre', 'section', 'est_pour_graphique', 'ordre', 'nb_colonnes', 'nb_lignes')
    list_filter = ('section', 'est_pour_graphique')
    list_editable = ('ordre',)
    inlines = [AProposColonneInline, AProposLigneInline]
    ordering = ['section', 'ordre']

    fieldsets = (
        ('Informations', {
            'fields': ('section', 'titre', 'est_pour_graphique', 'ordre')
        }),
        ('💡 Comment ça marche ?', {
            'fields': (),
            'description': (
                '<strong>Ajoutez d\'abord les colonnes</strong> (ex: Année 1, Année 2, En cours...) '
                'puis les <strong>lignes</strong> (ex: Production, Encours...).<br>'
                'Ensuite <a href="/admin/eden/aproposcellule/add/" target="_blank">cliquez ici '
                'pour remplir les cellules</a> avec les valeurs.'
            )
        }),
    )

    def nb_colonnes(self, obj):
        return obj.colonnes.count()
    nb_colonnes.short_description = "Colonnes"

    def nb_lignes(self, obj):
        return obj.lignes.count()
    nb_lignes.short_description = "Lignes"


@admin.register(AProposCellule)
class AProposCelluleAdmin(admin.ModelAdmin):
    list_display = ('ligne', 'colonne', 'valeur')
    list_filter = ('ligne__tableau', 'colonne__tableau')
    search_fields = ('ligne__label', 'colonne__titre', 'valeur')
    ordering = ['ligne__tableau', 'ligne__ordre', 'colonne__ordre']

    fieldsets = (
        ('Cellule', {
            'fields': ('ligne', 'colonne', 'valeur')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filtrer les colonnes en fonction de la ligne
        if db_field.name == 'colonne':
            ligne_id = request.GET.get('ligne')
            if ligne_id:
                try:
                    ligne = AProposLigne.objects.get(pk=ligne_id)
                    kwargs['queryset'] = AProposColonne.objects.filter(tableau=ligne.tableau)
                except AProposLigne.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ══════════════════════════════════════════════
# ADMIN INDIVIDUELS (accès direct)
# ══════════════════════════════════════════════

@admin.register(AProposElement)
class AProposElementAdmin(admin.ModelAdmin):
    list_display = ('section', 'ordre', 'icone', 'titre', 'is_active')
    list_filter = ('section', 'is_active')
    list_editable = ('ordre', 'is_active')
    search_fields = ('titre', 'description')
    ordering = ['section', 'ordre']


@admin.register(AProposIndicateur)
class AProposIndicateurAdmin(admin.ModelAdmin):
    list_display = ('section', 'ordre', 'icone', 'nombre', 'suffixe', 'label', 'is_active')
    list_filter = ('section', 'is_active')
    list_editable = ('ordre', 'is_active')
    ordering = ['ordre']


@admin.register(AProposEtape)
class AProposEtapeAdmin(admin.ModelAdmin):
    list_display = ('section', 'ordre', 'annee', 'position', 'is_active')
    list_filter = ('section', 'position', 'is_active')
    list_editable = ('ordre', 'is_active')
    ordering = ['ordre']


# ══════════════════════════════════════════════
# HEADER PERSONNALISÉ
# ══════════════════════════════════════════════

admin.site.site_header = "EDEN GROUP — Administration"
admin.site.site_title = "EDEN GROUP Admin"
admin.site.index_title = "Gestion du contenu"

# Réorganiser le menu admin
admin.site.index_template = 'admin/custom_index.html'