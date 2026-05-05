"""
Traitement par lot d'un dossier de fichiers PDF.

Responsabilité unique : orchestrer la conversion, le parsing et
l'écriture des fichiers de sortie pour chaque PDF d'un dossier.

Sprint 4 : support du format de sortie (-t texte | -x XML).
"""

import os
import shutil
import sys

from converters.pdf_converter import PdfConverter, ConverterFactory
from parsers.article_parser import parser_article
from formatters.article_formatter import Sprint2Formatter
from formatters.xml_formatter import XmlFormatter
from utils.colors import (
    RESET, BOLD, C_BLEU, C_CYAN, C_VERT, C_ROUGE, C_JAUNE, C_GRIS
)

# Formats de sortie disponibles
FORMAT_TEXTE = "texte"
FORMAT_XML   = "xml"


def _preparer_dossier_sortie(dossier_pdf: str, format_sortie: str) -> str:
    sous_dossier = "xml" if format_sortie == FORMAT_XML else "txt"
    dossier_sortie = os.path.join(dossier_pdf, "output", sous_dossier)
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
    format_sortie: str,
) -> bool:
    """
    Convertit, parse et écrit le fichier de sortie pour un PDF.
    Retourne True si succès, False si erreur.
    """
    chemin_pdf = os.path.join(dossier_pdf, nom_pdf)
    nom_base   = os.path.splitext(nom_pdf)[0]
    extension  = ".xml" if format_sortie == FORMAT_XML else ".txt"
    chemin_sortie = os.path.join(dossier_sortie, nom_base + extension)

    print(f"  {C_CYAN}{nom_pdf}{RESET}", file=sys.stderr, end=" ")
    try:
        texte_brut = convertisseur.convert(chemin_pdf)
        sections   = parser_article(texte_brut)

        if format_sortie == FORMAT_XML:
            formatter = XmlFormatter()
        else:
            formatter = Sprint2Formatter()

        sortie = formatter.format(sections, nom_pdf)

        with open(chemin_sortie, "w", encoding="utf-8") as f:
            f.write(sortie + "\n")

        print(f"{C_VERT}✓{RESET}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"{C_ROUGE}✗ ERREUR : {e}{RESET}", file=sys.stderr)
        return False


def _afficher_bilan(
    nb_ok: int,
    nb_total: int,
    erreurs: list[str],
    dossier_sortie: str,
    format_sortie: str,
) -> None:
    print(f"\n{C_BLEU}{'─'*50}{RESET}", file=sys.stderr)
    print(
        f"{BOLD}Traités : {C_VERT}{nb_ok}{RESET}{BOLD}/{nb_total}{RESET}  |  "
        f"Erreurs : {C_ROUGE if erreurs else C_VERT}{len(erreurs)}{RESET}  |  "
        f"Format : {C_CYAN}{format_sortie.upper()}{RESET}",
        file=sys.stderr,
    )
    if erreurs:
        print(f"{C_ROUGE}Fichiers en erreur : {', '.join(erreurs)}{RESET}", file=sys.stderr)
    print(f"{C_GRIS}Sorties dans : {dossier_sortie}{RESET}", file=sys.stderr)


def traiter_dossier(
    dossier_pdf: str,
    outil: str = "pdftotext",
    format_sortie: str = FORMAT_TEXTE,
) -> None:
    """
    Parcourt `dossier_pdf`, parse chaque PDF et écrit les fichiers de sortie.

    :param dossier_pdf:   chemin vers le dossier contenant les PDFs.
    :param outil:         convertisseur PDF→texte ("pdftotext" ou "pdf2txt").
    :param format_sortie: FORMAT_TEXTE ("-t") ou FORMAT_XML ("-x").
    """
    if not os.path.isdir(dossier_pdf):
        print(f"Erreur : dossier introuvable : {dossier_pdf}", file=sys.stderr)
        sys.exit(1)

    pdfs = _lister_pdfs(dossier_pdf)
    if not pdfs:
        print("Aucun fichier PDF trouvé dans le dossier.", file=sys.stderr)
        return

    dossier_sortie = _preparer_dossier_sortie(dossier_pdf, format_sortie)
    convertisseur  = ConverterFactory.create(outil)
    erreurs: list[str] = []

    for nom_pdf in pdfs:
        ok = _traiter_un_pdf(
            nom_pdf, dossier_pdf, dossier_sortie,
            convertisseur, format_sortie,
        )
        if not ok:
            erreurs.append(nom_pdf)

    _afficher_bilan(
        len(pdfs) - len(erreurs), len(pdfs),
        erreurs, dossier_sortie, format_sortie,
    )