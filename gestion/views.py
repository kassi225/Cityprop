from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Commande, CityClimaDetails, FidelisationNote, TapisDetails
from django.db.models import Q
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from django.http import HttpResponse



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            login(request, user)
            return redirect('dashboard')
        return render(request, 'index/login.html', {'error': 'Identifiants incorrects'})
    return render(request, 'index/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def dashboard(request):
    today = timezone.now().date()
    first_day_month = today.replace(day=1)

    # Comptages globaux
    total_commandes = Commande.objects.count()
    total_cityprop = Commande.objects.filter(type_commande="CITYPROP").count()
    total_clim = Commande.objects.filter(type_commande="CLIMATISEUR").count()
    total_tapis = Commande.objects.filter(type_commande="TAPISPROP").count()

    # Fidélisation
    fidelises = CityClimaDetails.objects.filter(fidelise=True).count() + TapisDetails.objects.filter(fidelise=True).count()
    non_fidelises = total_commandes - fidelises
    fidelisations_mois = CityClimaDetails.objects.filter(fidelise=True, commande__date_creation__gte=first_day_month).count() + \
                        TapisDetails.objects.filter(fidelise=True, commande__date_creation__gte=first_day_month).count()

    # Alertes TAPIS >7 jours
    alertes_tapis_7j = TapisDetails.objects.filter(
        date_ramassage__lte=today - timedelta(days=7),
        statut__in=["NON_RESPECTE","PRET","CLIENT_INDISPO"]
    ).count()

    tapis_traite_mois = TapisDetails.objects.filter(
        statut__in=["LIVRE-satisfait","LIVRE-insatisfait"],
        commande__date_creation__gte=first_day_month
    ).count()

    # Statuts TAPIS
    tapis_non_respecte = TapisDetails.objects.filter(statut="NON_RESPECTE").count()
    tapis_pret = TapisDetails.objects.filter(statut="PRET").count()
    tapis_client_indispo = TapisDetails.objects.filter(statut="CLIENT_INDISPO").count()
    tapis_livre_satisfait = TapisDetails.objects.filter(statut="LIVRE-satisfait").count()
    tapis_livre_insatisfait = TapisDetails.objects.filter(statut="LIVRE-insatisfait").count()

    # Commandes récentes
    commandes_recents = Commande.objects.order_by('-date_creation')[:5]
    
    # Alertes fidélisation (renommées pour ne pas masquer le context processor)
    alertes_city = CityClimaDetails.objects.filter(fidelise=False, commande__type_commande='CITYPROP', date_intervention__lte=today - timedelta(days=180)).count()
    alertes_clima = CityClimaDetails.objects.filter(fidelise=False, commande__type_commande='CLIMATISEUR', date_intervention__lte=today - timedelta(days=90)).count()
    alertes_tapis_fidelisation = TapisDetails.objects.filter(fidelise=False, date_livraison__lte=today - timedelta(days=180)).count()

    # Top clients
    top_clients = Commande.objects.values("nom_client").annotate(total=Count("id")).order_by("-total")[:5]

    context = {
        "total_commandes": total_commandes,
        "total_cityprop": total_cityprop,
        "total_clim": total_clim,
        "total_tapis": total_tapis,
        "fidelises": fidelises,
        "non_fidelises": non_fidelises,
        "fidelisations_mois": fidelisations_mois,
        "alertes_city": alertes_city,
        "alertes_clima": alertes_clima,
        "alertes_tapis_fidelisation": alertes_tapis_fidelisation,  # <-- corrigé
        "alertes_tapis_7j": alertes_tapis_7j,
        "tapis_traite_mois": tapis_traite_mois,
        "tapis_non_respecte": tapis_non_respecte,
        "tapis_pret": tapis_pret,
        "tapis_client_indispo": tapis_client_indispo,
        "tapis_livre_satisfait": tapis_livre_satisfait,
        "tapis_livre_insatisfait": tapis_livre_insatisfait,
        "commandes_recents": commandes_recents,
        "top_clients": top_clients,
    }

    return render(request, "index/dashboard.html", context)


@login_required
def nouvelle_commande(request):
    if request.method == 'POST':

        nom = request.POST.get('nom_client')
        numero = request.POST.get('numero_client')
        loc = request.POST.get('localisation_client')
        type_cmd = request.POST.get('type_commande')

        if not nom or not numero or not loc or not type_cmd:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'index/nouvelle_commande.html')

        # Création commande
        commande = Commande.objects.create(
            nom_client=nom,
            numero_client=numero,
            localisation_client=loc,
            type_commande=type_cmd
        )

        # Details CITYCLIMA
        if type_cmd in ['CITYPROP', 'CLIMATISEUR']:
            date_inter = request.POST.get('date_intervention')
            satisfaction = request.POST.get('satisfaction')

            if date_inter or satisfaction:
                CityClimaDetails.objects.create(
                    commande=commande,
                    date_intervention=date_inter or None,
                    satisfaction=satisfaction or None
                )

        # Details TAPIS
        if type_cmd == 'TAPISPROP':
            date_ramassage = request.POST.get('date_ramassage')
            nombre = request.POST.get('nombre_tapis')
            cout = request.POST.get('cout')
            traitement = request.POST.get('date_traitement')
            livraison = request.POST.get('date_livraison')
            commentaire = request.POST.get('commentaire')

            if date_ramassage or nombre or cout or traitement or livraison or commentaire:
                TapisDetails.objects.create(
                    commande=commande,
                    date_ramassage=date_ramassage or None,
                    nombre_tapis=nombre or 0,
                    cout=cout or 0,
                    date_traitement=traitement or None,
                    date_livraison=livraison or None,
                    commentaire=commentaire or "",
                    statut=request.POST.get('statut') or "NON_RESPECTE"
                )

        messages.success(request, "La commande a été créée avec succès !")
        return redirect('liste_fiches')
    

    return render(request, 'index/nouvelle_commande.html')


@login_required
def liste_fiches(request):
    commandes = Commande.objects.all().order_by('-date_creation')

    type_filter = request.GET.get('type_commande', '')
    statut_filter = request.GET.get('statut', '')
    nom_filter = request.GET.get('nom_client', '')
    numero_filter = request.GET.get('numero_client', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    fidelise_filter = request.GET.get('fidelise', '')

    if type_filter:
        commandes = commandes.filter(type_commande=type_filter)

    if statut_filter:
        commandes = commandes.filter(tapisdetails__statut=statut_filter)

    if nom_filter:
        commandes = commandes.filter(nom_client__icontains=nom_filter)

    if numero_filter:
        commandes = commandes.filter(numero_client__icontains=numero_filter)

    if date_debut:
        commandes = commandes.filter(date_creation__date__gte=date_debut)

    if date_fin:
        commandes = commandes.filter(date_creation__date__lte=date_fin)

    if fidelise_filter == "oui":
        commandes = commandes.filter(
            Q(cityclimadetails__fidelise=True) | Q(tapisdetails__fidelise=True)
        )
    elif fidelise_filter == "non":
        commandes = commandes.filter(
            Q(cityclimadetails__fidelise=False) | Q(tapisdetails__fidelise=False)
        )

    paginator = Paginator(commandes.distinct(), 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'commandes': page_obj,
        'type_filter': type_filter,
        'statut_filter': statut_filter,
        'nom_filter': nom_filter,
        'numero_filter': numero_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'fidelise_filter': fidelise_filter,
    }

    return render(request, 'index/liste_fiches.html', context)


@login_required
def detail_fiche(request, fiche_id):
    commande = get_object_or_404(Commande, id=fiche_id)
    
    # Récupération des détails existants
    cityclima = getattr(commande, 'cityclimadetails', None)
    tapis = getattr(commande, 'tapisdetails', None)

    if request.method == 'POST':
        # --- Mise à jour champs généraux ---
        commande.nom_client = request.POST.get('nom_client', commande.nom_client)
        commande.numero_client = request.POST.get('numero_client', commande.numero_client)
        commande.localisation_client = request.POST.get('localisation_client', commande.localisation_client)
        commande.type_commande = request.POST.get('type_commande', commande.type_commande)
        commande.save()

        # --- Mise à jour détails CityClima ---
        if commande.type_commande in ['CITYPROP', 'CLIMATISEUR']:
            if cityclima:
                if request.POST.get('date_intervention'):
                    cityclima.date_intervention = request.POST.get('date_intervention')
                if request.POST.get('satisfaction'):
                    cityclima.satisfaction = request.POST.get('satisfaction')
                cityclima.save()
            else:
                date_intervention = request.POST.get('date_intervention') or None
                satisfaction = request.POST.get('satisfaction') or None
                if date_intervention or satisfaction:
                    CityClimaDetails.objects.create(
                        commande=commande,
                        date_intervention=date_intervention,
                        satisfaction=satisfaction
                    )

        # --- Mise à jour détails Tapis ---
        elif commande.type_commande == 'TAPISPROP':
            if tapis:
                if request.POST.get('date_ramassage'):
                    tapis.date_ramassage = request.POST.get('date_ramassage')
                if request.POST.get('nombre_tapis'):
                    tapis.nombre_tapis = request.POST.get('nombre_tapis')
                if request.POST.get('cout'):
                    tapis.cout = request.POST.get('cout')
                if request.POST.get('date_traitement'):
                    tapis.date_traitement = request.POST.get('date_traitement')
                if request.POST.get('date_livraison'):
                    tapis.date_livraison = request.POST.get('date_livraison')
                if request.POST.get('commentaire') is not None:
                    tapis.commentaire = request.POST.get('commentaire')
                if request.POST.get('statut'):
                    tapis.statut = request.POST.get('statut')
                tapis.save()
            else:
                # Créer le détail uniquement si l'utilisateur a renseigné au moins un champ
                date_ramassage = request.POST.get('date_ramassage') or None
                nombre_tapis = request.POST.get('nombre_tapis') or None
                cout = request.POST.get('cout') or None
                date_traitement = request.POST.get('date_traitement') or None
                date_livraison = request.POST.get('date_livraison') or None
                commentaire = request.POST.get('commentaire') or ''
                statut = request.POST.get('statut') or 'NON_RESPECTE'
                
                if any([date_ramassage, nombre_tapis, cout, date_traitement, date_livraison, commentaire]):
                    TapisDetails.objects.create(
                        commande=commande,
                        date_ramassage=date_ramassage,
                        nombre_tapis=nombre_tapis,
                        cout=cout,
                        date_traitement=date_traitement,
                        date_livraison=date_livraison,
                        commentaire=commentaire,
                        statut=statut
                    )

        messages.success(request, "Commande mise à jour avec succès !")
        return redirect('detail_fiche', fiche_id=fiche_id)

    context = {
        'commande': commande,
        'cityclima': cityclima,
        'tapis': tapis,
    }
    return render(request, 'index/detail_fiche.html', context)


@login_required
def alertes_fidelisation(request):
    """
    Liste des commandes devant être rappelées pour fidélisation
    CITYPROP: date_intervention > 6 mois
    CLIMATISEUR: date_intervention > 3 mois
    TAPISPROP: date_livraison > 6 mois
    """
    now = timezone.now().date()

    # CITYPROP → intervention > 6 mois
    city_alertes = CityClimaDetails.objects.filter(
        fidelise=False,
        commande__type_commande='CITYPROP',
        date_intervention__isnull=False,
        date_intervention__lte=now - timedelta(days=180)
    )

    # CLIMATISEUR → intervention > 3 mois
    clima_alertes = CityClimaDetails.objects.filter(
        fidelise=False,
        commande__type_commande='CLIMATISEUR',
        date_intervention__isnull=False,
        date_intervention__lte=now - timedelta(days=90)
    )

    # TAPISPROP → livraison > 6 mois
    tapis_alertes = TapisDetails.objects.filter(
        fidelise=False,
        date_livraison__isnull=False,
        date_livraison__lte=now - timedelta(days=180)
    )

    context = {
        "city_alertes": city_alertes,
        "clima_alertes": clima_alertes,
        "tapis_alertes": tapis_alertes,
    }
    return render(request, "index/fidelisation.html", context)


@login_required
def marquer_fidelise(request, id):
    """
    Marque une commande comme fidélisée et enregistre un commentaire facultatif
    """
    commentaire = request.POST.get("commentaire", "").strip()

    try:
        # Identifier le détail correspondant à l'ID
        if CityClimaDetails.objects.filter(id=id).exists():
            detail = CityClimaDetails.objects.get(id=id)
            type_detail = "CITYCLIMA"
        else:
            detail = TapisDetails.objects.get(id=id)
            type_detail = "TAPIS"

        # Marquer la commande comme fidélisée
        detail.fidelise = True
        detail.save()

        # Enregistrer le commentaire dans FidelisationNote si présent
        if commentaire:
            if type_detail == "CITYCLIMA":
                FidelisationNote.objects.create(
                    detail_city_clima=detail,
                    commentaire=commentaire
                )
            else:
                FidelisationNote.objects.create(
                    detail_tapis=detail,
                    commentaire=commentaire
                )

        messages.success(request, "Fidélisation enregistrée avec succès.")

    except Exception as e:
        print("Erreur fidélisation:", e)
        messages.error(request, "Impossible de mettre à jour la fidélisation.")

    return redirect('alertes_fidelisation')

@login_required
def detail_fidelisation(request, id):
    """
    Page pour gérer la fidélisation d'une commande.
    Affiche les infos client et permet d'ajouter un commentaire de négociation.
    """
    try:
        if CityClimaDetails.objects.filter(id=id).exists():
            detail = CityClimaDetails.objects.get(id=id)
            type_detail = "CITYCLIMA"
        else:
            detail = TapisDetails.objects.get(id=id)
            type_detail = "TAPIS"
    except:
        messages.error(request, "Détail introuvable.")
        return redirect('liste_fiches')

    if request.method == "POST":
        commentaire = request.POST.get("commentaire", "").strip()
        fidelise = request.POST.get("fidelise") == "on"

        # Sauvegarder la note si commentaire
        if commentaire:
            if type_detail == "CITYCLIMA":
                FidelisationNote.objects.create(
                    detail_city_clima=detail,
                    commentaire=commentaire
                )
            else:
                FidelisationNote.objects.create(
                    detail_tapis=detail,
                    commentaire=commentaire
                )

        # Marquer fidélisé si coché
        if fidelise:
            detail.fidelise = True
            detail.save()
            messages.success(request, "Client fidélisé avec succès !")
            return redirect('liste_fiches')

        messages.success(request, "Commentaire enregistré.")
        return redirect('detail_fidelisation', id=id)

    context = {
        "detail": detail,
        "type_detail": type_detail
    }
    return render(request, "index/detail_fidelisation.html", context)


@login_required
def alertes_tapis_retard(request):
    today = timezone.now().date()
    
    # On récupère les commandes TAPISPROP dont la date de ramassage est dépassée de 7 jours
    # et qui ne sont pas encore livrées (statut != LIVRE-satisfait/LIVRE-insatisfait)
    alertes = TapisDetails.objects.filter(
        date_ramassage__isnull=False,
        date_ramassage__lte=today - timedelta(days=7)
    ).exclude(statut__in=['LIVRE-satisfait', 'LIVRE-insatisfait'])

    context = {
        "alertes": alertes
    }
    return render(request, "index/alerte_tapis.html", context)


@login_required
def detail_alerte_tapis(request, id):
    tapis = get_object_or_404(TapisDetails, id=id)

    # Empêcher l’accès si la commande n'est plus en alerte
    if tapis.statut in ["LIVRE-satisfait", "LIVRE-insatisfait"]:
        messages.info(request, "Cette commande n'est plus en alerte.")
        return redirect("alertes_tapis_retard")

    if request.method == "POST":
        # Nouveau commentaire
        texte = request.POST.get("commentaire", "").strip()
        if texte:
            from .models import TapisAlerteCommentaire
            TapisAlerteCommentaire.objects.create(
                tapis=tapis,
                texte=texte
            )
            messages.success(request, "Commentaire ajouté avec succès.")

        # Mise à jour du statut
        new_statut = request.POST.get("statut")
        if new_statut:
            tapis.statut = new_statut
            tapis.save()
            messages.success(request, "Statut mis à jour.")

            # Si statut = livré -> supprimer de l'alerte
            if new_statut in ["LIVRE-satisfait", "LIVRE-insatisfait"]:
                return redirect("alertes_tapis_retard")

        return redirect("detail_alerte_tapis", id=id)

    context = {
        "tapis": tapis,
        "commentaires": tapis.commentaires_alerte.order_by("-date")
    }

    return render(request, "index/detail_alerte_tapis.html", context)


@login_required
def export_commandes_excel(request):
    commandes = Commande.objects.all().order_by('-date_creation')

    # mêmes filtres que liste_fiches
    type_filter = request.GET.get('type_commande', '')
    statut_filter = request.GET.get('statut', '')
    nom_filter = request.GET.get('nom_client', '')
    numero_filter = request.GET.get('numero_client', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    fidelise_filter = request.GET.get('fidelise', '')

    if type_filter:
        commandes = commandes.filter(type_commande=type_filter)
    if statut_filter:
        commandes = commandes.filter(tapisdetails__statut=statut_filter)
    if nom_filter:
        commandes = commandes.filter(nom_client__icontains=nom_filter)
    if numero_filter:
        commandes = commandes.filter(numero_client__icontains=numero_filter)
    if date_debut:
        commandes = commandes.filter(date_creation__date__gte=date_debut)
    if date_fin:
        commandes = commandes.filter(date_creation__date__lte=date_fin)
    if fidelise_filter == "oui":
        commandes = commandes.filter(
            Q(cityclimadetails__fidelise=True) | Q(tapisdetails__fidelise=True)
        )
    elif fidelise_filter == "non":
        commandes = commandes.filter(
            Q(cityclimadetails__fidelise=False) | Q(tapisdetails__fidelise=False)
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Commandes"

    # 🎨 Styles
    header_fill = PatternFill(start_color="157347", end_color="157347", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    center = Alignment(vertical="center", wrap_text=True)

    headers = [
        "Client", "Numéro", "Localisation",
        "Type", "Date création",
        "Détails", "Fidélisé"
    ]
    ws.append(headers)

    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center

    # 📊 Données
    for c in commandes:
        details = "-"
        fidelise = "Non"

        if c.type_commande in ["CITYPROP", "CLIMATISEUR"] and hasattr(c, "cityclimadetails"):
            d = c.cityclimadetails
            details = f"Intervention: {d.date_intervention or '-'}\nSatisfaction: {d.satisfaction or '-'}"
            fidelise = "Oui" if d.fidelise else "Non"

        elif c.type_commande == "TAPISPROP" and hasattr(c, "tapisdetails"):
            t = c.tapisdetails
            details = (
                f"Ramassage: {t.date_ramassage or '-'}\n"
                f"Livraison: {t.date_livraison or '-'}\n"
                f"Statut: {t.get_statut_display()}"
            )
            fidelise = "Oui" if t.fidelise else "Non"

        ws.append([
            c.nom_client,
            c.numero_client,
            c.localisation_client,
            c.type_commande,
            c.date_creation.strftime("%d/%m/%Y"),
            details,
            fidelise
        ])

    # 📐 Ajustement colonnes
    widths = [22, 18, 35, 15, 15, 45, 12]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="commandes_cityprop.xlsx"'
    wb.save(response)
    return response


def alertes_counts(request):
    alertes_city = CityClimaDetails.objects.filter(fidelise=False).count()
    alertes_tapis = TapisDetails.objects.filter(retard=True).count()
    return {
        'alertes_city': alertes_city,
        'alertes_tapis': alertes_tapis,
    }





