#!/usr/bin/env python3
"""
Point d'entrée CLI du parseur d'articles scientifiques.

Sprint 3 : -t, -x, ou les deux simultanément (-t -x).
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
from utils.colors import RESET, BOLD, C_BLEU, C_CYAN, C_ROUGE


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Parseur d'articles scientifiques PDF → texte et/ou XML (Sprint 3)",
        epilog="Exemples :\n"
               "  python main.py misc -t        # texte seulement\n"
               "  python main.py misc -x        # XML seulement\n"
               "  python main.py misc -t -x     # les deux formats\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    ap.add_argument(
        "-t",
        dest="format_texte",
        action="store_true",
        help="Générer la sortie au format texte .txt",
    )
    ap.add_argument(
        "-x",
        dest="format_xml",
        action="store_true",
        help="Générer la sortie au format XML .xml",
    )
    return ap


def main() -> None:
    args = _build_parser().parse_args()

    # Si aucun format spécifié → texte par défaut
    if not args.format_texte and not args.format_xml:
        args.format_texte = True

    formats = []
    if args.format_texte:
        formats.append(FORMAT_TEXTE)
    if args.format_xml:
        formats.append(FORMAT_XML)

    afficher_banner()
    print(
        f"  {C_BLEU}{BOLD}Outil de conversion : {RESET}{C_CYAN}{args.outil}{RESET}",
        file=sys.stderr,
    )
    print(
        f"  {C_BLEU}{BOLD}Formats de sortie   : {RESET}{C_CYAN}{' + '.join(f.upper() for f in formats)}{RESET}",
        file=sys.stderr,
    )
    print(file=sys.stderr)

    for format_sortie in formats:
        traiter_dossier(args.dossier, args.outil, format_sortie)


if __name__ == "__main__":
    main()