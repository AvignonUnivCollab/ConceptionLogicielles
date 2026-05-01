"""
Parseur structurel d'un article scientifique.

Responsabilité unique : à partir d'un texte brut nettoyé, produire
un dictionnaire `{section: contenu}` en trois passes successives :
  1. Extraction du titre
  2. Extraction des auteurs
  3. Découpage des sections thématiques
"""

import re

from parsers.section_taxonomy import SECTIONS_ORDRE
from parsers.section_detector import detecter_section
from parsers.text_cleaner import (
    nettoyer_texte,
    supprimer_sauts_excessifs,
)


# ---------------------------------------------------------------------------
# Heuristiques locales
# ---------------------------------------------------------------------------

def _est_titre_article(ligne: str) -> bool:
    s = ligne.strip()
    if not s or len(s) < 5:
        return False
    if s.endswith((".com", ".fr", ".org", "@")):
        return False
    mots = s.split()
    return 2 <= len(mots) <= 20


def _est_ligne_affiliation(ligne: str) -> bool:
    return bool(re.search(
        r"@|universit|laboratoire|department|institute|lab\b|faculty",
        ligne,
        re.IGNORECASE,
    ))


def _est_ligne_auteurs(ligne: str) -> bool:
    if not re.match(r"^[A-ZÀ-Ÿ]", ligne) or len(ligne) >= 200:
        return False
    return bool(
        re.search(r",|\band\b|·|;", ligne)
        or re.match(r"^([A-ZÀ-Ÿ][a-zà-ÿ]+[\s\.\-]*){2,6}$", ligne)
    )


# ---------------------------------------------------------------------------
# Les trois passes d'extraction
# ---------------------------------------------------------------------------

def _extraire_titre(lignes: list[str]) -> tuple[str, int]:
    """
    Passe 1 : cherche le titre dans les premières lignes.
    Retourne (texte_titre, index_fin_titre).
    """
    for i, ligne in enumerate(lignes):
        stripped = ligne.strip()
        if not stripped:
            continue
        if not _est_titre_article(ligne):
            continue

        titre_lignes = [stripped]
        j = i + 1
        while j < len(lignes) and j < i + 5:
            nl = lignes[j].strip()
            if not nl:
                j += 1
                continue
            if detecter_section(nl):
                break
            if re.match(r"^abstract[\s\.\—\–\:]?", nl, re.IGNORECASE):
                break
            if _est_titre_article(lignes[j]) and not re.search(r"@|\d{4,}", nl):
                titre_lignes.append(nl)
                j += 1
            else:
                break

        return " ".join(titre_lignes), j

    return "", 0


def _extraire_auteurs(lignes: list[str], debut: int) -> str:
    """
    Passe 1.5 : cherche les auteurs entre le titre et l'abstract.
    """
    auteur_lignes = []
    for i in range(debut, min(debut + 15, len(lignes))):
        l = lignes[i].strip()
        if not l:
            continue
        if detecter_section(l):
            break
        if re.match(r"^abstract[\s\.\—\–\:]?", l, re.IGNORECASE):
            break
        if _est_ligne_affiliation(l):
            continue
        if _est_ligne_auteurs(l):
            auteur_lignes.append(l)
    return " ".join(auteur_lignes)


def _extraire_sections(lignes: list[str]) -> dict[str, str]:
    """
    Passe 2 : parcourt les lignes et accumule le contenu par section.
    """
    sections: dict[str, str] = {k: "" for k in SECTIONS_ORDRE}
    section_courante: str | None = None
    contenu_courant: list[str] = []

    def _sauvegarder() -> None:
        if section_courante and contenu_courant:
            contenu = "\n".join(contenu_courant).strip()
            if contenu:
                sep = "\n\n" if sections[section_courante] else ""
                sections[section_courante] += sep + contenu

    for ligne in lignes:
        stripped = ligne.strip()

        nom_sec = detecter_section(ligne)
        if nom_sec:
            _sauvegarder()
            section_courante = nom_sec
            if nom_sec == "abstract":
                reste = re.sub(
                    r"^abstract[\s\.\—\–\:\*]+", "", stripped, flags=re.IGNORECASE
                ).strip()
                contenu_courant = [reste] if reste else []
            else:
                contenu_courant = []
            continue

        # Abstract seul centré sur sa ligne
        if re.match(r"^\s*abstract\s*$", stripped, re.IGNORECASE):
            _sauvegarder()
            section_courante = "abstract"
            contenu_courant = []
            continue

        if section_courante:
            contenu_courant.append(ligne)

    _sauvegarder()
    return sections


# ---------------------------------------------------------------------------
# Point d'entrée public
# ---------------------------------------------------------------------------

def parser_article(texte: str) -> dict[str, str]:
    """
    Parse un texte brut et retourne les sections de l'article.

    :param texte: texte extrait du PDF (non nettoyé).
    :return: dictionnaire {clé_section: contenu}.
    """
    sections: dict[str, str] = {k: "" for k in SECTIONS_ORDRE}

    texte = nettoyer_texte(texte)
    lignes = texte.split("\n")

    titre, idx_fin_titre = _extraire_titre(lignes)
    sections["titre"]   = titre
    sections["auteurs"] = _extraire_auteurs(lignes, idx_fin_titre)

    sections_corps = _extraire_sections(lignes[idx_fin_titre:])
    for cle, contenu in sections_corps.items():
        if cle not in ("titre", "auteurs"):
            sections[cle] = contenu

    # Post-traitement : normaliser les sauts de ligne
    for cle in sections:
        if sections[cle]:
            sections[cle] = supprimer_sauts_excessifs(sections[cle])

    return sections
