# src/view/reservations/reservation_vue.py
from typing import Optional, Any, Union
from datetime import date
from InquirerPy import inquirer

from view.vue_abstraite import VueAbstraite
from view.session import Session

# Passage aux services
from service.bus_service import BusService
from service.reservation_service import ReservationService
from service.evenement_service import EvenementService
from model.reservation_models import ReservationModelIn
try:
    from model.evenement_models import EvenementModelOut
except ImportError:
    EvenementModelOut = object # Fallback si le fichier n'existe pas

# Envoi d’e-mail de confirmation
from dotenv import load_dotenv
try:
    from utils.api_brevo import send_email_brevo
    LOADED_BREVO = True
except ImportError:
    LOADED_BREVO = False
    print("WARNING: 'api_brevo' non trouvé. L'envoi d'email sera désactivé.")
load_dotenv()


class ReservationVue(VueAbstraite):
    """
    Vue console : permet à un utilisateur de réserver une place pour un événement.
    Gère à la fois les dictionnaires (de ConsulterVue) et les objets (de son propre
    sélecteur).
    """

    def __init__(self, message: str = "", evenement: Optional[Any] = None):
        super().__init__(message)
        self.session = Session()
        self.user = self.session.utilisateur
        self.reservation_service = ReservationService()
        self.evenement_service = EvenementService()
        self.evenement = evenement
        self.bus_service = BusService()

    # --- HELPER (la méthode robuste) ---
    @staticmethod
    def _get_attr(obj: Any, key: str, default=None):
        """Accède à un attribut/clé, que ce soit un dict ou un objet."""
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    # --- FIN HELPER ---

    # ----------------- Cycle Vue -----------------
    def afficher(self) -> None:
        """
        Affiche le titre de la vue pour réserver un événement.
        """
        super().afficher()
        print("\n--- Réservation d’un événement ---")

    def choisir_menu(self) -> Optional[VueAbstraite]:
        """
        Permet à l’utilisateur de créer une réservation pour un événement
        via un formulaire interactif.
        """
        from view.client.connexion_client_vue import ConnexionClientVue
        from view.consulter.consulter_evenement_vue import ConsulterVue

        # --- Vérification de la connexion ---
        if not self.session.est_connecte() or not self.user:
            print("Vous devez être connecté pour réserver.")
            return ConsulterVue("Connexion requise pour réserver.")

        # --- Étape 1 : sélectionner ou confirmer l’événement ---
        if not self.evenement:
            evenements = self.evenement_service.lister_evenements_disponibles()
            if not evenements:
                print("Aucun événement disponible pour réservation.")
                return ConsulterVue("Aucun événement disponible.")

            choix_evt = inquirer.select(
                message="Sélectionnez un événement :",
                choices=[
                    {"name": f"{e.date_evenement} | {e.titre}", "value": e}
                    for e in evenements
                ] + [{"name": "--- Retour ---", "value": None}],
            ).execute()

            if choix_evt is None:
                return ConsulterVue("Retour au menu précédent.")
            self.evenement = choix_evt

        evt = self.evenement 

        titre_evt = self._get_attr(evt, 'titre', 'N/A')
        date_evt = self._get_attr(evt, 'date_evenement', 'N/A')
        print(f"\nÉvénement sélectionné : {titre_evt} ({date_evt})")

        # --- Étape 2 : vérifier les places restantes ---
        places = self._get_attr(evt, "places_restantes")
        if places is not None and places <= 0:# Correction: <= 0
            print("L'événement est complet.")
            return ConsulterVue("Événement complet.")

        # --- Étape 3 : saisie des options de réservation ---
        print("\n--- Choix de vos options ---")
        
        # Récupération de l'ID événement
        id_evt = self._get_attr(evt, 'id_evenement')

        # --- Logique BUS ALLER ---
        bus_aller = False
        cap_aller = self.bus_service.get_capacite(id_evt, 'aller')
        prises_aller = self.reservation_service.get_nb_places_bus_prises(id_evt, 'aller')
        restantes_aller = cap_aller - prises_aller

        if cap_aller == 0:
            print("🚌 Bus Aller : Pas de bus prévu.")
        elif restantes_aller <= 0:
            print(f"🚌 Bus Aller : COMPLET ({cap_aller}/{cap_aller})")
        else:
            # On ne pose la question que s'il y a de la place
            bus_aller = inquirer.confirm(
                message=f"Prendre le bus ALLER ? ({restantes_aller} places disp.)", 
                default=True
            ).execute()

        # --- Logique BUS RETOUR ---
        bus_retour = False
        cap_retour = self.bus_service.get_capacite(id_evt, 'retour')
        prises_retour = self.reservation_service.get_nb_places_bus_prises(id_evt, 'retour')
        restantes_retour = cap_retour - prises_retour

        if cap_retour == 0:
            print("Bus Retour : Pas de bus prévu.")
        elif restantes_retour <= 0:
            print(f"Bus Retour : COMPLET ({cap_retour}/{cap_retour})")
        else:
            bus_retour = inquirer.confirm(
                message=f"Prendre le bus RETOUR ? ({restantes_retour} places disp.)", 
                default=True
            ).execute()

        # --- Autres options (classique) ---
        adherent = inquirer.confirm(message="Êtes-vous adhérent ?", default=False).execute()
        sam = inquirer.confirm(message="Êtes-vous SAM ?", default=False).execute()
        boisson = inquirer.confirm(message="Souhaitez-vous une boisson ?", default=False).execute()

        # --- Étape 4 : construction du modèle ---
        
        id_evt = self._get_attr(evt, 'id_evenement')
        if not id_evt:
             print("Erreur : Impossible de trouver l'ID de cet événement.")
             return ConnexionClientVue("Erreur de réservation.")

        resa_in = ReservationModelIn(
            fk_utilisateur=self.user.id_utilisateur,
            fk_evenement=id_evt, 
            bus_aller=bus_aller,
            bus_retour=bus_retour,
            adherent=adherent,
            sam=sam,
            boisson=boisson,
        )

        # --- Étape 5 : enregistrement via le service ---
        try:
            resa_out = self.reservation_service.create_reservation(resa_in)
        except Exception as e:
            print(f"Erreur lors de la création de la réservation : {e}")
            return ConnexionClientVue("Erreur lors de la réservation.")

        if not resa_out:
            print("La réservation n’a pas pu être créée (peut-être déjà existante ?).")
            return ConnexionClientVue("Échec de la réservation.")

        print(f"Réservation confirmée pour {titre_evt} ({date_evt})")

        # --- Étape 6 : e-mail de confirmation ---
        if LOADED_BREVO: # On n'essaie pas si l'import a échoué
            try:
                subject = "Confirmation de votre réservation — BDE Ensai"
                message_text = (
                    f"Bonjour {self.user.prenom} {self.user.nom},\n\n"
                    f"Votre réservation pour l’événement « {titre_evt} » du {date_evt} est confirmée.\n\n"
                    f"Options :\n"
                    f" - Bus aller : {'Oui' if bus_aller else 'Non'}\n"
                    f" - Bus retour : {'Oui' if bus_retour else 'Non'}\n"
                    f" - Adhérent : {'Oui' if adherent else 'Non'}\n"
                    f" - SAM : {'Oui' if sam else 'Non'}\n"
                    f" - Boisson : {'Oui' if boisson else 'Non'}\n\n"
                    "Si vous n’êtes pas à l’origine de cette action, veuillez nous contacter.\n\n"
                    "— L’équipe du BDE Ensai"
                )

                status, _ = send_email_brevo(
                    to_email=self.user.email,
                    subject=subject,
                    message_text=message_text,
                )

                if 200 <= status < 300:
                    print("Un e-mail de confirmation vous a été envoyé.")
                else:
                    print(f"E-mail non envoyé (HTTP {status}).")

            except Exception as exc:
                print(f"Impossible d'envoyer l'e-mail de confirmation : {exc}")

        # --- Étape 7 : retour au menu client ---
        return ConnexionClientVue("Réservation effectuée avec succès.")
