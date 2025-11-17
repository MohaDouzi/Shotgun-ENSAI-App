# src/model/creneauBus_models.py
from pydantic import BaseModel, constr, Field
from typing import Optional, Literal

class CreneauBusModelIn(BaseModel):
    """
    Modèle d'entrée pour la création d'un créneau de bus.
    """
    fk_evenement: Optional[int] = None
    matricule: Optional[str] = None
    nombre_places: int = Field(..., gt=0)
    direction: Literal["aller", "retour"] = "aller"
    description: str

class CreneauBusModelOut(BaseModel):
    """
    Modèle de sortie pour la lecture d'un créneau de bus.
    """
    id_bus: int
    fk_evenement: Optional[int] = None
    matricule: Optional[str] = None
    nombre_places: int
    direction: Literal["aller", "retour"]
    description: str