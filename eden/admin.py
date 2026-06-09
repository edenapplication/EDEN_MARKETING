from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteFoncier, ImageSite, Parcelle, ImageParcelle,
    Temoignage, DemandeContact, Reservation, VisiteProgrammee, GroupyCategorie, GroupyQR
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