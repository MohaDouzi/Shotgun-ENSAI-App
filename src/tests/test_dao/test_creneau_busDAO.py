import os
import uuid
from datetime import datetime

import pytest

from unittest.mock import patch, MagicMock

from utils.reset_database import ResetDatabase
from utils.securite import hash_password

from dao.creneau_bus_dao import CreneauBusDao
from model.creneauBus_models import CreneauBusModelIn, CreneauBusModelOut


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initialisation des données de test"""
    with patch.dict(os.environ, {"SCHEMA": "projet_test_dao"}):
        ResetDatabase().lancer(test_dao=True)
        yield


def test_row_to_model():
    """ Vérifie qu'une ligne SQL (dict) soit convertie en objet Pydantic CreneauBusModelOut."""
    # GIVEN
    row = {"id_bus": 1,
           "fk_evenement": 1,
           "matricule": "BUS-002",
           "nombre_places": 50,
           "direction": "aller",
           "description": "Bus 1 aller"}

    # WHEN
    creneau_bus = CreneauBusDao()._row_to_model(row)

    # THEN
    assert isinstance(creneau_bus, CreneauBusModelOut)


def test_find_by_id():
    """Récupère le créneau d'un bus par l'identifiant """

    # GIVEN
    id_bus = 3

    # WHEN
    bus = CreneauBusDao().find_by_id(id_bus)

    # THEN
    assert bus is not None


def test_find_by_event():
    """Récupère les bus pour un événement donné """
    # GIVEN
    id_evenement = 1

    # WHEN
    bus = CreneauBusDao().find_by_event(id_evenement)

    # THEN
    assert bus is not None


def test_find_by_description():
    """ Récupère le bus par sa description"""
    # GIVEN
    description = "Bus 1 aller"

    # WHEN
    bus = CreneauBusDao().find_by_description(description)

    # THEN
    assert bus is not None


def test_find_all():
    """ Récupère tous les bus """
    # GIVEN

    # WHEN
    bus = CreneauBusDao().find_all()

    # THEN
    assert isinstance(bus, list)
    for j in bus:
        assert isinstance(j, CreneauBusModelOut)
    assert len(bus) >= 2


def test_exists_description():
    """Vérifie l'unicité de la description."""
    # GIVEN
    description = "Bus 3 retour"

    # WHEN
    unique_description = CreneauBusDao().exists_description(description)

    # THEN
    assert unique_description == 1


def test_create():
    """ Création d'un créneau de bus """

    # GIVEN
    bus = CreneauBusModelIn(fk_evenement=4, matricule="BUS-002", nombre_places=50,
                            direction="aller", description="Bus 5 aller")

    # WHEN
    creation_ok = CreneauBusDao().create(bus)

    # THEN
    assert creation_ok


def test_update():
    """Met à jour un créneau de bus"""

    # GIVEN
    new_matricule = "BUS-030"
    bus = CreneauBusModelOut(id_bus=4, fk_evenement=2, new_matricule=new_matricule,
                             nombre_places=50, direction="retour", description="Bus 2 retour")

    # WHEN
    modification_ok = CreneauBusDao().update(bus, bus.id_bus)

    # THEN
    assert modification_ok


def test_update_places():
    """Met à jour le nombre de places d'un bus"""

    # GIVEN
    new_places = 70
    bus = CreneauBusModelOut(id_bus=1, fk_evenement=1, matricule="BUS-002",
                             nombre_places=new_places, direction="aller", description="Bus 1 aller")

    # WHEN
    modification_ok = CreneauBusDao().update_places(bus.id_bus, new_places)

    # THEN
    assert modification_ok


def test_delete():
    """ Supprime un créneau de bus """

    # GIVEN
    dao = CreneauBusDao()
    bus = dao.find_by_id(3)
    assert bus is not None

    # WHEN
    suppression_ok = CreneauBusDao().delete(bus.id_bus)

    # THEN
    assert suppression_ok


def test_count_for_event():
    """Compte le nombre de bus rattachés à un événement."""

    # GIVEN
    id_event = 1

    # WHEN
    # Patch du curseur pour renvoyer un tuple au lieu d'un dict
    with patch("dao.creneau_bus_dao.DBConnection.getConnexion") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        nbre_bus = CreneauBusDao().count_for_event(id_event)

    # THEN
    assert isinstance(nbre_bus, int)
    assert nbre_bus >= 0


def test_get_capacite_totale():
    """ Calcule la somme des places pour un événement et une direction."""
    # GIVEN
    id_event = 1
    direction = "retour"

    # WHEN
    places = CreneauBusDao().get_capacite_totale(id_event, direction)

    # THEN
    assert isinstance(places, int)
    assert places > 0
