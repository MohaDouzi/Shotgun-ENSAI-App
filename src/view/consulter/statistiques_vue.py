# src/view/consulter/statistiques_vue.py
from typing import Optional, Any
from InquirerPy import inquirer

from view.vue_abstraite import VueAbstraite
from view.session import Session
from service.consultation_evenement_service import ConsultationEvenementService


class StatistiquesInscriptionsVue(VueAbstraite):
    """
    Vue Admin : Statistiques globales.
    """

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.service = ConsultationEvenementService()
        self.user = Session().utilisateur

    def afficher(self) -> None:
        super().afficher()
        print("\n--- Statistiques des Inscriptions ---")

    def _get_val(self, row: dict, key: str, default: Any = 0) -> Any:
        val = row.get(key)
        return val if val is not None else default

    def _print_stats_globale(self, tableau: list):
        if not tableau:
            print("Aucune donnée à afficher.")
            return

        # En-tête
        print(f"{'ID':>4} | {'Date':<10} | {'Titre':<25} | {'Cap.':>5} | {'Ins.':>5} | {'% Occ.':>6} | {'SAM':>4} | {'Adh.':>4} | {'Note':>5}")
        print("-" * 90)

        for row in tableau:
            # 1. Données de base
            id_evt = self._get_val(row, 'id_evenement')
            date_str = str(self._get_val(row, 'date_evenement', 'N/A'))[:10]
            titre = str(self._get_val(row, 'titre', 'Sans titre'))[:25]
            
            # 2. Stats calculées par le DAO 
            capacite = self._get_val(row, 'capacite')
            inscrits = self._get_val(row, 'nb_inscrits')
            sam = self._get_val(row, 'nb_sam')
            adh = self._get_val(row, 'nb_adh')
            
            # 3. Calculs simples d'affichage
            pourcentage = 0.0
            if capacite > 0:
                pourcentage = (inscrits / capacite) * 100
            
            avg_note = self._get_val(row, 'avg_note')
            note_str = f"{avg_note:.1f}" if avg_note else "-"

            # 4. Affichage
            print(f"{id_evt:>4} | {date_str:<10} | {titre:<25} | {capacite:>5} | {inscrits:>5} | {pourcentage:>5.1f}% | {sam:>4} | {adh:>4} | {note_str:>5}")

        print("-" * 90)

    def choisir_menu(self) -> Optional[VueAbstraite]:
        from view.administrateur.connexion_admin_vue import ConnexionAdminVue
        
        if not self.user or not getattr(self.user, "administrateur", False):
             return ConnexionAdminVue("Accès refusé.")

        try:
            events = self.service.lister_tous(limit=100)
            self._print_stats_globale(events)

        except Exception as e:
            print(f"Erreur lors du calcul des statistiques : {e}")

        inquirer.select(
            message="Actions :",
            choices=["Actualiser", "Retour au menu admin"],
        ).execute()
        
        return ConnexionAdminVue()