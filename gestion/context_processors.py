from django.utils import timezone
from datetime import timedelta
from .models import CityClimaDetails, TapisDetails

def alertes_sidebar(request):
    today = timezone.now().date()

    # 1. FIDÉLISATION : Cityprop (180 jours)
    alertes_city = CityClimaDetails.objects.filter(
        fidelise=False,
        commande__type_commande='CITYPROP',
        date_intervention__lte=today - timedelta(days=180)
    ).count()

    # 2. FIDÉLISATION : Climatiseur (90 jours)
    alertes_clima = CityClimaDetails.objects.filter(
        fidelise=False,
        commande__type_commande='CLIMATISEUR',
        date_intervention__lte=today - timedelta(days=90)
    ).count()

    # 3. FIDÉLISATION : Tapis (Relance 180 jours après LIVRAISON)
    # On ne relance que les tapis déjà livrés
    alertes_tapis_fidelisation = TapisDetails.objects.filter(
        fidelise=False,
        statut__in=['LIVRE_SATISFAIT', 'LIVRE_INSATISFAIT'],
        date_livraison__lte=today - timedelta(days=180)
    ).count()

    # 4. RETARD LOGISTIQUE : Tapis (Non livrés 7 jours après RAMASSAGE)
    alertes_tapis_retard = TapisDetails.objects.filter(
        date_ramassage__isnull=False,
        date_ramassage__lte=today - timedelta(days=11)
    ).exclude(
        statut__in=['LIVRE_SATISFAIT', 'LIVRE_INSATISFAIT', 'ABANDON']
    ).count()

    return {
        "alertes_city": alertes_city,
        "alertes_clima": alertes_clima,
        "alertes_tapis_fidelisation": alertes_tapis_fidelisation,
        "alertes_tapis_retard": alertes_tapis_retard,
        # Total pour une bulle de notification globale "Fidélisation"
        "total_fidelisation": alertes_city + alertes_clima + alertes_tapis_fidelisation
    }