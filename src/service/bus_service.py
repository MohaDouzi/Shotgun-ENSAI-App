# src/service/bus_service.py
from typing import List, Optional

from dao.creneau_bus_dao import CreneauBusDao
from model.creneauBus_models import CreneauBusModelIn, CreneauBusModelOut


class BusService:
    """
    Service pour la gestion des créneaux de bus (table `bus`).
    Contient la logique métier et délègue les opérations au DAO.
    """

    def __init__(self):
        self.dao = CreneauBusDao()

    def ajouter_bus_evenement(
        self, 
        id_evenement: int, 
        places_aller: int, 
        desc_aller: str,
        places_retour: int, 
        desc_retour: str
    ) -> None:
        """
        Crée automatiquement les objets CreneauBusModelIn pour un événement.
        """
        # 1. Gestion du Bus ALLER
        if places_aller > 0:
            bus_aller = CreneauBusModelIn(
                fk_evenement=id_evenement,
                direction='aller',
                nombre_places=places_aller,
                matricule=f"BA-{id_evenement}", 
                description=desc_aller or f"Bus Aller - Event {id_evenement}"
            )
            try:
                self.create_bus(bus_aller)
            except ValueError as e:
                print(f"Impossible de créer le bus aller : {e}")

        # 2. Gestion du Bus RETOUR
        if places_retour > 0:
            bus_retour = CreneauBusModelIn(
                fk_evenement=id_evenement,
                direction='retour',
                nombre_places=places_retour,
                matricule=f"BR-{id_evenement}",
                description=desc_retour or f"Bus Retour - Event {id_evenement}"
            )
            try:
                self.create_bus(bus_retour)
            except ValueError as e:
                print(f"Impossible de créer le bus retour : {e}")

    def get_capacite(self, id_evenement: int, direction: str) -> int:
        """
        Récupère la capacité totale pour une direction donnée via le DAO.
        """
        return self.dao.get_capacite_totale(id_evenement, direction)

    # ---------- CRUD CLASSIQUE ----------

    def create_bus(self, bus_in: CreneauBusModelIn) -> CreneauBusModelOut:
        """
        Crée un nouveau créneau de bus après vérifications métier.
        """
        if not bus_in.description or bus_in.description.strip() == "":
            raise ValueError("La description du bus est obligatoire.")
        
        if bus_in.nombre_places <= 0:
            raise ValueError("Le nombre de places doit être supérieur à zéro.")
        
        if self.dao.exists_description(bus_in.description):
            raise ValueError(f"Un bus avec la description '{bus_in.description}' existe déjà.")

        created = self.dao.create(bus_in)
        if not created:
            raise ValueError("Erreur lors de la création du bus.")
        return created

    # ---------- READ ----------
    def get_all_buses(self, limit: int = 100, offset: int = 0) -> List[CreneauBusModelOut]:
        """Retourne la liste paginée de tous les bus."""
        return self.dao.find_all(limit=limit, offset=offset)

    def get_bus_by_id(self, id_bus: int) -> CreneauBusModelOut:
        """Retourne un bus par son ID, ou lève une erreur si non trouvé."""
        bus = self.dao.find_by_id(id_bus)
        if not bus:
            raise ValueError(f"Aucun bus trouvé avec l'id {id_bus}.")
        return bus

    def get_buses_by_event(self, id_evenement: int) -> List[CreneauBusModelOut]:
        """Retourne tous les bus liés à un événement."""
        return self.dao.find_by_event(id_evenement)

    def get_bus_by_description(self, description: str) -> CreneauBusModelOut:
        """Retourne un bus par sa description."""
        bus = self.dao.find_by_description(description)
        if not bus:
            raise ValueError(f"Aucun bus trouvé avec la description '{description}'.")
        return bus

    # ---------- UPDATE ----------
    def update_bus(self, bus: CreneauBusModelIn, id_bus: int) -> CreneauBusModelOut:
        """Met à jour un bus existant (tous champs)."""
        existing = self.dao.find_by_id(id_bus)
        if not existing:
            raise ValueError("Impossible de mettre à jour : bus introuvable.")
        
        if bus.nombre_places <= 0:
            raise ValueError("Le nombre de places doit être supérieur à zéro.")
        
        if bus.description != existing.description and self.dao.exists_description(bus.description):
            raise ValueError(f"Un autre bus utilise déjà la description '{bus.description}'.")

        updated = self.dao.update(bus, id_bus)
        if not updated:
            raise ValueError("Erreur lors de la mise à jour du bus.")
        return updated

    def update_places(self, id_bus: int, nombre_places: int) -> CreneauBusModelOut:
        """Met à jour uniquement le nombre de places."""
        if nombre_places <= 0:
            raise ValueError("Le nombre de places doit être supérieur à zéro.")
        
        existing = self.dao.find_by_id(id_bus)
        if not existing:
            raise ValueError("Bus introuvable pour mise à jour du nombre de places.")
        
        updated = self.dao.update_places(id_bus, nombre_places)
        if not updated:
            raise ValueError("Erreur lors de la mise à jour du nombre de places.")
        return updated

    # ---------- DELETE ----------
    def delete_bus(self, id_bus: int) -> bool:
        """Supprime un bus par son ID."""
        existing = self.dao.find_by_id(id_bus)
        if not existing:
            raise ValueError("Impossible de supprimer : bus introuvable.")
        return self.dao.delete(id_bus)

    # ---------- HELPERS ----------
    def count_buses_for_event(self, id_evenement: int) -> int:
        """Retourne le nombre de bus pour un événement donné."""
        return self.dao.count_for_event(id_evenement)