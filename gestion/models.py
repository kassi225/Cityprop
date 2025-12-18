from django.db import models
from django.utils import timezone
from num2words import num2words
from decimal import Decimal, ROUND_HALF_UP


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
    
    taux_reduction_pourcentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Réduction (%)"
    )
    
    montant_final_net = models.IntegerField(
        default=0, 
        verbose_name="Montant Net à Payer"
    )

    def save(self, *args, **kwargs):
        # 1. Génération du numéro de document
        if not self.numero_document:
            date_str = timezone.now().strftime("%Y%m%d")
            # Utilisation d'un placeholder temporaire si l'ID n'existe pas encore
            temp_id = self.id if self.id else "NEW"
            self.numero_document = f"{date_str}-{temp_id}-ABJ" 
        
        # 2. On sauvegarde une première fois pour s'assurer que les lignes sont accessibles
        super().save(*args, **kwargs)
        
        # 3. Mise à jour automatique du montant final net après calcul
        # Note: On appelle update_final_amount puis on resauvegarde uniquement ce champ
        self.update_final_amount()
        super().save(update_fields=['montant_final_net'])
        
    @property
    def total_ht_lignes(self):
        """Calcule le montant total des lignes (Total HT avant réduction)."""
        return sum(ligne.prix_total for ligne in self.lignes.all())

    @property
    def montant_reduction(self):
        """
        Calcule la réduction avec la règle commerciale :
        Dernier chiffre 0-4 -> devient 0 | 5-9 -> devient 5
        """
        taux = Decimal(str(self.taux_reduction_pourcentage))
        if taux > 0:
            total_ht = Decimal(str(self.total_ht_lignes))
            # Calcul mathématique de base
            reduction_brute = (total_ht * taux / Decimal('100'))
            valeur = int(reduction_brute.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            
            # Application de votre règle d'arrondi (0/5)
            dernier_chiffre = valeur % 10
            base_dizaine = (valeur // 10) * 10
            
            if dernier_chiffre < 5:
                return base_dizaine  # ex: 1001 -> 1000
            else:
                return base_dizaine + 5  # ex: 1007 -> 1005
        return 0
        
    @property
    def total(self):
        """Retourne le montant final NET à payer."""
        return self.montant_final_net

    @property
    def total_lettres(self):
        """Convertit le total final (net) en lettres."""
        try:
            return num2words(self.total, lang='fr').upper() + " FRANC CFA"
        except:
            return "ZERO FRANC CFA"

    def update_final_amount(self):
        """Calcule et met à jour le montant final net en tenant compte de la réduction arrondie."""
        total_ht = Decimal(str(self.total_ht_lignes))
        # Le montant_reduction ici utilise déjà votre règle (0 ou 5)
        net = total_ht - Decimal(str(self.montant_reduction))
        
        self.montant_final_net = int(net)
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
        ('ABANDON', 'Tapis abandonné'),
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
    
    # --- AJOUTER CETTE LIGNE ---
    fidelise_marquee = models.BooleanField(default=False) 
    
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
