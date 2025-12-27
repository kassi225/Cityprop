from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Commande,
    CityClimaDetails,
    TapisDetails,
    FidelisationNote,
    TapisAlerteCommentaire,
    OperationCaisse
)


# =================================================================
#  PERSONNALISATION DE L'INTERFACE (Logo et Titres CityProp)
# =================================================================

admin.site.site_header = format_html(
    '<img src="/static/images/cityprop_logo.png" style="height: 40px; margin-right: 10px; vertical-align: middle;"> ADMINISTRATION CITYPROP'
)
admin.site.site_title = "CityProp Portal"
admin.site.index_title = "Gestion de la plateforme CityProp"

# =================================================================
#  SÉCURITÉ : GESTION DES UTILISATEURS (Masquer le SuperUser)
# =================================================================

class MyUserAdmin(UserAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si l'utilisateur connecté n'est pas SUPERUSER, il ne voit pas les autres SUPERUSER (dont vous)
        if not request.user.is_superuser:
            return qs.filter(is_superuser=False)
        return qs

    def get_readonly_fields(self, request, obj=None):
        # Empêche un simple ADMIN de modifier ses propres privilèges
        if not request.user.is_superuser:
            return ('is_superuser', 'last_login', 'date_joined', 'is_staff')
        return super().get_readonly_fields(request, obj)

# Réenregistrement de la gestion des utilisateurs
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

# =================================================================
#  INLINES
# =================================================================

class CityClimaInline(admin.StackedInline):
    model = CityClimaDetails
    extra = 0

class TapisInline(admin.StackedInline):
    model = TapisDetails
    extra = 0

class FidelisationNoteInline(admin.TabularInline):
    model = FidelisationNote
    extra = 0
    readonly_fields = ("date",)

class TapisAlerteCommentaireInline(admin.TabularInline):
    model = TapisAlerteCommentaire
    extra = 0
    readonly_fields = ("date",)

# =================================================================
#  CONFIGURATIONS DES MODÈLES (Commande, Tapis, etc.)
# =================================================================

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("id", "nom_client", "numero_client", "type_commande", "date_creation")
    list_filter = ("type_commande", "date_creation")
    search_fields = ("nom_client", "numero_client", "localisation_client")
    ordering = ("-date_creation",)
    date_hierarchy = "date_creation"
    inlines = [CityClimaInline, TapisInline]

@admin.register(CityClimaDetails)
class CityClimaAdmin(admin.ModelAdmin):
    list_display = ("commande", "date_intervention", "satisfaction", "fidelise")
    list_filter = ("satisfaction", "fidelise")
    search_fields = ("commande__nom_client", "commande__numero_client")
    autocomplete_fields = ("commande",)
    inlines = [FidelisationNoteInline]

@admin.register(TapisDetails)
class TapisAdmin(admin.ModelAdmin):
    list_display = ("commande", "statut", "date_ramassage", "date_livraison", "nombre_tapis", "fidelise")
    list_filter = ("statut", "fidelise")
    search_fields = ("commande__nom_client", "commande__numero_client")
    autocomplete_fields = ("commande",)
    ordering = ("-date_ramassage",)
    inlines = [TapisAlerteCommentaireInline, FidelisationNoteInline]

@admin.register(FidelisationNote)
class FidelisationNoteAdmin(admin.ModelAdmin):
    list_display = ("client_name", "date")
    search_fields = ("commentaire", "detail_city_clima__commande__nom_client", "detail_tapis__commande__nom_client")
    list_filter = ("date",)
    readonly_fields = ("date",)

@admin.register(TapisAlerteCommentaire)
class TapisAlerteCommentaireAdmin(admin.ModelAdmin):
    list_display = ("tapis", "date")
    search_fields = ("texte", "tapis__commande__nom_client")
    list_filter = ("date",)
    readonly_fields = ("date",)
    
    


@admin.register(OperationCaisse)
class OperationCaisseAdmin(admin.ModelAdmin):
    # Colonnes affichées dans la liste
    list_display = ('date', 'equipe', 'libelle', 'get_type_mouvement', 'get_montant_formatte')
    
    # Filtres latéraux
    list_filter = ('type_mouvement', 'date', 'equipe')
    
    # Barre de recherche
    search_fields = ('libelle', 'equipe', 'montant')
    
    # Tri par défaut (plus récent en haut)
    ordering = ('-date', '-id')

    def get_type_mouvement(self, obj):
        """ Ajoute une pastille de couleur pour le flux """
        color = "#198754" if obj.type_mouvement == 'ENTREE' else "#dc3545"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.type_mouvement
        )
    get_type_mouvement.short_description = "Flux"

    def get_montant_formatte(self, obj):
        """ Formate le montant avec séparateur de milliers """
        return format_html(
            '<span style="font-weight: bold;">{:,.2f} FCFA</span>', 
            obj.montant
        ).replace(',', ' ')
    def get_montant_formatte(self, obj):
        """ Formate le montant avec séparateur de milliers avant de sécuriser le HTML """
        # On formate d'abord le nombre en texte avec Python
        montant_texte = "{:,.2f}".format(obj.montant).replace(',', ' ')
        
        # On injecte ensuite le texte déjà formaté dans le HTML
        return format_html(
            '<span style="font-weight: bold;">{} FCFA</span>', 
            montant_texte
        )
    get_montant_formatte.short_description = "Montant"