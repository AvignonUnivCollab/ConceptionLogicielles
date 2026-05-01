"""
Nettoyage et normalisation du texte brut extrait d'un PDF.

Responsabilité unique : préparer le texte avant le parsing structurel.
"""

import re


def nettoyer_texte(texte: str) -> str:
    """
    Supprime les numéros de page isolés et les sauts de page.
    """
    lignes = texte.split("\n")
    propres = [
        ligne.replace("\f", "")
        for ligne in lignes
        if not re.match(r"^\s*\d+\s*$", ligne)
    ]
    return "\n".join(propres)


def reconstruire_mots_ieee(texte: str) -> str:
    """
    Reconstitue les mots éclatés au format IEEE colonne.
    Exemples : 'I NTRODUCTION' → 'INTRODUCTION', 'E XPERIMENTS' → 'EXPERIMENTS'.
    """
    return re.sub(
        r'\b([A-Z]) ([A-Z][A-Z ]{1,20}[A-Z])\b',
        lambda m: m.group(1) + m.group(2).replace(" ", ""),
        texte,
    )


def supprimer_sauts_excessifs(texte: str) -> str:
    """Réduit les séquences de 3 sauts de ligne ou plus à 2 maximum."""
    return re.sub(r"\n{3,}", "\n\n", texte).strip()
