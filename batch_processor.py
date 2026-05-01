"""
Traitement par lot d'un dossier de fichiers PDF.

Responsabilité unique : orchestrer la conversion, le parsing et
l'écriture des fichiers de sortie pour chaque PDF d'un dossier.
"""

import os
import shutil
import sys

from converters.pdf_converter import PdfConverter, ConverterFactory
from parsers.article_parser import parser_article
from formatters.article_formatter import Sprint2Formatter
from utils.colors import (
    RESET, BOLD, C_BLEU, C_CYAN, C_VERT, C_ROUGE, C_JAUNE, C_GRIS
)


def _preparer_dossier_sortie(dossier_pdf: str) -> str:
    """
    Crée (ou recrée) le sous-dossier `output/` dans le dossier source.
    Retourne le chemin du dossier de sortie.
    """
    dossier_sortie = os.path.join(dossier_pdf, "output")
    if os.path.exists(dossier_sortie):
        print(
            f"{C_JAUNE}Suppression de l'ancien dossier : {dossier_sortie}{RESET}",
            file=sys.stderr,
        )
        shutil.rmtree(dossier_sortie)
    os.makedirs(dossier_sortie)
    print(
        f"{C_VERT}Dossier de sortie créé : {dossier_sortie}{RESET}",
        file=sys.stderr,
    )
    return dossier_sortie


def _lister_pdfs(dossier: str) -> list[str]:
    return sorted(f for f in os.listdir(dossier) if f.lower().endswith(".pdf"))


def _traiter_un_pdf(
    nom_pdf: str,
    dossier_pdf: str,
    dossier_sortie: str,
    convertisseur: PdfConverter,
    formatter: Sprint2Formatter,
) -> bool:
    """
    Convertit, parse et écrit le fichier .txt pour un PDF.
    Retourne True si succès, False si erreur.
    """
    chemin_pdf = os.path.join(dossier_pdf, nom_pdf)
    nom_base   = os.path.splitext(nom_pdf)[0]
    chemin_txt = os.path.join(dossier_sortie, nom_base + ".txt")

    print(f"  {C_CYAN}{nom_pdf}{RESET}", file=sys.stderr, end=" ")
    try:
        texte_brut = convertisseur.convert(chemin_pdf)
        sections   = parser_article(texte_brut)
        sortie     = formatter.format(sections, nom_pdf)

        with open(chemin_txt, "w", encoding="utf-8") as f:
            f.write(sortie + "\n")

        print(f"{C_VERT}✓{RESET}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"{C_ROUGE}✗ ERREUR : {e}{RESET}", file=sys.stderr)
        return False


def _afficher_bilan(nb_ok: int, nb_total: int, erreurs: list[str], dossier_sortie: str) -> None:
    print(f"\n{C_BLEU}{'─'*50}{RESET}", file=sys.stderr)
    print(
        f"{BOLD}Traités : {C_VERT}{nb_ok}{RESET}{BOLD}/{nb_total}{RESET}  |  "
        f"Erreurs : {C_ROUGE if erreurs else C_VERT}{len(erreurs)}{RESET}",
        file=sys.stderr,
    )
    if erreurs:
        print(f"{C_ROUGE}Fichiers en erreur : {', '.join(erreurs)}{RESET}", file=sys.stderr)
    print(f"{C_GRIS}Sorties dans : {dossier_sortie}{RESET}", file=sys.stderr)


def traiter_dossier(dossier_pdf: str, outil: str = "pdftotext") -> None:
    """
    Parcourt `dossier_pdf`, parse chaque PDF et écrit les .txt dans
    `dossier_pdf/output/`.

    :param dossier_pdf: chemin vers le dossier contenant les PDFs.
    :param outil: nom du convertisseur ("pdftotext" ou "pdf2txt").
    """
    if not os.path.isdir(dossier_pdf):
        print(f"Erreur : dossier introuvable : {dossier_pdf}", file=sys.stderr)
        sys.exit(1)

    pdfs = _lister_pdfs(dossier_pdf)
    if not pdfs:
        print("Aucun fichier PDF trouvé dans le dossier.", file=sys.stderr)
        return

    dossier_sortie = _preparer_dossier_sortie(dossier_pdf)
    convertisseur  = ConverterFactory.create(outil)
    formatter      = Sprint2Formatter()
    erreurs: list[str] = []

    for nom_pdf in pdfs:
        ok = _traiter_un_pdf(nom_pdf, dossier_pdf, dossier_sortie, convertisseur, formatter)
        if not ok:
            erreurs.append(nom_pdf)

    _afficher_bilan(len(pdfs) - len(erreurs), len(pdfs), erreurs, dossier_sortie)
