"""
Benchmark de comparaison entre convertisseurs PDF.

Responsabilité unique : mesurer et afficher la qualité de chaque outil
(nombre de sections détectées, mots collés) puis recommander le meilleur.
"""

import os
import re
import sys

from converters.pdf_converter import PdfConverter, ConverterFactory
from parsers.article_parser import parser_article
from utils.colors import (
    RESET, BOLD, C_BLEU, C_CYAN, C_VERT, C_ROUGE, C_GRIS
)


def _evaluer_convertisseur(
    nom: str, convertisseur: PdfConverter, pdf_path: str
) -> dict | None:
    """
    Extrait le texte, parse l'article et calcule des métriques de qualité.
    Retourne un dict de métriques, ou None si une erreur survient.
    """
    print(f"{C_BLEU}{BOLD}── {nom} ──────────────────────────────{RESET}")
    try:
        texte    = convertisseur.convert(pdf_path)
        sections = parser_article(texte)
        trouvees = [k for k, v in sections.items() if v.strip()]
        nb_mots  = len(texte.split())
        mots_colles = len(re.findall(r"[a-z]{15,}", texte))

        qualite = (
            f"{C_ROUGE}texte dégradé{RESET}"
            if mots_colles > 50
            else f"{C_VERT}bon{RESET}"
        )
        print(f"  {C_GRIS}Mots extraits        :{RESET} {nb_mots}")
        print(f"  {C_GRIS}Sections détectées   :{RESET} {len(trouvees)} → {C_VERT}{', '.join(trouvees)}{RESET}")
        print(f"  {C_GRIS}Mots collés (≥15c)   :{RESET} {mots_colles}  {qualite}")
        print()
        return {"sections": len(trouvees), "mots_colles": mots_colles}

    except Exception as e:
        print(f"  {C_ROUGE}ERREUR : {e}{RESET}\n")
        return None


def comparer_outils(pdf_path: str) -> None:
    """
    Compare `pdftotext` et `pdf2txt` sur un même fichier et
    recommande l'outil produisant le moins de mots collés.
    """
    print(f"\n{C_BLEU}{BOLD}{'='*60}{RESET}")
    print(f"{C_BLEU}{BOLD} COMPARAISON pdftotext vs pdf2txt{RESET}")
    print(f"{C_GRIS} Fichier : {C_CYAN}{os.path.basename(pdf_path)}{RESET}")
    print(f"{C_BLEU}{BOLD}{'='*60}{RESET}\n")

    candidats = [
        ("pdftotext -layout", ConverterFactory.create("pdftotext")),
        ("pdf2txt.py",        ConverterFactory.create("pdf2txt")),
    ]
    resultats: dict[str, dict] = {}

    for nom, convertisseur in candidats:
        metriques = _evaluer_convertisseur(nom, convertisseur, pdf_path)
        if metriques is not None:
            resultats[nom] = metriques

    print(f"{C_BLEU}{BOLD}── Verdict ──────────────────────────────────{RESET}")
    if resultats:
        meilleur = min(resultats, key=lambda x: resultats[x]["mots_colles"])
        print(f"{C_VERT}{BOLD}Outil recommandé : {meilleur}{RESET}")
    print()
