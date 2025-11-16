# src/service/commentaire_service.py
from typing import Optional

from dao.commentaire_dao import CommentaireDao
from model.commentaire_models import CommentaireModelIn, CommentaireModelOut

class CommentaireService:
    """
    Service pour la logique métier des commentaires.
    """
    def __init__(self):
        self.dao = CommentaireDao()

    def get_comment_by_reservation(self, id_reservation: int) -> Optional[CommentaireModelOut]:
        """Récupère le commentaire lié à une réservation."""
        return self.dao.find_by_reservation_id(id_reservation)

    def create_comment(self, comm_in: CommentaireModelIn) -> Optional[CommentaireModelOut]:
        """Crée un nouveau commentaire."""
        if comm_in.note is None and (comm_in.avis is None or comm_in.avis.strip() == ""):
            raise ValueError("Un commentaire ne peut pas être vide (ni note, ni avis).")
        
        return self.dao.create(comm_in)

    def update_comment(self, id_commentaire: int, comm_in: CommentaireModelIn) -> Optional[CommentaireModelOut]:
        """Met à jour un commentaire."""
        if comm_in.note is None and (comm_in.avis is None or comm_in.avis.strip() == ""):
            raise ValueError("Un commentaire ne peut pas être vide (ni note, ni avis).")
        
        return self.dao.update(id_commentaire, comm_in)