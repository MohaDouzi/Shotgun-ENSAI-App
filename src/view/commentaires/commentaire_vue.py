# src/view/commentaires/commentaire_vue.py
from InquirerPy import inquirer
from typing import Optional, Any

from view.vue_abstraite import VueAbstraite
from view.session import Session
from service.commentaire_service import CommentaireService
from model.commentaire_models import CommentaireModelIn, CommentaireModelOut
from model.reservation_models import ReservationModelOut


class CommentaireVue(VueAbstraite):
    """
    Vue pour créer ou modifier un commentaire sur une réservation.
    """
    def __init__(self, reservation: ReservationModelOut, commentaire: Optional[CommentaireModelOut] = None, message: str = ""):
        super().__init__(message)
        self.user = Session().utilisateur
        self.service = CommentaireService()
        self.reservation = reservation
        self.commentaire = commentaire

    def afficher(self) -> None:
        """ Affiche l'en-tête de la vue """
        super().afficher()
        if self.commentaire:
            print(f"Modifier votre avis (Réservation #{self.reservation.id_reservation})")
        else:
            print(f"Laisser un avis (Réservation #{self.reservation.id_reservation})")

    def choisir_menu(self) -> Optional[VueAbstraite]:
        
        from view.reservations.mes_reservations_vue import MesReservationsVue
        
        if not self.user:
            return MesReservationsVue("Erreur: Vous n'êtes plus connecté.")

        try:
            # On pré-remplit les champs si un commentaire existe
            note_actuelle = str(self.commentaire.note) if self.commentaire and self.commentaire.note else ""
            avis_actuel = self.commentaire.avis if self.commentaire and self.commentaire.avis else ""

            note_str = inquirer.text(
                message="Votre note (sur 5, laissez vide pour 'Pas de note') :",
                default=note_actuelle,
                validate=lambda n: (n.isdigit() and 1 <= int(n) <= 5) or n == "",
                invalid_message="Doit être un nombre entre 1 et 5, ou vide."
            ).execute()
            
            avis = inquirer.text(
                message="Votre avis (laissez vide pour 'Pas d'avis') :",
                default=avis_actuel
            ).execute()

            # On convertit les réponses
            note_finale = int(note_str) if note_str.isdigit() else None
            avis_final = avis.strip() if avis.strip() else None

            
            # On crée le "formulaire"
            comm_in = CommentaireModelIn(
                fk_utilisateur=self.user.id_utilisateur,
                fk_reservation=self.reservation.id_reservation,
                note=note_finale,
                avis=avis_final
            )

            if self.commentaire:
                # C'est une MISE A JOUR
                resultat = self.service.update_comment(self.commentaire.id_commentaire, comm_in)
                msg = "Avis mis à jour avec succès !"
            else:
                # C'est une CRÉATION
                resultat = self.service.create_comment(comm_in)
                msg = "Avis publié avec succès !"

            if not resultat:
                msg = "Erreur lors de l'enregistrement."

            return MesReservationsVue(msg)

        except ValueError as ve:
            # Erreur levée par le service (ex: commentaire vide)
            return MesReservationsVue(f"Erreur : {ve}")
        except Exception as e:
            return MesReservationsVue(f"Erreur inattendue : {e}")