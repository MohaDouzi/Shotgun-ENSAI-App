from unittest.mock import MagicMock, Mock

from service.evenement_service import EvenementService
from dao.evenement_dao import EvenementDao
from business_object.Evenement import Evenement
from model.evenement_models import EvenementModelIn, EvenementModelOut


def test_create_event():
    """ Création d'un événement"""

    # GIVEN
    evenement = EvenementModelIn(fk_transport=1, titre="Sortie Escalade", adresse="2 rue de l'Hôtel Dieu", ville="Rennes",
                                 date_evenement="2026-01-26", description="Initiation à l'escalade",
                                 capacite=20, categorie="Sport", statut="pas encore finalisé")

    # WHEN
    nvel_event = EvenementService().create_event(evenement)

    # THEN
    assert nvel_event is not None


def test_get_all_events():
    """ Récupère tous les événements """
    # GIVEN

    # WHEN
    events = EvenementService.get_all_events()

    # THEN
    assert isinstance(events, list)
    for j in events:
        assert isinstance(j, EvenementModelOut)
    assert len(events) >= 2
