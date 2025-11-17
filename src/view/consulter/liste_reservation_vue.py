# view/consulter/liste_reservation_vue.py
from typing import Optional, Any, Dict, List
from datetime import date
from InquirerPy import inquirer

from view.vue_abstraite import VueAbstraite
from view.session import Session

from service.consultation_evenement_service import ConsultationEvenementService
from service.reservation_service import ReservationService
from service.utilisateur_service import UtilisateurService
from service.commentaire_service import CommentaireService


class ListeInscritsEvenementVue(VueAbstraite):
    """
    Vue admin : liste des inscrits en temps réel à un événement.
    - Sélection de l'événement
    - Affichage des inscrits (Nom, Prénom, Email, options)
    - Totaux (participants, bus aller/retour, adhérents)
    - Rafraîchissement manuel
    """

    def __init__(self, message: str = "", id_evenement: Optional[int] = None):
        super().__init__(message)
        self.service_evt = ConsultationEvenementService()
        self.service_resa = ReservationService()
        self.service_user = UtilisateurService()
        self.service_comm = CommentaireService()
        self.id_evenement = id_evenement
        self._evenement_cache: Any = None 

    # ----------------- Helpers -----------------
    @staticmethod
    def _is_admin() -> bool:
        user = Session().utilisateur
        return bool(user and getattr(user, "administrateur", False))

    @staticmethod
    def _get_attr(obj: Any, key: str, default=None):
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    
    def _select_evenement(self) -> Optional[int]:
        """
        Laisse l'admin choisir un événement PARMI TOUS (passés, futurs, brouillons).
        """
        choices: List[Dict[str, Any]] = []

        try:
            tous = self.service_evt.lister_tous(limit=500)
            
            if not tous:
                print("Aucun événement trouvé en base.")
                return None

            for e in tous:
                id_evt = e.get("id_evenement")
                date_evt = str(e.get("date_evenement", ""))[:10]
                titre = e.get("titre", "—")
                statut = e.get("statut", "")
                
                label = f"[{id_evt}] {date_evt} | {titre} ({statut})"
                choices.append({"name": label, "value": id_evt})

        except Exception as e:
            print(f"Erreur lors du chargement des événements : {e}")
            return None

        choices.append({"name": "--- Retour ---", "value": None})

        return inquirer.select(
            message="Sélectionnez un événement pour voir les inscrits :",
            choices=choices,
        ).execute()

    def _fetch_evenement(self, id_evenement: int):
        """
        Récupère les détails de l'événement sélectionné.
        """
        try:
            tous = self.service_evt.lister_tous(limit=500)
            for e in tous:
                if e.get("id_evenement") == id_evenement:
                    return e
        except Exception:
            pass

        try:
            return self.service_evt.get_event_by_id(id_evenement)
        except Exception:
            return None

    def _load_inscrits(self, id_evenement: int) -> List[Dict[str, Any]]:
        """Retourne la liste des inscrits enrichie avec les infos utilisateur ET leur avis."""
        inscrits: List[Dict[str, Any]] = []
        try:
            reservations = self.service_resa.get_reservations_by_event(id_evenement)
        except Exception as exc:
            print(f"Erreur lors de la récupération des réservations : {exc}")
            return []

        for r in reservations:
            user = None
            commentaire = None 
            try:
                user = self.service_user.get_user_by_id(r.fk_utilisateur)
            except Exception:
                pass
            
            try:
                commentaire = self.service_comm.get_comment_by_reservation(r.id_reservation)
            except Exception:
                pass 

            inscrits.append(
                {
                    "id_reservation": getattr(r, "id_reservation"),
                    "nom": getattr(user, "nom", "—") if user else "—",
                    "prenom": getattr(user, "prenom", "—") if user else "—",
                    "email": getattr(user, "email", "—") if user else "—",
                    "bus_aller": bool(getattr(r, "bus_aller", False)),
                    "bus_retour": bool(getattr(r, "bus_retour", False)),
                    "adherent": bool(getattr(r, "adherent", False)),
                    "sam": bool(getattr(r, "sam", False)),
                    "boisson": bool(getattr(r, "boisson", False)),
                    "date_reservation": getattr(r, "date_reservation", None),
                    "commentaire_note": self._get_attr(commentaire, 'note'), 
                    "commentaire_avis": self._get_attr(commentaire, 'avis') 
                }
            )
        return inscrits

    def _print_header(self):
        titre = self._get_attr(self._evenement_cache, "titre", "—")
        date_evt = self._get_attr(self._evenement_cache, "date_evenement", "—")
        ville = self._get_attr(self._evenement_cache, "ville")
        adresse = self._get_attr(self._evenement_cache, "adresse")
        lieu = ville or adresse or "—"
        pr = None
        if isinstance(self._evenement_cache, dict):
            pr = self._evenement_cache.get("places_restantes")

        print("\n- Liste des inscrits (temps réel) -")
        print(f"Événement : {titre}")
        print(f"Date      : {date_evt}")
        print(f"Lieu      : {lieu}")
        if pr is not None:
            print(f"Places restantes estimées : {pr}")

    def _print_inscrits(self, inscrits: List[Dict[str, Any]]):
        if not inscrits:
            print("\nAucun inscrit pour le moment.")
            return

        print("\nInscrits :")
        for i, s in enumerate(inscrits, start=1):
            dr = s["date_reservation"]
            dr_str = ""
            try:
                if dr:
                    dr_str = f" | réservé le {dr.strftime('%d/%m/%Y %H:%M')}"
            except Exception:
                dr_str = f" | réservé le {dr}"

            options = []
            if s["bus_aller"]:  options.append("Aller")
            if s["bus_retour"]: options.append("Retour")
            if s["adherent"]:   options.append("Adhérent")
            if s["sam"]:        options.append("SAM")
            if s["boisson"]:    options.append("Boisson")
            opt_str = f" | Options: {', '.join(options)}" if options else ""

            avis_str = ""
            if s["commentaire_avis"] or s["commentaire_note"]:
                note = f"({s['commentaire_note']}/5)" if s['commentaire_note'] else ""
                avis = s['commentaire_avis'] or "Aucun texte"
                avis_str = f"\n  └─ AVIS {note}: « {avis} »"

            print(f"  {i:02d}. {s['prenom']} {s['nom']} <{s['email']}>{opt_str}{dr_str}{avis_str}")

        total = len(inscrits)
        t_aller = sum(1 for s in inscrits if s["bus_aller"])
        t_retour = sum(1 for s in inscrits if s["bus_retour"])
        t_adh = sum(1 for s in inscrits if s["adherent"])

        print("\n--- Totaux ---")
        print(f"Participants : {total}")
        print(f"Bus aller    : {t_aller}")
        print(f"Bus retour   : {t_retour}")
        print(f"Adhérents    : {t_adh}")

    # ----------------- Cycle Vue -----------------
    def afficher(self) -> None:
        super().afficher()

        if not self._is_admin():
            print("Accès refusé : réservé aux administrateurs.")
            return

        if not self.id_evenement:
            self.id_evenement = self._select_evenement()

        if not self.id_evenement:
            print("Aucun événement sélectionné.")
            return

        self._evenement_cache = self._fetch_evenement(self.id_evenement)
        inscrits = self._load_inscrits(self.id_evenement)
        self._print_header()
        self._print_inscrits(inscrits)

    def choisir_menu(self) -> Optional[VueAbstraite]:
        from view.administrateur.connexion_admin_vue import ConnexionAdminVue

        if not self._is_admin():
            return ConnexionAdminVue("Accès refusé.")

        if not self.id_evenement:
            return ConnexionAdminVue("Aucun événement sélectionné.")

        while True:
            action = inquirer.select(
                message="Actions :",
                choices=[
                    "Actualiser la liste",
                    "Changer d'événement",
                    "--- Retour ---",
                ],
            ).execute()

            if action == "Actualiser la liste":
                inscrits = self._load_inscrits(self.id_evenement)
                self._print_header()
                self._print_inscrits(inscrits)

            elif action == "Changer d'événement":
                new_id = self._select_evenement()
                if not new_id:
                    continue
                self.id_evenement = new_id
                self._evenement_cache = self._fetch_evenement(self.id_evenement)
                inscrits = self._load_inscrits(self.id_evenement)
                self._print_header()
                self._print_inscrits(inscrits)

            else:
                return ConnexionAdminVue("Retour au menu admin")
