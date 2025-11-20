# src/view/reservations/mes_reservations_vue.py
from InquirerPy import inquirer
from typing import Optional, Any

from view.vue_abstraite import VueAbstraite
from view.session import Session
from service.reservation_service import ReservationService
from service.evenement_service import EvenementService
from service.commentaire_service import CommentaireService

from view.commentaires.commentaire_vue import CommentaireVue


class MesReservationsVue(VueAbstraite):
    """
    Vue interactive pour afficher et gérer les réservations d'un utilisateur.
    Permet de sélectionner une réservation pour y ajouter/modifier un commentaire.
    """

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.session = Session()
        self.user = self.session.utilisateur
        self.reservation_service = ReservationService()
        self.evenement_service = EvenementService()
        self.commentaire_service = CommentaireService()
    
    @staticmethod
    def _get_attr(obj: Any, key: str, default=None):
        if obj is None: return default
        if isinstance(obj, dict): return obj.get(key, default)
        return getattr(obj, key, default)

    def afficher(self):
        """
        Affiche simplement l'en-tête de la vue.
        """
        super().afficher()

    def choisir_menu(self) -> Optional[VueAbstraite]:
        """
        Affiche la liste des réservations comme un menu sélectionnable.
        """
        from view.client.connexion_client_vue import ConnexionClientVue
        from view.administrateur.connexion_admin_vue import ConnexionAdminVue

        if not self.session.est_connecte() or not self.user:
            print("Vous n'êtes pas connecté.")
            return ConnexionClientVue()

        # On détermine la vue de retour en fonction du rôle
        if self.user.administrateur:
            vue_de_retour = ConnexionAdminVue
            label_retour = "--- Retour au menu admin ---"
        else:
            vue_de_retour = ConnexionClientVue
            label_retour = "--- Retour au menu client ---"

        print(f"Vos Réservations ({self.user.prenom})")

        try:
            # 1. On récupère les réservations
            reservations = self.reservation_service.get_reservations_by_user(self.user.id_utilisateur)
            
            if not reservations:
                print("\nVous n'avez aucune réservation pour le moment.")
                input("\n(Entrée) pour continuer...")
                return vue_de_retour()

            # 2. Création du menu interactif
            choices_reservations = []
            
            for res in reservations:
                evt = None
                titre_evt = f"Événement #{getattr(res, 'fk_evenement', 'N/A')}"
                try:
                    if getattr(res, "fk_evenement", None):
                        evt = self.evenement_service.get_event_by_id(res.fk_evenement)
                        if evt:
                            titre_evt = f"{getattr(evt, 'titre', 'N/A')} (le {getattr(evt, 'date_evenement', 'N/A')})"
                except Exception:
                    pass

                # 3. LOGIQUE DES COMMENTAIRES
                commentaire_existant = self.commentaire_service.get_comment_by_reservation(res.id_reservation)
                
                if commentaire_existant:
                    action_str = "Consulter/Modifier votre avis"
                    valeur = {"reservation": res, "commentaire": commentaire_existant}
                else:
                    action_str = "Laisser un avis"
                    valeur = {"reservation": res, "commentaire": None}

                choices_reservations.append({
                    "name": f"[{titre_evt}] - {action_str}",
                    "value": valeur
                })

            choices_reservations.append({"name": label_retour, "value": None})

            # 4. On affiche le menu
            selection = inquirer.select(
                message="Sélectionnez une réservation pour la commenter :",
                choices=choices_reservations,
            ).execute()

            # 5. On gère la sélection
            if selection is None:
                return vue_de_retour()

            return CommentaireVue(
                reservation=selection["reservation"],
                commentaire=selection["commentaire"]
            )

        except Exception as e:
            print(f"\n Erreur lors de la récupération de vos réservations : {e}")
            input("\n(Entrée) pour continuer...")
            return vue_de_retour() 