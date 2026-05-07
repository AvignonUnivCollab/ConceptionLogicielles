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

def selectionner_fichiers(pdfs: list[str], dossier_pdf: str) -> list[str]:
    """Affiche le menu de sélection et retourne la liste des PDFs choisis."""
    n = len(pdfs)
    largeur_num = len(str(n))

    print(f"\n{C_BLEU}{BOLD}┌─ PDFs disponibles{'─' * 30}┐{RESET}", file=sys.stderr)
    for i, nom in enumerate(pdfs, 1):
        num = f"{i:>{largeur_num}}"
        print(f"{C_BLEU}│{RESET}  {C_GRIS}[{C_CYAN}{num}{C_GRIS}]{RESET}  {nom}", file=sys.stderr)
    print(f"{C_BLEU}└{'─' * 49}┘{RESET}", file=sys.stderr)
    print(
        f"\n{C_GRIS}  Syntaxe : {C_CYAN}1,3{C_GRIS}  ·  {C_CYAN}2-5{C_GRIS}  ·  "
        f"{C_CYAN}1,4-7,10{C_GRIS}  ·  {C_CYAN}*{C_GRIS} pour tout sélectionner{RESET}",
        file=sys.stderr,
    )

    try:
        selection_input = input(f"\n  {BOLD}Votre sélection :{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C_JAUNE}Annulé.{RESET}", file=sys.stderr)
        return []

    if selection_input in ('*', 'all', ''):
        if selection_input == '':
            print(f"{C_JAUNE}  Aucune sélection → tous les fichiers traités.{RESET}", file=sys.stderr)
        return pdfs

    indices_choisis: set[int] = set()
    for partie in selection_input.split(','):
        partie = partie.strip()
        if not partie:
            continue
        if '-' in partie:
            try:
                debut, fin = map(int, partie.split('-', 1))
                if debut > fin:
                    debut, fin = fin, debut
                indices_choisis.update(range(debut, fin + 1))
            except ValueError:
                print(f"{C_ROUGE}  Ignoré (plage invalide) : « {partie} »{RESET}", file=sys.stderr)
        else:
            try:
                indices_choisis.add(int(partie))
            except ValueError:
                print(f"{C_ROUGE}  Ignoré (valeur invalide) : « {partie} »{RESET}", file=sys.stderr)

    choix = [pdfs[i - 1] for i in sorted(indices_choisis) if 0 < i <= n]

    if not choix:
        print(f"{C_ROUGE}  Aucun fichier valide sélectionné.{RESET}", file=sys.stderr)
    else:
        noms = ", ".join(f"{C_CYAN}{p}{RESET}" for p in choix)
        print(f"\n  {C_VERT}✓{RESET} Sélection : {noms}\n", file=sys.stderr)

    return choix

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
    nb_ignore: int,
    erreurs: list[str],
    dossier_sortie: str,
    format_sortie: str,
) -> None:
    print(f"\n{C_BLEU}{'─'*50}{RESET}", file=sys.stderr)
    print(
        f"{BOLD}Traités : {C_VERT}{nb_ok}{RESET}{BOLD}/{nb_total}{RESET}  |  "
        f"Erreurs : {C_ROUGE if erreurs else C_VERT}{len(erreurs)}{RESET}  |  "
        f"Ignorés : {C_GRIS}{nb_ignore}{RESET}  |  "
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

    pdfs_a_traiter = selectionner_fichiers(pdfs, dossier_pdf)
    if not pdfs_a_traiter:
        print("Aucun fichier PDF sélectionné.", file=sys.stderr)
        return

    dossier_sortie = _preparer_dossier_sortie(dossier_pdf, format_sortie)
    convertisseur  = ConverterFactory.create(outil)
    erreurs: list[str] = []

    for nom_pdf in pdfs_a_traiter:
        ok = _traiter_un_pdf(
            nom_pdf, dossier_pdf, dossier_sortie,
            convertisseur, format_sortie,
        )
        if not ok:
            erreurs.append(nom_pdf)

    _afficher_bilan(
        len(pdfs_a_traiter) - len(erreurs), len(pdfs_a_traiter), len(pdfs) - len(pdfs_a_traiter), 
        erreurs, dossier_sortie, format_sortie,
    )