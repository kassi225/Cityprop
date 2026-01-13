from datetime import date
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
    signature = models.CharField(max_length=255, default="LA COMPTABILITÉ")
    
    # Précision augmentée à 3 chiffres après la virgule
    taux_reduction_pourcentage = models.DecimalField(
        max_digits=7, 
        decimal_places=3, 
        default=0.000,
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
            temp_id = self.id if self.id else "NEW"
            self.numero_document = f"{date_str}-{temp_id}-ABJ" 
        
        # 2. Premier enregistrement pour accéder aux lignes
        super().save(*args, **kwargs)
        
        # 3. Calcul du montant final et mise à jour
        self.update_final_amount()
        super().save(update_fields=['montant_final_net'])
        
    @property
    def total_ht_lignes(self):
        """Somme de toutes les lignes avant réduction."""
        return sum(ligne.prix_total for ligne in self.lignes.all())

    @property
    def montant_reduction(self):
        """
        Calcule la différence entre le HT et le Net arrondi.
        Garantit que HT - Réduction = Net (Multiple de 5).
        """
        total_ht = Decimal(str(self.total_ht_lignes))
        return int(total_ht) - self.montant_final_net
        
    @property
    def total(self):
        """Alias pour le montant net final."""
        return self.montant_final_net

    @property
    def total_lettres(self):
        """Conversion du montant net en toutes lettres."""
        try:
            return num2words(self.total, lang='fr').upper() + " FRANC CFA"
        except:
            return "ZERO FRANC CFA"

    def update_final_amount(self):
        """
        Calcule le net avec le taux à 3 décimales et arrondit 
        le résultat final à la pièce de 5 FCFA la plus proche.
        """
        total_ht = Decimal(str(self.total_ht_lignes))
        taux = Decimal(str(self.taux_reduction_pourcentage))
        
        if taux > 0:
            reduction_theorique = (total_ht * taux / Decimal('100'))
            net_theorique = float(total_ht - reduction_theorique)
            
            # Règle d'arrondi monétaire (Multiple de 5)
            # Ex: 120 003 -> 120 005 | 120 002 -> 120 000
            self.montant_final_net = int(round(net_theorique / 5.0) * 5)
        else:
            self.montant_final_net = int(total_ht)
            
        return self.montant_final_net

    def __str__(self):
        return f"{self.type_document} #{self.numero_document}"

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
        return self.quantite * self.prix_unitaire       
    
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
    
    designation = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Désignation des équipements"
    )

    # Coût de l'intervention
    cout = models.PositiveIntegerField(
        default=0, 
        blank=True, 
        null=True, 
        verbose_name="Coût"
    )

    def __str__(self):
        return f"Détails {self.commande}"

class TapisDetails(models.Model):
    STATUT_CHOICES = (
        ('NON_RESPECTE', 'En cours(en Atelier)'),
        ('PRET', 'En attente(Sortie Atelier)'),
        ('CLIENT_INDISPO', 'Tapis prêt Client indisponible'),
        ('LIVRE_SATISFAIT', 'Livré - Client satisfait'),
        ('LIVRE_INSATISFAIT', 'Livré - Client insatisfait'),
        ('ABANDON', 'Tapis abandonné'),
    )

    commande = models.OneToOneField(Commande, on_delete=models.CASCADE)
    fidelise = models.BooleanField(default=False)

    # Étapes de dates
    date_ramassage = models.DateField(blank=True, null=True)
    nombre_tapis = models.PositiveIntegerField(blank=True, null=True)
    cout = models.PositiveIntegerField(blank=True, null=True)
    
    # Étape 1 : Fin du nettoyage à l'atelier
    date_traitement = models.DateField(blank=True, null=True)
    
    # Étape 2 : Date à laquelle on a promis de livrer le client (NOUVEAU)
    date_prevue_livraison = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date prévue de livraison"
    )
    
    # Étape 3 : Date réelle où le tapis est sorti
    date_livraison = models.DateField(blank=True, null=True)
    
    commentaire = models.TextField(blank=True, null=True)

    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='NON_RESPECTE'
    )
    
    @property
    def niveau_urgence(self):
        if not self.date_traitement:
            return "NORMAL"
        
        aujourdhui = date.today()
        diff = (self.date_traitement - aujourdhui).days

        if diff < 0:
            return "RETARD"  # Date dépassée
        elif diff <= 1:
            return "URGENT"  # Aujourd'hui ou demain
        else:
            return "NORMAL"  # Plus de 1 jour de marge

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
    
    

class OperationCaisse(models.Model):
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée (Recette)'),
        ('SORTIE', 'Sortie (Dépense)'),
    ]

    date = models.DateField()
    equipe = models.CharField(max_length=100, verbose_name="Équipe / Bénéficiaire")
    libelle = models.CharField(max_length=255, verbose_name="Libellé de l'opération")
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    # Correction : Utilisation de decimal_places au lieu de decimal_digits
    montant = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00
    )
    
    # Correction : Utilisation de decimal_places et ajout de default
    solde_historique = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        editable=False, 
        default=0.00
    )

    def __str__(self):
        return f"{self.date} - {self.libelle} ({self.montant} FCFA)"

    class Meta:
        verbose_name = "Opération de Caisse"
        verbose_name_plural = "Opérations de Caisse"
        ordering = ['date', 'id'] # Chronologique : du plus ancien au plus récent
        
    @property
    def montant_signe(self):
        if self.type_mouvement == 'SORTIE':
            return -self.montant
        return self.montant
