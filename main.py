#!/usr/bin/env python3
"""
Point d'entrée CLI du parseur d'articles scientifiques.

Sprint 3 : ajout de l'argument de format de sortie (-t | -x).
"""

import argparse
import sys
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from utils.banner import afficher_banner
from batch_processor import traiter_dossier, FORMAT_TEXTE, FORMAT_XML
from converters.pdf_converter import ConverterFactory
from utils.colors import RESET, BOLD, C_BLEU, C_CYAN


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Parseur d'articles scientifiques PDF → texte ou XML (Sprint 3)"
    )
    ap.add_argument(
        "dossier",
        help="Chemin vers le dossier contenant les fichiers PDF",
    )
    ap.add_argument(
        "--outil",
        choices=ConverterFactory.available_names(),
        default="pdftotext",
        help="Outil de conversion PDF→texte (défaut : pdftotext)",
    )

    # Groupe mutuellement exclusif : -t ou -x
    groupe_format = ap.add_mutually_exclusive_group()
    groupe_format.add_argument(
        "-t",
        dest="format_sortie",
        action="store_const",
        const=FORMAT_TEXTE,
        help="Sortie au format texte .txt (défaut)",
    )
    groupe_format.add_argument(
        "-x",
        dest="format_sortie",
        action="store_const",
        const=FORMAT_XML,
        help="Sortie au format XML .xml",
    )
    ap.set_defaults(format_sortie=FORMAT_TEXTE)

    return ap


def main() -> None:
    args = _build_parser().parse_args()

    afficher_banner()
    print(
        f"  {C_BLEU}{BOLD}Outil de conversion : {RESET}{C_CYAN}{args.outil}{RESET}",
        file=sys.stderr,
    )
    print(
        f"  {C_BLEU}{BOLD}Format de sortie    : {RESET}{C_CYAN}{args.format_sortie.upper()}{RESET}",
        file=sys.stderr,
    )
    print(file=sys.stderr)

    traiter_dossier(args.dossier, args.outil, args.format_sortie)


if __name__ == "__main__":
    main()
