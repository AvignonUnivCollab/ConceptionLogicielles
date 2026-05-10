"""
Détecteur robuste de titres de sections.
Améliorations :
- reconnaît les numéros avec espaces multiples : "1    Introduction" ;
- reconnaît les numéros décimaux : "3.2 Related Work" ;
- reconnaît les titres IEEE espacés : "I NTRODUCTION" ;
- évite de couper trop tôt les lignes à cause des espaces de mise en page.
"""

import re

from parsers.section_taxonomy import MOTS_CLES, SOUS_SECTIONS_CORPS
from parsers.text_cleaner import reconstruire_mots_ieee


def _normaliser(titre: str) -> str:
    t = reconstruire_mots_ieee(titre)
    t = t.replace("—", "-").replace("–", "-")
    t = re.sub(r"\s+", " ", t).strip().lower()
    t = re.sub(r"^[\[\(]?\s*", "", t)
    t = re.sub(r"[\.:;\-\s]+$", "", t)
    return t


def classer_titre(titre: str) -> str | None:
    """Retourne la section canonique correspondant à un intitulé."""
    t = _normaliser(titre)
    if not t:
        return None

    # On ignore les vraies sous-sections techniques : elles restent dans le corps.
    for ss in SOUS_SECTIONS_CORPS:
        if t == ss or t.startswith(ss + " "):
            return None

    for section, mots in MOTS_CLES.items():
        for mot in mots:
            m = _normaliser(mot)
            # Correspondance stricte ou début d'un titre composé.
            if t == m or t.startswith(m + " ") or t.startswith(m + ":"):
                return section
    return None


def _candidats_colonnes(ligne: str) -> list[str]:
    """
    Retourne des fragments possibles de titres dans une ligne pdftotext -layout.
    Important : on garde aussi la ligne entière, car "1    Introduction" contient
    plusieurs espaces mais n'est pas une ligne double-colonne.
    """
    norm = reconstruire_mots_ieee(ligne.strip())
    candidats = [norm]
    candidats.extend([p.strip() for p in re.split(r"\s{4,}", norm) if p.strip()])
    # Supprimer doublons en conservant l'ordre
    out, seen = [], set()
    for c in candidats:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _titre_depuis_fragment(fragment: str) -> str | None:
    f = fragment.strip()
    if not f or len(f) > 180:
        return None

    # Abstract inline : "Abstract— text" ou "Abstract. text"
    if re.match(r"^abstract\s*[\.\:\-]\s*", f, re.IGNORECASE):
        return "abstract"

    # Numéro arabe : "1 Introduction", "1. Introduction", "2.3 Method"
    m = re.match(r"^\s*\d+(?:\.\d+)*\s*\.?\s+(.{2,80})$", f)
    if m:
        return classer_titre(m.group(1))

    # Numéro romain IEEE : "I. INTRODUCTION", "IV EXPERIMENTS"
    m = re.match(r"^\s*[IVXLCDM]+\s*\.?\s+(.{2,80})$", f, re.IGNORECASE)
    if m:
        return classer_titre(m.group(1))

    # Titre seul : Abstract, Introduction, References, Conclusion and future work...
    # On limite aux lignes courtes pour éviter de classer une phrase comme titre.
    if len(f) <= 90 and re.match(r"^[A-ZÀ-Ÿ][A-Za-zÀ-ÿ0-9\s,&/\-:]+$", f):
        return classer_titre(f)

    return None


def detecter_section(ligne: str) -> str | None:
    """Analyse une ligne et retourne la clé de section si elle ressemble à un titre."""
    if not ligne or not ligne.strip():
        return None
    for frag in _candidats_colonnes(ligne):
        sec = _titre_depuis_fragment(frag)
        if sec:
            return sec
    return None
