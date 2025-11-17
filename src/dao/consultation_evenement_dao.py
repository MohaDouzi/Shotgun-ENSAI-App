# src/dao/consultation_evenement_dao.py
from typing import List, Optional, Dict, Any
from datetime import date

from psycopg2.extras import RealDictCursor

from dao.db_connection import DBConnection
from model.evenement_models import EvenementModelOut


class ConsultationEvenementDao:
    """
    DAO de consultation (lecture seule) des événements.
    Fournit des méthodes pratiques pour lister et filtrer les événements.
    """

    def lister_tous(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "date_evenement ASC, id_evenement ASC",
    ) -> List[Dict[str, Any]]:
        """
        Liste paginée de tous les événements avec TOUTES les stats (places, avis, SAM, etc.).
        Retourne des dictionnaires enrichis.
        """
        query = (
            "WITH resa AS ( "
            "   SELECT fk_evenement, "
            "          COUNT(*) AS nb_resa, "
            "          COUNT(CASE WHEN sam THEN 1 END) AS nb_sam, "
            "          COUNT(CASE WHEN adherent THEN 1 END) AS nb_adh "
            "   FROM reservation "
            "   GROUP BY fk_evenement "
            "), "
            "comm AS ( "
            "   SELECT r.fk_evenement, "
            "          AVG(c.note) as avg_note, "
            "          COUNT(c.id_commentaire) as comment_count "
            "   FROM commentaire c "
            "   JOIN reservation r ON c.fk_reservation = r.id_reservation "
            "   WHERE c.note IS NOT NULL "
            "   GROUP BY r.fk_evenement "
            ") "
            "SELECT e.id_evenement, e.fk_utilisateur, e.titre, e.adresse, e.ville, "
            "       e.date_evenement, e.description, e.capacite, e.categorie, e.statut, e.date_creation, "
            "       (e.capacite - COALESCE(r.nb_resa, 0)) AS places_restantes, "
            "       COALESCE(r.nb_resa, 0) AS nb_inscrits, "
            "       COALESCE(r.nb_sam, 0) AS nb_sam, "
            "       COALESCE(r.nb_adh, 0) AS nb_adh, "
            "       c.avg_note, "
            "       COALESCE(c.comment_count, 0) AS comment_count "
            "FROM evenement e "
            "LEFT JOIN resa r ON r.fk_evenement = e.id_evenement "
            "LEFT JOIN comm c ON c.fk_evenement = e.id_evenement "
            f"ORDER BY {order_by} "
            "LIMIT %(limit)s OFFSET %(offset)s"
        )
        params = {"limit": max(limit, 0), "offset": max(offset, 0)}

        with DBConnection().getConnexion() as con:
            # On utilise RealDictCursor pour avoir des dictionnaires directement
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, params)
                rows = curs.fetchall()

        # RealDictCursor renvoie déjà des dict-like, mais on force le cast en dict pur
        return [dict(row) for row in rows]


    def lister_disponibles(
        self,
        limit: int = 100,
        offset: int = 0,
        a_partir_du: Optional[date] = None,
    ) -> List[EvenementModelOut]:
        """
        Liste simple des événements 'disponible en ligne'.
        Retourne des OBJETS EvenementModelOut (pas de stats calculées).
        """
        where = ["statut = 'disponible en ligne'"]
        params: Dict[str, Any] = {"limit": max(limit, 0), "offset": max(offset, 0)}

        if a_partir_du is not None:
            where.append("date_evenement >= %(dmin)s")
            params["dmin"] = a_partir_du

        query = (
            "SELECT id_evenement, fk_utilisateur, titre, adresse, ville, "
            "       date_evenement, description, capacite, categorie, statut, date_creation "
            "FROM evenement "
            f"WHERE {' AND '.join(where)} "
            "ORDER BY date_evenement ASC, id_evenement ASC "
            "LIMIT %(limit)s OFFSET %(offset)s"
        )

        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, params)
                rows = curs.fetchall()

        return [EvenementModelOut(**row) for row in rows]


    def lister_avec_places_restantes(
        self,
        limit: int = 100,
        offset: int = 0,
        seulement_disponibles: bool = True,
        a_partir_du: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Liste des événements avec calcul des places restantes ET des avis.
        Retourne des DICTIONNAIRES enrichis.
        """
        where = []
        params: Dict[str, Any] = {"limit": max(limit, 0), "offset": max(offset, 0)}

        if seulement_disponibles:
            where.append("e.statut = 'disponible en ligne'")
        if a_partir_du is not None:
            where.append("e.date_evenement >= %(dmin)s")
            params["dmin"] = a_partir_du

        where_clause = f"WHERE {' AND '.join(where)} " if where else ""

        query = (
            "WITH resa AS ( "
            "   SELECT fk_evenement, COUNT(*) AS nb_resa "
            "   FROM reservation "
            "   GROUP BY fk_evenement "
            "), "
            "comm AS ( "
            "   SELECT r.fk_evenement, "
            "          AVG(c.note) as avg_note, "
            "          COUNT(c.id_commentaire) as comment_count "
            "   FROM commentaire c "
            "   JOIN reservation r ON c.fk_reservation = r.id_reservation "
            "   WHERE c.note IS NOT NULL "
            "   GROUP BY r.fk_evenement "
            ") "
            "SELECT e.id_evenement, e.fk_utilisateur, e.titre, e.adresse, e.ville, "
            "       e.date_evenement, e.description, e.capacite, e.categorie, e.statut, e.date_creation, "
            "       (e.capacite - COALESCE(r.nb_resa, 0)) AS places_restantes, "
            "       c.avg_note, "
            "       COALESCE(c.comment_count, 0) AS comment_count "
            "FROM evenement e "
            "LEFT JOIN resa r ON r.fk_evenement = e.id_evenement "
            "LEFT JOIN comm c ON c.fk_evenement = e.id_evenement "
            f"{where_clause}"
            "ORDER BY e.date_evenement ASC, e.id_evenement ASC "
            "LIMIT %(limit)s OFFSET %(offset)s"
        )

        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, params)
                rows = curs.fetchall()

        return [dict(row) for row in rows]


    def rechercher(
        self,
        ville: Optional[str] = None,
        categorie: Optional[str] = None,
        statut: Optional[str] = None,
        date_min: Optional[date] = None,
        date_max: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EvenementModelOut]:
        """
        Recherche d'événements avec filtres.
        Retourne des OBJETS EvenementModelOut.
        """
        where = []
        params: Dict[str, Any] = {"limit": max(limit, 0), "offset": max(offset, 0)}

        if ville:
            where.append("ville ILIKE %(ville)s")
            params["ville"] = f"%{ville}%"
        if categorie:
            where.append("categorie = %(categorie)s")
            params["categorie"] = categorie
        if statut:
            where.append("statut = %(statut)s")
            params["statut"] = statut
        if date_min:
            where.append("date_evenement >= %(date_min)s")
            params["date_min"] = date_min
        if date_max:
            where.append("date_evenement <= %(date_max)s")
            params["date_max"] = date_max

        where_clause = f"WHERE {' AND '.join(where)} " if where else ""
        
        query = (
            "SELECT id_evenement, fk_utilisateur, titre, adresse, ville, "
            "       date_evenement, description, capacite, categorie, statut, date_creation "
            "FROM evenement "
            f"{where_clause}"
            "ORDER BY date_evenement ASC, id_evenement ASC "
            "LIMIT %(limit)s OFFSET %(offset)s"
        )

        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, params)
                rows = curs.fetchall()

        return [EvenementModelOut(**row) for row in rows]