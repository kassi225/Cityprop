from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard protégé
    path('dashboard/', views.dashboard, name='dashboard'),

    # Commandes
    path('commande/nouvelle/', views.nouvelle_commande, name='nouvelle_commande'),
    
    
    # Fiches clients
    path('fiches/', views.liste_fiches, name='liste_fiches'),
    path('fiches/<int:fiche_id>/', views.detail_fiche, name='detail_fiche'),
    
    # Alertes fidélisation
    path('alertes/fidelisation/', views.alertes_fidelisation, name='alertes_fidelisation'),
    path('alertes/fidelisation/valider/<int:id>/', views.marquer_fidelise, name='marquer_fidelise'),
    path('fidelisation/<int:id>/', views.detail_fidelisation, name='detail_fidelisation'),
    
    # Alerte tapis 
    path("alertes_tapis/", views.alertes_tapis_retard, name="alertes_tapis_retard"),
    path("alertes_tapis/<int:id>/", views.detail_alerte_tapis, name="detail_alerte_tapis"),
 
    # Export commande
    path("export-commandes/", views.export_commandes_excel, name="export_commandes_excel"),
    
    #facture
    

    # Détails de la commande
    path('commande/<int:fiche_id>/', views.detail_fiche, name='detail_fiche'),

    

    # ➕ FACTURE
    path('facture/creer/<int:fiche_id>/', views.creer_facture, name='creer_facture'),
    path('facture/<int:facture_id>/', views.voir_facture, name='voir_facture'),
    path('devis/<int:facture_id>/telecharger/', 
         views.telecharger_devis_pdf, 
         name='telecharger_devis_pdf'),
    path('commande/<int:fiche_id>/creer-facture/', views.creer_facture, name='creer_facture'),








    
    
]
