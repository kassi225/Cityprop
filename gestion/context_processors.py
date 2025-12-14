from django.utils import timezone
from datetime import timedelta
from .models import CityClimaDetails, TapisDetails

def alertes_sidebar(request):
    today = timezone.now().date()

    alertes_city = CityClimaDetails.objects.filter(
        fidelise=False,
        commande__type_commande='CITYPROP',
        date_intervention__lte=today - timedelta(days=180)
    ).count()

    alertes_clima = CityClimaDetails.objects.filter(
        fidelise=False,
        commande__type_commande='CLIMATISEUR',
        date_intervention__lte=today - timedelta(days=90)
    ).count()

    alertes_tapis = TapisDetails.objects.filter(
        date_ramassage__isnull=False,
        date_ramassage__lte=today - timedelta(days=7)
    ).exclude(statut__in=['LIVRE-satisfait', 'LIVRE-insatisfait']).count()

    return {
        "alertes_city": alertes_city,
        "alertes_clima": alertes_clima,
        "alertes_tapis": alertes_tapis
    }
