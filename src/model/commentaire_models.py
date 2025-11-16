# src/model/commentaire_models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CommentaireModelIn(BaseModel):
    """
    Modèle Pydantic pour la CRÉATION (IN) d'un commentaire.
    """
    fk_utilisateur: int
    fk_reservation: int
    note: Optional[int] = Field(None, ge=1, le=5) # Note entre 1 et 5
    avis: Optional[str] = None

class CommentaireModelOut(BaseModel):
    """
    Modèle Pydantic pour la LECTURE (OUT) d'un commentaire.
    """
    id_commentaire: int
    fk_utilisateur: int
    fk_reservation: int
    note: Optional[int]
    avis: Optional[str]
    date_commentaire: datetime