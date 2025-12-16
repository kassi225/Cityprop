from django.db import models
from django.utils import timezone
from num2words import num2words


class Facture(models.Model):
    TYPE_CHOICES = (
        ('DEVIS', 'Devis'),
        ('FACTURE', 'Facture'),
    )

    commande = models.ForeignKey('Commande', on_delete=models.CASCADE) 
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES, default='DEVIS')
    numero_document = models.CharField(max_length=50, blank=True) 
    date_emission = models.DateField(default=timezone.now)
    lieu_emission = models.CharField(max_length=255, default="Abidjan")
    objet = models.CharField(max_length=255, blank=True)
    signature = models.CharField(max_length=255, blank=True)
    
    # --- NOUVEAUX CHAMPS POUR LA RÉDUCTION ---
    taux_reduction_pourcentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Réduction (%)"
    )
    
    # Champ qui stockera le total après réduction (le montant à payer)
    montant_final_net = models.IntegerField(
        default=0, 
        verbose_name="Montant Net à Payer"
    )
    # ----------------------------------------
    
    def save(self, *args, **kwargs):
        # Génération du numéro de document (votre code existant)
        if not self.numero_document:
            date_str = timezone.now().strftime("%Y%m%d")
            self.numero_document = f"{date_str}-{self.id or 'TEMP'}-ABJ" 
            
        super().save(*args, **kwargs)
        
    @property
    def total_ht_lignes(self):
        """Calcule le montant total des lignes (Total HT avant réduction)."""
        # Note: 'lignes' est le related_name utilisé dans FactureLigne
        return sum(ligne.prix_total for ligne in self.lignes.all())

    @property
    def montant_reduction(self):
        """Calcule le montant de la réduction en FCFA."""
        if self.taux_reduction_pourcentage > 0:
            # S'assurer que le calcul est fait avec le montant total HT
            return self.total_ht_lignes * (self.taux_reduction_pourcentage / 100)
        return 0
        
    @property
    def total(self):
        """Retourne le montant final NET à payer (lu depuis montant_final_net)."""
        # Le 'total' est désormais le montant net stocké.
        return self.montant_final_net

    @property
    def total_lettres(self):
        """Convertit le total final (net) en lettres."""
        # Utilise la propriété 'total' (montant net)
        return num2words(self.total, lang='fr').upper() + " FRANC CFA"

    def update_final_amount(self):
        """Calcule et met à jour le montant final net avant sauvegarde."""
        total_net = self.total_ht_lignes - self.montant_reduction
        self.montant_final_net = round(total_net)
        return self.montant_final_net

    def __str__(self):
        return f"{self.type_document} #{self.numero_document} - {self.commande.nom_client}"

class FactureLigne(models.Model):
    facture = models.ForeignKey(
        Facture,
        related_name='lignes',
        on_delete=models.CASCADE
    )
    designation = models.CharField(max_length=255)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.PositiveIntegerField()
    note_prix_unitaire = models.CharField(max_length=255, blank=True)
    
    @property
    def prix_total(self):
        """Calcule le total pour une seule ligne : Quantité * Prix Unitaire."""
        try:
            # Les champs PositiveIntegerField garantissent que les valeurs sont des entiers non négatifs
            return self.quantite * self.prix_unitaire
        except TypeError:
            return 0
         
    
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
