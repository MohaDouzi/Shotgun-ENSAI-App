from unittest.mock import MagicMock

from service.utilisateur_service import UtilisateurService
from dao.utilisateur_dao import UtilisateurDao
from business_object.Utilisateur import Utilisateur


liste_joueurs = [
    Utilisateur(email="alice.dupont@gmail.com", prenom="Alice", nom="Dupont", 
                motDePasse='$2b$12$/px.xnw.CVDEBCVzNn/tleT2B3AStNTpXpOPkGOwrNQ3GrX7.lfrm'),
    Joueur(pseudo="lea", age="10", mail="lea@mail.fr", mdp="0000"),
    Joueur(pseudo="gg", age="10", mail="gg@mail.fr", mdp="abcd"),
]
elf.email = email
        self.prenom = prenom
        self.nom = nom
        self.numeroTel = numeroTel
        self.motDePasse = motDePasse

def test_creer_ok():
    """ "Création de Joueur réussie"""

    # GIVEN
    pseudo, mdp, age, mail, fan_pokemon = "jp", "1234", 15, "z@mail.oo", True
    JoueurDao().creer = MagicMock(return_value=True)

    # WHEN
    joueur = JoueurService().creer(pseudo, mdp, age, mail, fan_pokemon)

    # THEN
    assert joueur.pseudo == pseudo