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


# Journal EDEN GROUP
path('journal/', views.journal_kiosque, name='journal_kiosque'),
path('journal/<int:numero>/', views.journal_lire, name='journal_lire'),
path('journal/<int:numero>/page/<int:page>/', views.journal_page_json, name='journal_page_json'),

# Dashboard Journal
path('dashboard/journal/', views.dashboard_journal, name='dashboard_journal'),
path('dashboard/journal/ajouter/', views.dashboard_journal_edition_form, name='dashboard_journal_edition_ajouter'),
path('dashboard/journal/<int:pk>/modifier/', views.dashboard_journal_edition_form, name='dashboard_journal_edition_modifier'),
path('dashboard/journal/<int:pk>/supprimer/', views.dashboard_journal_edition_supprimer, name='dashboard_journal_edition_supprimer'),
path('dashboard/journal/<int:pk>/publier/', views.dashboard_journal_publier, name='dashboard_journal_publier'),
path('dashboard/journal/<int:edition_pk>/page/<int:page_num>/editer/', views.dashboard_journal_page_editer, name='dashboard_journal_page_editer'),
path('dashboard/journal/<int:edition_pk>/page/ajouter/', views.dashboard_journal_page_ajouter, name='dashboard_journal_page_ajouter'),
path('dashboard/journal/<int:edition_pk>/page/<int:page_num>/supprimer/', views.dashboard_journal_page_supprimer, name='dashboard_journal_page_supprimer'),
path('dashboard/journal/media/upload/', views.dashboard_journal_media_upload, name='dashboard_journal_media_upload'),
path('dashboard/journal/media/liste/', views.dashboard_journal_media_liste, name='dashboard_journal_media_liste'),
path('api/journal/sauvegarder-page/', views.api_journal_sauvegarder_page, name='api_journal_sauvegarder_page'),
path('dashboard/sites/<uuid:pk>/stats-manuelles/', views.dashboard_site_stats_manuelles, name='dashboard_site_stats_manuelles'),
# Dashboard home config
path('dashboard/home-config/', views.dashboard_home_config, name='dashboard_home_config'),
path('dashboard/home-config/hero/', views.dashboard_hero_form, name='dashboard_hero_form'),
path('dashboard/home-config/services/', views.dashboard_services, name='dashboard_services'),
path('dashboard/home-config/etapes/', views.dashboard_etapes, name='dashboard_etapes'),
path('dashboard/home-config/livret/', views.dashboard_livret_form, name='dashboard_livret_form'),
path('dashboard/home-config/actualites/', views.dashboard_actualites, name='dashboard_actualites'),
path('dashboard/home-config/actualites/ajouter/', views.dashboard_actualite_form, name='dashboard_actualite_ajouter'),
path('dashboard/home-config/actualites/<int:pk>/modifier/', views.dashboard_actualite_form, name='dashboard_actualite_modifier'),
path('dashboard/home-config/actualites/<int:pk>/supprimer/', views.dashboard_actualite_supprimer, name='dashboard_actualite_supprimer'),
path('dashboard/home-config/commentaires/', views.dashboard_commentaires, name='dashboard_commentaires'),
path('dashboard/home-config/commentaires/ajouter/', views.dashboard_commentaire_form, name='dashboard_commentaire_ajouter'),
path('dashboard/home-config/commentaires/<int:pk>/modifier/', views.dashboard_commentaire_form, name='dashboard_commentaire_modifier'),
path('dashboard/home-config/commentaires/<int:pk>/supprimer/', views.dashboard_commentaire_supprimer, name='dashboard_commentaire_supprimer'),
path('dashboard/home-config/stats/', views.dashboard_stats_home, name='dashboard_stats_home'),
path('dashboard/home-config/hero-slides/', views.dashboard_hero_slides, name='dashboard_hero_slides'),
path('dashboard/home-config/hero-slides/<int:pk>/supprimer/', views.dashboard_hero_slide_supprimer, name='dashboard_hero_slide_supprimer'),
path('dashboard/home-config/hero-slides/<int:pk>/toggle/', views.dashboard_hero_slide_toggle, name='dashboard_hero_slide_toggle'),
path('dashboard/journal/<int:edition_pk>/page/<int:page_num>/supprimer/', views.dashboard_journal_page_supprimer, name='dashboard_journal_page_supprimer'),

# Module Une & Événements — public
path('une-evenements/', views.une_evenements_accueil, name='une_evenements_accueil'),
path('une-evenements/<int:pk>/', views.une_evenement_detail, name='une_evenement_detail'),
path('une-evenements/categorie/<str:cat>/', views.une_evenements_liste, name='une_evenements_liste'),

# Dashboard
path('dashboard/une-evenements/', views.dashboard_une_liste, name='dashboard_une_liste'),
path('dashboard/une-evenements/ajouter/', views.dashboard_une_form, name='dashboard_une_ajouter'),
path('dashboard/une-evenements/<int:pk>/modifier/', views.dashboard_une_form, name='dashboard_une_modifier'),
path('dashboard/une-evenements/<int:pk>/supprimer/', views.dashboard_une_supprimer, name='dashboard_une_supprimer'),
path('dashboard/une-evenements/<int:pk>/publier/', views.dashboard_une_publier, name='dashboard_une_publier'),
path('dashboard/une-evenements/<int:pk>/editeur/', views.dashboard_une_editeur, name='dashboard_une_editeur'),
path('api/une-evenements/sauvegarder/', views.api_une_sauvegarder, name='api_une_sauvegarder'),
path('dashboard/une-evenements/media/upload/', views.dashboard_une_media_upload, name='dashboard_une_media_upload'),

# Module Nos Projets — public
path('projets/', views.nos_projets, name='nos_projets'),
path('projets/<slug:slug>/', views.projet_detail, name='projet_detail'),
path('api/projet/<slug:slug>/etapes/', views.api_projet_etapes, name='api_projet_etapes'),

# Dashboard Nos Projets
path('dashboard/projets/', views.dashboard_projets_liste, name='dashboard_projets_liste'),
path('dashboard/projets/ajouter/', views.dashboard_projet_form, name='dashboard_projet_ajouter'),
path('dashboard/projets/<uuid:pk>/modifier/', views.dashboard_projet_form, name='dashboard_projet_modifier'),
path('dashboard/projets/<uuid:pk>/supprimer/', views.dashboard_projet_supprimer, name='dashboard_projet_supprimer'),
path('dashboard/projets/<uuid:pk>/etapes/', views.dashboard_projet_etapes, name='dashboard_projet_etapes'),
path('dashboard/projets/<uuid:pk>/galerie/', views.dashboard_projet_galerie, name='dashboard_projet_galerie'),
path('dashboard/projets/<uuid:pk>/galerie/supprimer/<int:img_pk>/', views.dashboard_projet_image_supprimer, name='dashboard_projet_image_supprimer'),
path('dashboard/projets/<uuid:pk>/infrastructures/', views.dashboard_projet_infrastructures, name='dashboard_projet_infrastructures'),

# Module Nos Agences — public
path('agences/', views.nos_agences, name='nos_agences'),

# Dashboard Agences
path('dashboard/agences/', views.dashboard_agences_liste, name='dashboard_agences_liste'),
path('dashboard/agences/ajouter/', views.dashboard_agence_form, name='dashboard_agence_ajouter'),
path('dashboard/agences/<int:pk>/modifier/', views.dashboard_agence_form, name='dashboard_agence_modifier'),
path('dashboard/agences/<int:pk>/supprimer/', views.dashboard_agence_supprimer, name='dashboard_agence_supprimer'),
path('dashboard/agences/stats/', views.dashboard_agences_stats, name='dashboard_agences_stats'),

# Module Nos Services — public
path('services/', views.nos_services, name='nos_services'),
path('services/<slug:slug>/', views.service_detail, name='service_detail'),

# Dashboard Services
path('dashboard/services-module/', views.dashboard_services_liste, name='dashboard_services_liste'),
path('dashboard/services-module/ajouter/', views.dashboard_service_form, name='dashboard_service_ajouter'),
path('dashboard/services-module/<int:pk>/modifier/', views.dashboard_service_form, name='dashboard_service_modifier'),
path('dashboard/services-module/<int:pk>/supprimer/', views.dashboard_service_supprimer, name='dashboard_service_supprimer'),
path('dashboard/services-module/categories/', views.dashboard_services_categories, name='dashboard_services_categories'),
path('dashboard/services-module/processus/', views.dashboard_services_processus, name='dashboard_services_processus'),
path('dashboard/services-module/engagements/', views.dashboard_services_engagements, name='dashboard_services_engagements'),

path('api/calcul-parcelles/', views.api_calcul_parcelles, name='api_calcul_parcelles'),

# Académie — public
path('academie/', views.academie_accueil, name='academie_accueil'),
path('academie/<str:cat>/', views.academie_categorie, name='academie_categorie'),
path('academie/document/<int:pk>/telecharger/', views.academie_telecharger, name='academie_telecharger'),
path('academie/video/<int:pk>/voir/', views.academie_voir_video, name='academie_voir_video'),

# Dashboard Académie
path('dashboard/academie/', views.dashboard_academie_liste, name='dashboard_academie_liste'),
path('dashboard/academie/ajouter/', views.dashboard_academie_form, name='dashboard_academie_ajouter'),
path('dashboard/academie/<int:pk>/modifier/', views.dashboard_academie_form, name='dashboard_academie_modifier'),
path('dashboard/academie/<int:pk>/supprimer/', views.dashboard_academie_supprimer, name='dashboard_academie_supprimer'),
path('dashboard/academie/videos/', views.dashboard_academie_videos, name='dashboard_academie_videos'),
path('dashboard/academie/videos/ajouter/', views.dashboard_academie_video_form, name='dashboard_academie_video_ajouter'),
path('dashboard/academie/videos/<int:pk>/modifier/', views.dashboard_academie_video_form, name='dashboard_academie_video_modifier'),
path('dashboard/academie/videos/<int:pk>/supprimer/', views.dashboard_academie_video_supprimer, name='dashboard_academie_video_supprimer'),
path('dashboard/academie/faq/', views.dashboard_academie_faq, name='dashboard_academie_faq'),
path('dashboard/academie/parcours/', views.dashboard_academie_parcours, name='dashboard_academie_parcours'),
path('dashboard/academie/stats/', views.dashboard_academie_stats, name='dashboard_academie_stats'),

]