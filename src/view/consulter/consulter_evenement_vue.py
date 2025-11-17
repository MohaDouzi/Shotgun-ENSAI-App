# view/consulter/consulter_vue.py
from typing import Optional, Any, List
from datetime import date
from InquirerPy import inquirer
from typing import Optional, Any, List

from view.vue_abstraite import VueAbstraite
from service.consultation_evenement_service import ConsultationEvenementService  # nouveau
from view.reservations.reservation_vue import ReservationVue


class ConsulterVue(VueAbstraite):
    """
    Vue pour la consultation des événements disponibles.
    Permet de lister, filtrer, rechercher et consulter les événements.
    Utilise ConsultationEvenementService (et non plus le DAO direct).
    """

    def __init__(self) -> None:
        super().__init__("CONSULTER")
        self.service = ConsultationEvenementService()  # on passe par le service

    def afficher(self) -> None:
        super().afficher()

    # --- AJOUT DE L'HELPER  ---
    @staticmethod
    def _get_attr(obj: Any, key: str, default=None):
        """Accède à un attribut/clé, que ce soit un dict ou un objet."""
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def choisir_menu(self) -> Optional[VueAbstraite]:
        # Import local pour éviter boucles circulaires
        from view.client.connexion_client_vue import ConnexionClientVue
        from view.accueil.accueil_vue import AccueilVue
        from view.session import Session

        user = Session().utilisateur
        if user:
            if getattr(user, "administrateur", False):
                from view.administrateur.connexion_admin_vue import ConnexionAdminVue
                vue_de_retour = ConnexionAdminVue
            else:
                vue_de_retour = ConnexionClientVue
        else:
            vue_de_retour = AccueilVue

        menu_choix = {
            "Lister les événements disponibles (avec places restantes)": "places",
            "Lister tous les événements": "tous",
            "Rechercher (ville, statut, dates)": "recherche",
            "Retour": "retour",
        }

        choix_action = inquirer.select(
            message="Que souhaitez-vous faire ?",
            choices=list(menu_choix.keys()),
        ).execute()

        action = menu_choix[choix_action]
        if action == "retour":
            return vue_de_retour("Retour au menu principal")

        events: List[Any] = []

        try:
            # ---------- 1. Récupération selon action ----------
            if action == "places":
                events = self.service.lister_avec_places_restantes(
                    limit=50,
                    a_partir_du=date.today()
                )

            elif action == "tous":
                events = self.service.lister_tous(limit=50)

            elif action == "recherche":
                ville = input("Ville (laisser vide pour ignorer) : ").strip() or None
                categorie = input("Catégorie (laisser vide) : ").strip() or None
                statut = input("Statut (ex: 'disponible en ligne', laisser vide) : ").strip() or None
                date_min = input("Date minimum (YYYY-MM-DD, vide pour ignorer) : ").strip()
                date_max = input("Date maximum (YYYY-MM-DD, vide pour ignorer) : ").strip()
                date_min = date.fromisoformat(date_min) if date_min else None
                date_max = date.fromisoformat(date_max) if date_max else None

                events = self.service.rechercher(
                    ville=ville,
                    categorie=categorie,
                    statut=statut,
                    date_min=date_min,
                    date_max=date_max,
                    limit=50
                )

            # ---------- 2. Vérification ----------
            if not events:
                print("\nAucun événement ne correspond à votre recherche.")
                input("\n(Entrée) pour continuer...")
                return self

           # ---------- 3. Formatage ----------
            choices_events = []
            for ev in events:
                places_val = self._get_attr(ev, "places_restantes")
                places_str = f"({places_val} places)" if places_val is not None else ""
                
                date_evt = self._get_attr(ev, "date_evenement", "")
                titre = self._get_attr(ev, "titre", "N/A")

                # --- AJOUT DES AVIS ---
                avg_note = self._get_attr(ev, "avg_note")
                count_avis = self._get_attr(ev, "comment_count", 0)
                
                avis_str = ""
                if avg_note is not None:
                    avis_str = f" {avg_note:.1f}/5 ({count_avis} avis)"

                titre_affiche = f"{date_evt} | {titre} {places_str}{avis_str}"
                choices_events.append({"name": titre_affiche, "value": ev})

            choices_events.append({"name": "--- Retour ---", "value": None})


            event_selectionne = inquirer.select(
                message="Sélectionnez un événement pour voir les détails :",
                choices=choices_events,
            ).execute()

            if event_selectionne is None:
                return self

            # ---------- 4. On affiche les détails ----------
            self._afficher_details_event(event_selectionne)
            
            statut_evenement = self._get_attr(event_selectionne, 'statut')
            is_available = (statut_evenement == 'disponible en ligne')

            places_restantes = self._get_attr(event_selectionne, 'places_restantes')
            has_places = (places_restantes is None) or (places_restantes > 0)

            action_choices = []
            if user:
                # Si l'utilisateur est connecté, on vérifie s'il peut réserver
                if is_available and has_places:
                    action_choices.append("Réserver cet événement")
                elif not is_available:
                    print("Cet événement n'est pas (ou plus) disponible à la réservation.")
                elif not has_places:
                    print("Cet événement est complet.")
            else:
                # L'utilisateur n'est pas connecté
                print("Vous devez être connecté pour réserver.")

            action_choices.append("Retour à la liste")

            choix_detail = inquirer.select(
                message="Que souhaitez-vous faire ?",
                choices=action_choices,
            ).execute()

            if choix_detail == "Réserver cet événement":
                return ReservationVue(evenement=event_selectionne)
            else:
                return self

        except Exception as e:
            print(f"Erreur lors de la récupération des événements : {e}")
            input("(Entrée) pour continuer...")
            return self

    # --- FONCTION DÉTAILS ---
    def _afficher_details_event(self, ev: Any) -> None:
        """
        Affiche une vue détaillée d'un événement (gère dict et objet)
        ET affiche les derniers commentaires textuels.
        """
        print("\n" + "=" * 50)
        print("          DÉTAIL DE L'ÉVÉNEMENT")
        print("=" * 50)

        # --- Infos générales ---
        print(f"  Titre     : {self._get_attr(ev, 'titre', 'N/A')}")
        print(f"  Date      : {self._get_attr(ev, 'date_evenement', 'N/A')}")
        lieu = self._get_attr(ev, 'ville') or self._get_attr(ev, 'adresse') or 'N/A'
        print(f"  Lieu      : {lieu}")
        print(f"  Capacité  : {self._get_attr(ev, 'capacite', 'N/A')}")
        
        places_restantes = self._get_attr(ev, 'places_restantes')
        if places_restantes is not None:
             print(f"  Places    : {places_restantes}")
        else:
             print(f"  Places    : (calcul non disponible sur cette vue)")
             
        print(f"  Statut    : {self._get_attr(ev, 'statut', 'N/A')}")
        print(f"  Catégorie : {self._get_attr(ev, 'categorie', 'N/A')}")

        # Note Moyenne
        avg_note = self._get_attr(ev, "avg_note")
        count_avis = self._get_attr(ev, "comment_count", 0)
        if avg_note is not None:
            print(f"  Note Moy. : {avg_note:.1f}/5 ({count_avis} avis)")
        else:
            print("  Note Moy. : (Aucun avis pour le moment)")
        
        print("-" * 50)
        print(f"  Description : \n  {self._get_attr(ev, 'description', 'Aucune description.')}")
        print("-" * 50)

        if count_avis > 0:
            print("  💬 DERNIERS AVIS :")
            
            try:
                from service.commentaire_service import CommentaireService
                com_service = CommentaireService()
                
                id_evt = self._get_attr(ev, 'id_evenement')
                
                avis_list = com_service.get_comments_for_event(id_evt)
                
                # On affiche les 3 premiers avis pour ne pas surcharger l'écran
                for com in avis_list[:3]: 
                    prenom = com.get('prenom', 'Anonyme')
                    nom = com.get('nom', '')
                    note = com.get('note')
                    texte = com.get('avis') or ""
                    
                    # Formatage : "Alice D."
                    auteur = f"{prenom} {nom[0]}." if nom else prenom
                    note_str = f"{note}/5" if note else "-"
                    
                    print(f"    • {auteur} ({note_str}) : \"{texte}\"")
                
                # Si il y en a plus que 3
                if len(avis_list) > 3:
                    print(f"    ... et {len(avis_list) - 3} autres avis (voir stats).")

            except Exception as e:
                print(f"    (Impossible de charger le détail des avis : {e})")
        else:
            print("  💬 Aucun commentaire écrit pour l'instant.")

        print("=" * 50 + "\n")