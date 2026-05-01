"""
Animation de démarrage : banner ASCII + barre de chargement.
"""

import os
import sys
import time

from utils.colors import (
    RESET, BOLD, C_BLEU, C_CYAN, C_VERT, C_GRIS
)

_LOGO = [
    r" ____   ___   _____   ____    _   _  _   _ ",
    r"|  _ \ |  _ \|  ___| |  _ \  | | | || \ | |",
    r"| |_) || | | | |_    | |_) | | | | ||  \| |",
    r"|  __/ | |_| |  _|   |  _ <  | |_| || |\  |",
    r"|_|    |____/|_|     |_| \_\  \___/ |_| \_|",
]

_GRAD = [
    "\033[38;2;88;166;255m",
    "\033[38;2;99;179;255m",
    "\033[38;2;110;192;255m",
    "\033[38;2;121;192;255m",
    "\033[38;2;132;205;255m",
    "\033[38;2;143;218;255m",
]

_SOUS_TITRE  = "  Parseur d'articles scientifiques  ·  Sprint 2  ·  LIA Avignon"
_SEPARATEUR  = "  " + "─" * 50
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"


def _afficher_logo() -> None:
    for i, ligne in enumerate(_LOGO):
        couleur = _GRAD[i % len(_GRAD)]
        print(f"  {couleur}{BOLD}", end="", file=sys.stderr)
        for char in ligne:
            print(char, end="", flush=True, file=sys.stderr)
            time.sleep(0.004)
        print(RESET, file=sys.stderr)


def _afficher_sous_titre() -> None:
    time.sleep(0.05)
    print(f"\n{C_CYAN}", end="", file=sys.stderr)
    for char in _SOUS_TITRE:
        print(char, end="", flush=True, file=sys.stderr)
        time.sleep(0.018)
    print(RESET, file=sys.stderr)


def _afficher_barre_chargement(largeur: int = 40) -> None:
    time.sleep(0.1)
    print(f"\n  {C_GRIS}Initialisation ", end="", file=sys.stderr)
    print(f"{C_BLEU}[", end="", flush=True, file=sys.stderr)
    for i in range(largeur):
        time.sleep(0.018)
        r = int(63  + (88  - 63)  * i / largeur)
        g = int(185 + (166 - 185) * i / largeur)
        b = int(80  + (255 - 80)  * i / largeur)
        print(f"\033[38;2;{r};{g};{b}m█", end="", flush=True, file=sys.stderr)
    print(f"{C_BLEU}]{RESET} {C_VERT}{BOLD}prêt !{RESET}", file=sys.stderr)


def afficher_banner() -> None:
    """Affiche le banner animé complet au démarrage."""
    os.system("cls" if os.name == "nt" else "clear")
    print(_HIDE_CURSOR, end="", file=sys.stderr)
    print(file=sys.stderr)

    _afficher_logo()
    _afficher_sous_titre()
    _afficher_barre_chargement()

    time.sleep(0.05)
    print(f"\n{C_BLEU}{BOLD}{_SEPARATEUR}{RESET}\n", file=sys.stderr)
    print(_SHOW_CURSOR, end="", file=sys.stderr)
