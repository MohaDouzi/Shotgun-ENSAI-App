# src/dao/commentaire_dao.py
from typing import Optional
import logging

from dao.db_connection import DBConnection
from model.commentaire_models import CommentaireModelIn, CommentaireModelOut

logger = logging.getLogger(__name__)

class CommentaireDao:
    """
    DAO pour la table 'commentaire'.
    Gère les opérations CRUD (Create, Read, Update, Delete).
    """

    def find_by_reservation_id(self, id_reservation: int) -> Optional[CommentaireModelOut]:
        """
        Trouve un commentaire par l'ID de la réservation.
        On part du principe qu'il n'y a qu'un seul commentaire par réservation.
        """
        query = "SELECT * FROM commentaire WHERE fk_reservation = %(id_resa)s LIMIT 1"
        params = {"id_resa": id_reservation}

        with DBConnection().getConnexion() as con:
            with con.cursor() as curs:
                curs.execute(query, params)
                row = curs.fetchone()
        
        return CommentaireModelOut(**row) if row else None
    
    def find_all_by_event_id(self, id_evenement: int) -> list:
        """
        Récupère tous les commentaires liés à un événement (via la table reservation).
        Renvoie aussi le nom/prénom de l'auteur.
        """
        query = """
            SELECT c.note, c.avis, u.prenom, u.nom, c.date_commentaire
            FROM commentaire c
            JOIN reservation r ON c.fk_reservation = r.id_reservation
            JOIN utilisateur u ON c.fk_utilisateur = u.id_utilisateur
            WHERE r.fk_evenement = %(id_evt)s
            ORDER BY c.date_commentaire DESC
        """
        params = {"id_evt": id_evenement}

        with DBConnection().getConnexion() as con:
            with con.cursor() as curs:
                curs.execute(query, params)
                return curs.fetchall()

    def create(self, comm_in: CommentaireModelIn) -> Optional[CommentaireModelOut]:
        """Crée un nouveau commentaire."""
        query = """
            INSERT INTO commentaire (fk_utilisateur, fk_reservation, note, avis)
            VALUES (%(fk_utilisateur)s, %(fk_reservation)s, %(note)s, %(avis)s)
            RETURNING id_commentaire, fk_utilisateur, fk_reservation, note, avis, date_commentaire
        """
        params = comm_in.model_dump()

        with DBConnection().getConnexion() as con:
            with con.cursor() as curs:
                try:
                    curs.execute(query, params)
                    row = curs.fetchone()
                    con.commit()
                    return CommentaireModelOut(**row) if row else None
                except Exception as e:
                    con.rollback()
                    logger.exception(f"Erreur DAO (create commentaire): {e}")
                    return None

    def update(self, id_commentaire: int, comm_in: CommentaireModelIn) -> Optional[CommentaireModelOut]:
        """Met à jour un commentaire existant (note et avis)."""
        query = """
            UPDATE commentaire
            SET note = %(note)s, avis = %(avis)s, date_commentaire = NOW()
            WHERE id_commentaire = %(id_comm)s
            RETURNING id_commentaire, fk_utilisateur, fk_reservation, note, avis, date_commentaire
        """
        params = {
            "note": comm_in.note,
            "avis": comm_in.avis,
            "id_comm": id_commentaire
        }

        with DBConnection().getConnexion() as con:
            with con.cursor() as curs:
                try:
                    curs.execute(query, params)
                    row = curs.fetchone()
                    con.commit()
                    return CommentaireModelOut(**row) if row else None
                except Exception as e:
                    con.rollback()
                    logger.exception(f"Erreur DAO (update commentaire): {e}")
                    return None