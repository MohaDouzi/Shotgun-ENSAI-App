from unittest.mock import MagicMock, Mock

from service.reservation_service import ReservationService
from dao.reservation_dao import ReservationDao
from business_object.Reservation import Reservation
from model.reservation_models import ReservationModelIn, ReservationModelOut


def test_create_reservation():
    """ "Création d'une réservation réussie"""

    # GIVEN
    reservation = ReservationModelIn(fk_utilisateur=1, fk_evenement=4, bus_aller=True,
                                     bus_retour=True, adherent=False, sam=False, boisson=True)

    # WHEN
    nvelle_reservation = ReservationService().create_reservation(reservation)

    # THEN
    assert nvelle_reservation is not None
