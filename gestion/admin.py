from django.contrib import admin
from .models import (
    Commande,
    CityClimaDetails,
    TapisDetails,
    FidelisationNote,
    TapisAlerteCommentaire
)


# =========================
#   INLINES
# =========================

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


# =========================
#   COMMANDE
# =========================

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nom_client",
        "numero_client",
        "type_commande",
        "localisation_client",
        "date_creation",
    )
    list_filter = ("type_commande", "date_creation")
    search_fields = ("nom_client", "numero_client", "localisation_client")
    ordering = ("-date_creation",)
    date_hierarchy = "date_creation"

    inlines = [CityClimaInline, TapisInline]


# =========================
#   CITY / CLIMATISEUR
# =========================

@admin.register(CityClimaDetails)
class CityClimaAdmin(admin.ModelAdmin):
    list_display = (
        "commande",
        "date_intervention",
        "satisfaction",
        "fidelise",
    )
    list_filter = ("satisfaction", "fidelise")
    search_fields = ("commande__nom_client", "commande__numero_client")
    autocomplete_fields = ("commande",)

    inlines = [FidelisationNoteInline]


# =========================
#   TAPIS
# =========================

@admin.register(TapisDetails)
class TapisAdmin(admin.ModelAdmin):
    list_display = (
        "commande",
        "statut",
        "date_ramassage",
        "date_livraison",
        "nombre_tapis",
        "fidelise",
    )
    list_filter = ("statut", "fidelise")
    search_fields = ("commande__nom_client", "commande__numero_client")
    autocomplete_fields = ("commande",)
    ordering = ("-date_ramassage",)

    inlines = [TapisAlerteCommentaireInline, FidelisationNoteInline]


# =========================
#   NOTES DE FIDELISATION
# =========================

@admin.register(FidelisationNote)
class FidelisationNoteAdmin(admin.ModelAdmin):
    list_display = ("client_name", "date")
    search_fields = (
        "commentaire",
        "detail_city_clima__commande__nom_client",
        "detail_tapis__commande__nom_client",
    )
    list_filter = ("date",)
    readonly_fields = ("date",)


# =========================
#   COMMENTAIRES ALERTES TAPIS
# =========================

@admin.register(TapisAlerteCommentaire)
class TapisAlerteCommentaireAdmin(admin.ModelAdmin):
    list_display = ("tapis", "date")
    search_fields = (
        "texte",
        "tapis__commande__nom_client",
    )
    list_filter = ("date",)
    readonly_fields = ("date",)
