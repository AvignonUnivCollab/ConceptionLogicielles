# This is a sample Python script.

# Press Maj+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
#!/usr/bin/env python3
"""
Parseur d'articles scientifiques en format texte
Projet Scrum - Sprint 1
LIA / Avignon Université

"""

import re
import sys
import os
import argparse
import subprocess
import tempfile


# CONVERSION PDF → TEXTE
def convert_pdftotext(pdf_path: str) -> str:
    """Conversion avec pdftotext -layout (poppler-utils)."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["pdftotext", "-layout", pdf_path, tmp_path],
            check=True, capture_output=True
        )
        with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def convert_pdf2txt(pdf_path: str) -> str:
    """Conversion avec pdf2txt.py (pdfminer.six)."""
    result = subprocess.run(
        ["pdf2txt.py", pdf_path],
        capture_output=True, text=True, errors="replace"
    )
    return result.stdout


# NETTOYAGE DU TEXTE
def nettoyer_texte(texte: str) -> str:
    """Nettoie le texte extrait : retire les headers/footers de pages."""
    lignes = texte.split("\n")
    lignes_propres = []
    for ligne in lignes:
        # Retire les numéros de page isolés
        if re.match(r"^\s*\d+\s*$", ligne):
            continue
        # Retire les sauts de page
        if "\f" in ligne:
            ligne = ligne.replace("\f", "")
        lignes_propres.append(ligne)
    return "\n".join(lignes_propres)


# PARSEUR DE SECTIONS

# Mots-clés pour chaque section (ordre de priorité)
SECTIONS = {
    "titre":        [],   # toujours la première ligne significative
    "auteurs":      [],   # juste après le titre
    "abstract":     [r"abstract", r"résumé", r"summary"],
    "introduction": [r"introduction", r"\d[\.\s]+introduction"],
    "corps":        [r"method", r"méthode", r"approach", r"approche",
                     r"background", r"related work", r"travaux", r"système",
                     r"system", r"model", r"modèle", r"architecture",
                     r"framework", r"formulation", r"proposition",
                     r"\d[\.\s]+(method|approach|background|system)"],
    "resultats":    [r"result", r"résultat", r"experiment", r"expérience",
                     r"evaluation", r"évaluation",
                     r"\d[\.\s]+(result|experiment|evaluation)"],
    "conclusion":   [r"conclusion", r"discussion.*future",
                     r"conclusion.*future", r"future work",
                     r"\d[\.\s]+conclusion"],
    "discussion":   [r"discussion", r"analyse", r"analysis"],
    "bibliographie":[r"references?", r"bibliograph", r"bibliography"],
}


def detecter_section(ligne: str) -> str | None:
    """
    Détecte si une ligne est un titre de section.
    Retourne le nom de section ou None.
    Gère les articles simple et double-colonne.
    """
    ligne_stripped = ligne.strip()

    # Ignore les lignes vides ou trop longues pour être un titre
    if not ligne_stripped or len(ligne_stripped) > 120:
        return None

    # Normalise les espaces multiples (double-colonne : "1   Introduction")
    ligne_norm = re.sub(r"\s+", " ", ligne_stripped)
    ligne_lower = ligne_norm.lower()

    for nom_section, patterns in SECTIONS.items():
        if nom_section in ("titre", "auteurs"):
            continue
        for pattern in patterns:
            # Titre seul : "Abstract", "Introduction", "References"
            if re.match(r"^" + pattern + r"[\s\.\:]*$", ligne_lower, re.IGNORECASE):
                return nom_section
            # Section numérotée : "1 Introduction", "2. Method", "3.1 Results"
            if re.match(r"^\d+[\.\s]+" + pattern + r"[\s\.\:]*$", ligne_lower, re.IGNORECASE):
                return nom_section
            # Double-colonne : la moitié gauche seulement est le titre
            # ex : "1   Introduction                    redundancy with..."
            # On prend la partie gauche (avant grand espace)
            moitie_gauche = re.split(r"\s{4,}", ligne_stripped)[0].strip().lower()
            moitie_gauche = re.sub(r"\s+", " ", moitie_gauche)
            if moitie_gauche and re.match(r"^(\d+[\.\s]+)?" + pattern + r"[\s\.\:]*$",
                                          moitie_gauche, re.IGNORECASE):
                return nom_section

    return None


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
