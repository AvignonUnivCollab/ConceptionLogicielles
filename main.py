#!/usr/bin/env python3
"""
Point d'entrée CLI du parseur d'articles scientifiques.

Ce module est volontairement mince : il ne fait que parser les arguments
et déléguer aux modules métier. Aucune logique fonctionnelle ici.
"""

import argparse
import sys

from utils.banner import afficher_banner
from batch_processor import traiter_dossier
from converters.pdf_converter import ConverterFactory
from utils.colors import RESET, BOLD, C_BLEU, C_CYAN


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Parseur d'articles scientifiques PDF → texte structuré (Sprint 2)"
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
    return ap


def main() -> None:
    args = _build_parser().parse_args()

    afficher_banner()
    print(
        f"  {C_BLEU}{BOLD}Outil de conversion : {RESET}{C_CYAN}{args.outil}{RESET}",
        file=sys.stderr,
    )
    print(file=sys.stderr)

    traiter_dossier(args.dossier, args.outil)


if __name__ == "__main__":
    main()
