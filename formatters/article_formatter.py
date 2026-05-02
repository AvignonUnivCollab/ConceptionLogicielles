"""
Formateurs de sortie pour le résultat du parsing.

Architecture :
  - ArticleFormatter  : interface abstraite (OCP / DIP)
  - Sprint2Formatter  : format Sprint 2 (une ligne par champ)
  - StatsFormatter    : affichage des statistiques terminal
"""

import re
import sys
from abc import ABC, abstractmethod

from utils.colors import (
    RESET, BOLD, C_BLEU, C_VERT, C_JAUNE, C_GRIS
)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class ArticleFormatter(ABC):
    """Interface commune pour tout formateur de sections."""

    @abstractmethod
    def format(self, sections: dict[str, str], nom_fichier: str) -> str:
        """Retourne une chaîne représentant les sections de l'article."""


# ---------------------------------------------------------------------------
# Implémentation Sprint 2
# ---------------------------------------------------------------------------

def _une_ligne(texte: str) -> str:
    """Compresse un texte multi-lignes en une seule ligne."""
    return re.sub(r"\s+", " ", texte).strip()


class Sprint2Formatter(ArticleFormatter):
    """
    Format Sprint 2 : fichier, titre, auteurs, résumé sur une ligne chacun.

    Exemple de sortie :
        Fichier : article.pdf
        Titre   : Deep Learning for NLP
        Auteurs : Alice Martin, Bob Dupont
        Resume  : This paper presents...
    """

    def format(self, sections: dict[str, str], nom_fichier: str) -> str:
        return "\n".join([
            f"Fichier : {nom_fichier}",
            f"Titre : {_une_ligne(sections.get('titre',   ''))}",
            f"Auteurs : {_une_ligne(sections.get('auteurs', ''))}",
            f"Emails : {_une_ligne(sections.get('emails',  ''))}",
            f"Resume : {_une_ligne(sections.get('abstract', ''))}",
        ])


# ---------------------------------------------------------------------------
# Affichage des statistiques (pas un formateur de fichier, mais de terminal)
# ---------------------------------------------------------------------------

class StatsFormatter:
    """Affiche un résumé coloré des sections trouvées / manquantes."""

    def afficher(self, sections: dict[str, str]) -> None:
        trouvees  = [k for k, v in sections.items() if v.strip()]
        manquantes = [k for k, v in sections.items() if not v.strip()]

        print(f"\n{C_BLEU}{BOLD}── Statistiques ──────────────────────────────{RESET}")
        print(
            f"  {C_GRIS}Sections trouvées  ({len(trouvees)}) :{RESET} "
            f"{C_VERT}{', '.join(trouvees)}{RESET}"
        )
        if manquantes:
            print(
                f"  {C_GRIS}Sections absentes  ({len(manquantes)}) :{RESET} "
                f"{C_JAUNE}{', '.join(manquantes)}{RESET}"
            )
        print(f"{C_BLEU}──────────────────────────────────────────────{RESET}\n")
