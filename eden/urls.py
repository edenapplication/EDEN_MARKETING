from django.urls import path
from . import views

urlpatterns = [
    # ── PAGES PUBLIQUES ──
    path('', views.home, name='home'),
    path('sites/', views.sites_list, name='sites_list'),
    path('sites/<slug:slug>/', views.site_detail, name='site_detail'),
    path('carte/', views.carte, name='carte'),
    path('promotions/', views.promotions, name='promotions'),
    path('a-propos/', views.a_propos, name='a_propos'),
    path('contact/', views.contact, name='contact'),
    path('sites/<slug:site_slug>/parcelle/<str:numero>/', views.parcelle_detail, name='parcelle_detail'),
    path('reserver/<uuid:parcelle_id>/', views.reserver, name='reserver'),
    path('visite/', views.demande_visite, name='demande_visite'),

    # ── API ──
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/sites-geo/', views.api_sites_geo, name='api_sites_geo'),
    path('api/parcelles-geo/', views.api_parcelles_geo, name='api_parcelles_geo'),
    path('api/recherche/', views.api_recherche, name='api_recherche'),
    path('api/geo-import/', views.api_geo_import, name='api_geo_import'),
    path('api/groupy/', views.api_groupy, name='api_groupy'),

    # ── DASHBOARD ──
    path('dashboard/', views.dashboard_home, name='dashboard_home'),

    # Sites
    path('dashboard/sites/', views.dashboard_sites, name='dashboard_sites'),
    path('dashboard/sites/ajouter/', views.dashboard_site_form, name='dashboard_site_ajouter'),
    path('dashboard/sites/<uuid:pk>/modifier/', views.dashboard_site_form, name='dashboard_site_modifier'),
    path('dashboard/sites/<uuid:pk>/supprimer/', views.dashboard_site_supprimer, name='dashboard_site_supprimer'),
    path('dashboard/sites/<uuid:pk>/toggle-active/', views.dashboard_site_toggle, name='dashboard_site_toggle'),
    path('dashboard/sites/image/<int:pk>/supprimer/', views.dashboard_image_site_supprimer, name='dashboard_image_site_supprimer'),

    # Parcelles
    path('dashboard/parcelles/', views.dashboard_parcelles, name='dashboard_parcelles'),
    path('dashboard/parcelles/ajouter/', views.dashboard_parcelle_form, name='dashboard_parcelle_ajouter'),
    path('dashboard/parcelles/<uuid:pk>/modifier/', views.dashboard_parcelle_form, name='dashboard_parcelle_modifier'),
    path('dashboard/parcelles/<uuid:pk>/supprimer/', views.dashboard_parcelle_supprimer, name='dashboard_parcelle_supprimer'),
    path('dashboard/parcelles/<uuid:pk>/statut/', views.dashboard_parcelle_statut, name='dashboard_parcelle_statut'),
    path('dashboard/parcelles/image/<int:pk>/supprimer/', views.dashboard_image_parcelle_supprimer, name='dashboard_image_parcelle_supprimer'),

    # Réservations
    path('dashboard/reservations/', views.dashboard_reservations, name='dashboard_reservations'),
    path('dashboard/reservations/<uuid:pk>/', views.dashboard_reservation_detail, name='dashboard_reservation_detail'),
    path('dashboard/reservations/<uuid:pk>/supprimer/', views.dashboard_reservation_supprimer, name='dashboard_reservation_supprimer'),

    # Contacts
    path('dashboard/contacts/', views.dashboard_contacts, name='dashboard_contacts'),
    path('dashboard/contacts/<uuid:pk>/', views.dashboard_contact_detail, name='dashboard_contact_detail'),
    path('dashboard/contacts/<uuid:pk>/supprimer/', views.dashboard_contact_supprimer, name='dashboard_contact_supprimer'),

    # Visites
    path('dashboard/visites/', views.dashboard_visites, name='dashboard_visites'),
    path('dashboard/visites/ajouter/', views.dashboard_visite_form, name='dashboard_visite_ajouter'),
    path('dashboard/visites/<uuid:pk>/modifier/', views.dashboard_visite_form, name='dashboard_visite_modifier'),
    path('dashboard/visites/<uuid:pk>/supprimer/', views.dashboard_visite_supprimer, name='dashboard_visite_supprimer'),

    # Promotions
    path('dashboard/promotions/', views.dashboard_promotions, name='dashboard_promotions'),

    # Témoignages
    path('dashboard/temoignages/', views.dashboard_temoignages, name='dashboard_temoignages'),
    path('dashboard/temoignages/ajouter/', views.dashboard_temoignage_form, name='dashboard_temoignage_ajouter'),
    path('dashboard/temoignages/<int:pk>/modifier/', views.dashboard_temoignage_form, name='dashboard_temoignage_modifier'),
    path('dashboard/temoignages/<int:pk>/supprimer/', views.dashboard_temoignage_supprimer, name='dashboard_temoignage_supprimer'),

    # Utilisateurs
    path('dashboard/utilisateurs/', views.dashboard_utilisateurs, name='dashboard_utilisateurs'),
    path('dashboard/utilisateurs/ajouter/', views.dashboard_utilisateur_form, name='dashboard_utilisateur_ajouter'),
    path('dashboard/utilisateurs/<int:pk>/modifier/', views.dashboard_utilisateur_form, name='dashboard_utilisateur_modifier'),
    path('dashboard/utilisateurs/<int:pk>/supprimer/', views.dashboard_utilisateur_supprimer, name='dashboard_utilisateur_supprimer'),

    # Paramètres
    path('dashboard/parametres/', views.dashboard_parametres, name='dashboard_parametres'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # GROUPY Dashboard
path('dashboard/groupy/', views.dashboard_groupy, name='dashboard_groupy'),
path('dashboard/groupy/categories/', views.dashboard_groupy_categories, name='dashboard_groupy_categories'),
path('dashboard/groupy/qr/ajouter/', views.dashboard_groupy_qr_form, name='dashboard_groupy_qr_ajouter'),
path('dashboard/groupy/qr/<int:pk>/modifier/', views.dashboard_groupy_qr_form, name='dashboard_groupy_qr_modifier'),
path('dashboard/groupy/qr/<int:pk>/supprimer/', views.dashboard_groupy_qr_supprimer, name='dashboard_groupy_qr_supprimer'),
path('dashboard/groupy/categorie/ajouter/', views.dashboard_groupy_cat_form, name='dashboard_groupy_cat_ajouter'),
path('dashboard/groupy/categorie/<int:pk>/supprimer/', views.dashboard_groupy_cat_supprimer, name='dashboard_groupy_cat_supprimer'),

]