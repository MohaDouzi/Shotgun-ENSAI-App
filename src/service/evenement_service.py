# src/service/evenement_service.py
from typing import List, Optional
from dao.evenement_dao import EvenementDao
from model.evenement_models import EvenementModelIn, EvenementModelOut

from service.participant_service import ParticipantService
from utils.api_brevo import send_email_brevo


class EvenementService:
    """
    Service pour la gestion des événements.
    Contient la logique métier au-dessus du DAO.
    """

    def __init__(self):
        self.dao = EvenementDao()
        #from service.participant_service import ParticipantService
        self.participant_service = ParticipantService()

    # ---------- READ ----------
    def get_all_events(self, limit: int = 100, offset: int = 0) -> List[EvenementModelOut]:
        """Récupère tous les événements (paginés)."""
        return self.dao.find_all(limit=limit, offset=offset)

    def get_event_by_id(self, id_evenement: int) -> EvenementModelOut:
        """Récupère un événement par son ID, ou lève une erreur s’il n’existe pas."""
        event = self.dao.find_by_id(id_evenement)
        if not event:
            raise ValueError(f"Aucun événement trouvé avec l'id {id_evenement}.")
        return event

    def list_events_with_places(self, limit: int = 100, a_partir_du=None):
        """
        Liste les événements avec leurs places restantes (vue utilisée par ReservationVue).
        """
        return self.dao.lister_avec_places_restantes(limit=limit, a_partir_du=a_partir_du)

    def list_all_events(self, limit: int = 100):
        """
        Liste tous les événements (vue utilisée par StatistiquesInscriptionsVue).
        """
        return self.dao.lister_tous(limit=limit)

    # ---------- CREATE ----------
    def create_event(self, evenement_in: EvenementModelIn) -> EvenementModelOut:
        """Crée un nouvel événement, avec validation minimale."""
        if not evenement_in.titre or evenement_in.titre.strip() == "":
            raise ValueError("Le titre de l'événement est obligatoire.")
        if not evenement_in.date_evenement:
            raise ValueError("La date de l'événement est obligatoire.")
        if evenement_in.capacite is None or evenement_in.capacite <= 0:
            raise ValueError("La capacité doit être un entier positif obligatoire.")
            
        # --- Création en base ---
        evt_out = self.dao.create(evenement_in)

        # ------------------------
        # F08 - Notification email
        # ------------------------
        try:
            emails = self.participant_service.get_all_participants_emails()

            if not emails:
                print("[F08] Aucun participant à notifier.")
                return evt_out

            subject = f"NOUVEL ÉVÉNEMENT — {evt_out.titre}"

            message = (
                f"Bonjour,\n\n"
                f"Un nouvel événement vient d’être créé !\n\n"
                f"Titre   : {evt_out.titre}\n"
                f"Date    : {evt_out.date_evenement}\n"
                f"Ville   : {evt_out.ville or '—'}\n"
                f"Adresse : {evt_out.adresse or '—'}\n"
                f"Statut  : {evt_out.statut}\n\n"
                f"{evt_out.description or ''}\n\n"
                f"L’événement est actuellement **{evt_out.statut}**.\n\n"
                "— L’équipe du BDE Ensai"
            )
            envoyes = 0
            for email in emails:
                status, _ = send_email_brevo(
                    to_email=email,
                    subject=subject,
                    message_text=message
                )
                if 200 <= status < 300:
                    envoyes += 1

            print(f"[F08] Notification envoyée à {envoyes}/{len(emails)} participant(s).")

        except Exception as e:
            print(f"[F08] Erreur lors de l’envoi des mails : {e}")

        return evt_out

    # ---------- UPDATE ----------
    def update_event(self, evenement_out: EvenementModelOut) -> EvenementModelOut:
        """Met à jour un événement existant."""
        existing = self.dao.find_by_id(evenement_out.id_evenement)
        if not existing:
            raise ValueError("Impossible de mettre à jour : événement introuvable.")

        updated = self.dao.update(evenement_out)
        if not updated:
            raise ValueError("Erreur lors de la mise à jour de l'événement.")
        return updated

    # ---------- DELETE ----------
    def delete_event(self, id_evenement: int) -> bool:
        """Supprime un événement existant."""
        existing = self.dao.find_by_id(id_evenement)
        if not existing:
            raise ValueError("Impossible de supprimer : événement introuvable.")
        return self.dao.delete(id_evenement)

