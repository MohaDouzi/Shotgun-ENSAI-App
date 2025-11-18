# src/view/evenement/creer_evenement_vue.py
from __future__ import annotations
from typing import Optional
from datetime import date
import logging

from InquirerPy import inquirer
from pydantic import ValidationError

from view.vue_abstraite import VueAbstraite
from view.accueil.accueil_vue import AccueilVue
from view.session import Session

# Services et Modèles
from service.evenement_service import EvenementService
from model.evenement_models import EvenementModelIn
from service.bus_service import BusService

logger = logging.getLogger(__name__)

STATUTS = [
    "pas encore finalisé",
    "disponible en ligne",
    "déjà réalisé",
    "annulé",
]


class CreerEvenementVue(VueAbstraite):
    """
    Vue de création d'un événement (réservée aux administrateurs).
    Permet aussi de configurer les bus associés.
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.service = EvenementService()
        self.bus_service = BusService()

    def afficher(self) -> None:
        """
        Affiche l'en-tête de la vue de création d'un événement.
        """
        print("\n" + "-" * 50)
        print("Création d'un événement".center(50))
        print("-" * 50)
        if self.message:
            print(self.message)

    def choisir_menu(self) -> Optional[AccueilVue]:
        """
        Gère la création d'un événement et de ses bus.
        """
        from view.administrateur.connexion_admin_vue import ConnexionAdminVue

        sess = Session()
        user = sess.utilisateur
        if not sess.est_connecte() or not getattr(user, "administrateur", False):
            print("Accès refusé : vous devez être administrateur.")
            return AccueilVue("Accès refusé")

        # Saisie des champs Événement
        try:
            titre = inquirer.text(
                message="Titre :",
                validate=lambda t: len(t.strip()) > 0 or "Titre requis",
            ).execute().strip()

            adresse = inquirer.text(message="Adresse (optionnel) :").execute().strip() or None
            ville = inquirer.text(message="Ville (optionnel) :").execute().strip() or None

            date_str = inquirer.text(
                message="Date de l'événement (YYYY-MM-DD) :",
                validate=lambda t: (_valid_date(t) or "Format attendu YYYY-MM-DD"),
            ).execute()
            date_evenement = date.fromisoformat(date_str)

            description = inquirer.text(message="Description (optionnel) :").execute().strip() or None

            while True:
                capacite_str = inquirer.text(
                    message="Capacité :",
                    validate=lambda t: (t.isdigit() and int(t) > 0) or "Entrez un entier > 0",
                ).execute().strip()

                if not capacite_str:
                    print("La capacité est obligatoire.")
                    continue
                try:
                    capacite = int(capacite_str)
                    break
                except ValueError:
                    print("Veuillez entrer un nombre entier valide.")

            categorie = inquirer.text(message="Catégorie (optionnel) :").execute().strip() or None

            statut = inquirer.select(
                message="Statut :",
                choices=STATUTS,
                default="pas encore finalisé",
            ).execute()

            fk_utilisateur = user.id_utilisateur

            # Construction du modèle d'entrée
            evt_in = EvenementModelIn(
                fk_utilisateur=fk_utilisateur,
                titre=titre,
                adresse=adresse,
                ville=ville,
                date_evenement=date_evenement,
                description=description,
                capacite=capacite,
                categorie=categorie,
                statut=statut,
            )

        except ValidationError as ve:
            print("Données invalides :")
            for err in ve.errors():
                loc = ".".join(str(x) for x in err.get("loc", []))
                msg = err.get("msg", "erreur")
                print(f"   - {loc}: {msg}")
            logger.info("ValidationError création événement", exc_info=ve)
            return AccueilVue("Création annulée — retour au menu principal")

        except Exception as e:
            logger.exception("Erreur de saisie: %s", e)
            print("Erreur de saisie.")
            return AccueilVue("Création annulée — retour au menu principal")

        # Appel au service Événement
        try:
            evt_out = self.service.create_event(evt_in)
        except Exception as e:
            logger.exception("Erreur Service création événement: %s", e)
            print("Erreur lors de la création en base (contrainte non respectée ?).")
            return AccueilVue("Échec création — retour au menu principal")

        print(f"Événement créé (id={evt_out.id_evenement}) : {evt_out.titre} — le {evt_out.date_evenement}")

        print("\nConfiguration des Transports")
        print("Indiquez la capacité (0 si pas de bus) et les détails (Arrêts, Horaires).")
        
        try:
            # BUS ALLER
            places_aller_str = inquirer.text(
                message="Places Bus ALLER (0 = aucun) :", 
                default="0",
                validate=lambda x: x.isdigit()
            ).execute()
            places_aller = int(places_aller_str)
            
            desc_aller = ""
            if places_aller > 0:
                desc_aller = inquirer.text(
                    message="Détails ALLER (ex: 'Départ arrêt Etangs à 20h30') :",
                    validate=lambda x: len(x) > 3,
                ).execute()

            # --- BUS RETOUR ---
            places_retour_str = inquirer.text(
                message="Places Bus RETOUR (0 = aucun) :", 
                default="0",
                validate=lambda x: x.isdigit()
            ).execute()
            places_retour = int(places_retour_str)

            desc_retour = ""
            if places_retour > 0:
                desc_retour = inquirer.text(
                    message="Détails RETOUR (ex: 'Départ Boite à 04h00') :",
                    validate=lambda x: len(x) > 3,
                ).execute()

            # --- ENREGISTREMENT VIA LE SERVICE BUS ---
            if places_aller > 0 or places_retour > 0:
                self.bus_service.ajouter_bus_evenement(
                    id_evenement=evt_out.id_evenement, 
                    places_aller=places_aller,
                    desc_aller=desc_aller,
                    places_retour=places_retour,
                    desc_retour=desc_retour
                )
                print(f"Bus configurés avec succès.")
            else:
                print("Aucun bus configuré pour cet événement.")

        except Exception as e:
            print(f"Erreur lors de la configuration des bus : {e}")
            print("L'événement est créé, mais sans bus.")
        
        return ConnexionAdminVue("Événement créé — retour au menu principal")


def _valid_date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except Exception:
        return False