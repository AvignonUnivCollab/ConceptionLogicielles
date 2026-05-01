"""
Détecteur de titres de sections dans un article scientifique.

Responsabilité unique : à partir d'une ligne de texte, déterminer
si elle correspond à un titre de section connu et retourner sa clé canonique.
"""

import re

from parsers.section_taxonomy import MOTS_CLES, SOUS_SECTIONS_CORPS
from parsers.text_cleaner import reconstruire_mots_ieee


def classer_titre(titre: str) -> str | None:
    """
    Retourne la clé canonique de section pour un titre donné, ou None.

    Les sous-sections "corps" connues sont explicitement ignorées
    pour éviter de fragmenter la section corps en de fausses sections.
    """
    t = titre.lower().strip()

    for ss in SOUS_SECTIONS_CORPS:
        if ss in t:
            return None

    for section, mots in MOTS_CLES.items():
        for mot in mots:
            if mot in t or t.startswith(mot):
                return section

    return None


def detecter_section(ligne: str) -> str | None:
    """
    Analyse une ligne et retourne la clé de section si c'est un titre,
    sinon None.

    Cas reconnus :
      1. Titre seul (sans numéro) : "Abstract", "Introduction"
      2. Numéro arabe + titre     : "1 Introduction", "2.1 Related Work"
      3. Numéro romain IEEE       : "I. INTRODUCTION", "VI. EXPERIMENTS"
      4. Abstract inline          : "Abstract—...", "Abstract. ..."
    """
    stripped = ligne.strip()
    if not stripped or len(stripped) > 150:
        return None

    norm  = reconstruire_mots_ieee(stripped)
    gauche = re.split(r"\s{4,}", norm)[0].strip()  # colonne gauche (double colonne)

    # Cas 1 : titre seul sans numéro
    if re.match(r"^[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s\-]{1,60}$", gauche):
        return classer_titre(gauche)

    # Cas 2 : numéro arabe + titre
    m = re.match(r"^(\d+[\.\d]*)\s+(.+)$", gauche)
    if m:
        return classer_titre(m.group(2).strip())

    # Cas 3 : numéro romain IEEE + titre
    m = re.match(r"^([IVXivx]+)[\.\s]+(.+)$", gauche)
    if m:
        return classer_titre(m.group(2).strip())

    # Cas 4 : abstract inline
    if re.match(r"^abstract[\s\.\—\–\:]", stripped, re.IGNORECASE):
        return "abstract"

    return None
