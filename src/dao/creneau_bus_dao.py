# src/dao/creneau_bus_dao.py
from typing import List, Optional, Dict, Any
from psycopg2.extras import RealDictCursor

from dao.db_connection import DBConnection
from model.creneauBus_models import CreneauBusModelIn, CreneauBusModelOut


class CreneauBusDao:
    """
    DAO pour la gestion des créneaux de bus (table `bus`).
    """

    # ------------- HELPERS -------------
    @staticmethod
    def _row_to_model(row: dict) -> CreneauBusModelOut:
        """Convertit une ligne SQL (dict) en objet Pydantic CreneauBusModelOut."""
        # Pydantic est intelligent : il mappe les champs automatiquement
        return CreneauBusModelOut(**row)

    # ------------- CREATE -------------
    def create(self, bus_in: CreneauBusModelIn) -> Optional[CreneauBusModelOut]:
        """
        Insère un bus à partir d'un CreneauBusModelIn.
        """
        query = """
            INSERT INTO bus (fk_evenement, matricule, nombre_places, direction, description)
            VALUES (%(fk_evenement)s, %(matricule)s, %(nombre_places)s, %(direction)s, %(description)s)
            RETURNING id_bus, fk_evenement, matricule, nombre_places, direction, description
        """
        params = bus_in.model_dump()

        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                try:
                    curs.execute(query, params)
                    row = curs.fetchone()
                    con.commit()
                except Exception as e:
                    con.rollback()
                    print(f"Erreur DAO (create bus): {e}")
                    return None

        return self._row_to_model(row) if row else None

    # ------------- READ -------------
    def find_by_id(self, id_bus: int) -> Optional[CreneauBusModelOut]:
        query = "SELECT * FROM bus WHERE id_bus = %(id)s"
        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, {"id": id_bus})
                row = curs.fetchone()
        return self._row_to_model(row) if row else None

    def find_by_event(self, id_evenement: int) -> List[CreneauBusModelOut]:
        """Récupère tous les bus d'un événement."""
        query = "SELECT * FROM bus WHERE fk_evenement = %(id_evenement)s ORDER BY id_bus"
        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, {"id_evenement": id_evenement})
                rows = curs.fetchall()
        return [self._row_to_model(r) for r in rows]

    def find_by_description(self, description: str) -> Optional[CreneauBusModelOut]:
        query = "SELECT * FROM bus WHERE description = %(description)s"
        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, {"description": description})
                row = curs.fetchone()
        return self._row_to_model(row) if row else None
    
    def exists_description(self, description: str) -> bool:
        """Vérifie l'unicité de la description."""
        return self.find_by_description(description) is not None
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[CreneauBusModelOut]:
        query = "SELECT * FROM bus LIMIT %(limit)s OFFSET %(offset)s"
        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, {"limit": limit, "offset": offset})
                rows = curs.fetchall()
        return [self._row_to_model(r) for r in rows]

    # ------------- CALCULS (Capacité) -------------
    def get_capacite_totale(self, id_evenement: int, direction: str) -> int:
        """
        Calcule la somme des places pour un événement et une direction.
        """
        query = """
            SELECT SUM(nombre_places) as total
            FROM bus
            WHERE fk_evenement = %(id)s AND direction = %(dir)s
        """
        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute(query, {"id": id_evenement, "dir": direction})
                row = curs.fetchone()
        
        val = row.get('total') if row else 0
        return int(val) if val else 0

    # ------------- UPDATE / DELETE -------------
    
    def update(self, bus_in: CreneauBusModelIn, id_bus: int) -> Optional[CreneauBusModelOut]:
        """Met à jour un bus."""
        query = """
            WITH updated AS (
                UPDATE bus
                SET fk_evenement = %(fk_evenement)s,
                    matricule    = %(matricule)s,
                    nombre_places= %(nombre_places)s,
                    direction    = %(direction)s,
                    description  = %(description)s
                WHERE id_bus = %(id_bus)s
                RETURNING id_bus, fk_evenement, matricule, nombre_places, direction, description
            )
            SELECT * FROM updated
        """
        params = bus_in.model_dump()
        params["id_bus"] = id_bus

        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                try:
                    curs.execute(query, params)
                    row = curs.fetchone()
                    con.commit()
                except Exception as e:
                    con.rollback()
                    print(f"Erreur DAO (update bus): {e}")
                    return None
        return self._row_to_model(row) if row else None

    def update_places(self, id_bus: int, nombre_places: int) -> Optional[CreneauBusModelOut]:
        """
        Met à jour uniquement le nombre de places.
        """
        query = """
            WITH updated AS (
                UPDATE bus
                SET nombre_places = %(nombre_places)s
                WHERE id_bus = %(id_bus)s
                RETURNING id_bus, fk_evenement, matricule, nombre_places, direction, description
            )
            SELECT * FROM updated
        """
        with DBConnection().getConnexion() as con:
            with con.cursor(cursor_factory=RealDictCursor) as curs:
                try:
                    curs.execute(query, {"id_bus": id_bus, "nombre_places": nombre_places})
                    row = curs.fetchone()
                    con.commit()
                except Exception as e:
                    con.rollback()
                    print(f"Erreur DAO (update_places): {e}")
                    return None
        return self._row_to_model(row) if row else None

    def delete(self, id_bus: int) -> bool:
        query = "DELETE FROM bus WHERE id_bus = %(id)s"
        with DBConnection().getConnexion() as con:
            with con.cursor() as curs:
                curs.execute(query, {"id": id_bus})
                con.commit()
                return curs.rowcount > 0

    def count_for_event(self, id_evenement: int) -> int:
        """Nombre de bus rattachés à un événement."""
        query = "SELECT COUNT(*) AS c FROM bus WHERE fk_evenement = %(id)s"
        with DBConnection().getConnexion() as con:
            with con.cursor() as curs:
                curs.execute(query, {"id": id_evenement})
                row = curs.fetchone()
        return int(row[0]) if row else 0