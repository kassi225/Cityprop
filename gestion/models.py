from django.db import models
from django.utils import timezone

class Commande(models.Model):
    TYPE_CHOICES = (
        ('CITYPROP', 'Cityprop'),
        ('CLIMATISEUR', 'Climatiseur'),
        ('TAPISPROP', 'Tapisprop'),
    )

    nom_client = models.CharField(max_length=255)
    numero_client = models.CharField(max_length=20)
    localisation_client = models.CharField(max_length=255)
    type_commande = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_commande} - {self.nom_client}"


class CityClimaDetails(models.Model):
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE)
    date_intervention = models.DateField(blank=True, null=True)
    fidelise = models.BooleanField(default=False)

    SATISFACTION_CHOICES = (
        ('OK', 'OK'),
        ('KO_RET', 'KO - Retouche'),
        ('KO_REFUS', 'KO - Refus seconde intervention'),
    )
    satisfaction = models.CharField(
        max_length=20,
        choices=SATISFACTION_CHOICES,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Détails {self.commande}"


class TapisDetails(models.Model):
    STATUT_CHOICES = (
        ('NON_RESPECTE', 'Délai non respecté'),
        ('PRET', 'Tapis prêt'),
        ('CLIENT_INDISPO', 'Tapis prêt mais client indisponible'),
        ('LIVRE-satisfait', 'client satisfait'),
        ('LIVRE-insatisfait', 'client insatisfait'),
    )
    
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE)
    fidelise = models.BooleanField(default=False)

    date_ramassage = models.DateField(blank=True, null=True)
    nombre_tapis = models.PositiveIntegerField(blank=True, null=True)
    cout = models.PositiveIntegerField(blank=True, null=True)
    date_traitement = models.DateField(blank=True, null=True)
    date_livraison = models.DateField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='NON_RESPECTE')

    def __str__(self):
        return f"Tapis - {self.commande}"


class FidelisationNote(models.Model):
    detail_city_clima = models.ForeignKey(CityClimaDetails, null=True, blank=True, on_delete=models.CASCADE)
    detail_tapis = models.ForeignKey(TapisDetails, null=True, blank=True, on_delete=models.CASCADE)
    commentaire = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    @property
    def client_name(self):
        if self.detail_city_clima:
            return self.detail_city_clima.commande.nom_client
        if self.detail_tapis:
            return self.detail_tapis.commande.nom_client
        return "Inconnu"

    def __str__(self):
        return f"Note fidélisation {self.client_name} - {self.date}"
    
    
class TapisAlerteCommentaire(models.Model):
    tapis = models.ForeignKey(TapisDetails, on_delete=models.CASCADE, related_name="commentaires_alerte")
    texte = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alerte Tapis #{self.tapis.id} - {self.date}"
