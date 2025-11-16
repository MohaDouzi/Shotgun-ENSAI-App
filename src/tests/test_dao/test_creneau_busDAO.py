import os
import uuid
from datetime import datetime

import pytest

from unittest.mock import patch

from utils.reset_database import ResetDatabase
from utils.securite import hash_password

from dao.creneau_bus_dao import CreneauBus
from model.creneauBus_models import CreneauBusModelIn, CreneauBusModelOut