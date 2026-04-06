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
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(["pdftotext", "-layout", pdf_path, tmp_path],
                       check=True, capture_output=True)
        with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def convert_pdf2txt(pdf_path: str) -> str:
    result = subprocess.run(["pdf2txt.py", pdf_path],
                            capture_output=True, text=True, errors="replace")
    return result.stdout


# NETTOYAGE
def nettoyer_texte(texte: str) -> str:
    lignes = texte.split("\n")
    propres = []
    for ligne in lignes:
        if re.match(r"^\s*\d+\s*$", ligne):
            continue
        propres.append(ligne.replace("\f", ""))
    return "\n".join(propres)


def reconstruire_ieee(texte: str) -> str:
    """'I NTRODUCTION' → 'INTRODUCTION',  'E XPERIMENTS' → 'EXPERIMENTS'"""
    return re.sub(
        r'\b([A-Z]) ([A-Z][A-Z ]{1,20}[A-Z])\b',
        lambda m: m.group(1) + m.group(2).replace(" ", ""),
        texte
    )


# CLASSIFICATION DES SECTIONS
# Mots-clés associés à chaque section canonique
MOTS_CLES = {
    "abstract":     ["abstract", "résumé", "summary"],
    "introduction": ["introduction"],
    "corps":        ["method", "méthode", "approach", "approche", "background",
                     "related work", "related works", "travaux connexes",
                     "système", "system", "model", "modèle", "architecture",
                     "framework", "formulation", "methodology", "méthodologie",
                     "state of the art", "industrial context",
                     "single-document summarization", "multi-document summarization",
                     "sentence boundary detection", "rst spanish treebank",
                     "resources and statistics", "word representations"],
    "conclusion":   ["conclusion", "conclusions", "future work",
                     "conclusion and future", "conclusion and perspectives",
                     "discussion and future"],
    "discussion":   ["discussion", "analyse", "analysis"],
    "bibliographie": ["reference", "references", "bibliograph", "bibliography"],
}

# Sections qui ne doivent PAS être corps mais corps (sous-sections corps)
SOUS_SECTIONS_CORPS = [
    "early work", "machine learning", "naive-bayes", "hidden markov",
    "log-linear", "neural network", "deep natural", "abstraction",
    "topic-driven", "graph spreading", "centroid", "multilingual",
    "short summar", "sentence compress", "sequential document",
    "selecting a corpus", "instantiating", "designing the interface",
    "selecting and training", "managing the annotation", "validating",
    "delivering", "system overview", "normalization", "linguistic patterns",
    "pruning step", "ranking step", "experimental protocol",
    "window-boundaries", "general reference",
]


def classer_titre(titre: str) -> str | None:
    """
    Retourne la clé de section correspondant au titre, ou None.
    """
    t = titre.lower().strip()

    for ss in SOUS_SECTIONS_CORPS:
        if ss in t:
            return None  # ignore

    for section, mots in MOTS_CLES.items():
        for mot in mots:
            if mot in t or t.startswith(mot):
                return section

    return None


def detecter_section(ligne: str) -> str | None:
    """
    Détecte si une ligne est un titre de section principal.
    Retourne la clé de section ou None.
    """
    stripped = ligne.strip()
    if not stripped or len(stripped) > 150:
        return None

    # Reconstruire les mots IEEE espacés
    norm = reconstruire_ieee(stripped)

    # Extraire la partie gauche
    gauche = re.split(r"\s{4,}", norm)[0].strip()

    # Cas 1 : titre seul sans numéro
    if re.match(r"^[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s\-]{1,60}$", gauche):
        sec = classer_titre(gauche)
        if sec:
            return sec

    # Cas 2 : numéro arabe + titre
    m = re.match(r"^(\d+[\.\d]*)\s+(.+)$", gauche)
    if m:
        titre = m.group(2).strip()
        sec = classer_titre(titre)
        if sec:
            return sec

    # Cas 3 : numéro romain IEEE + titre
    m = re.match(r"^([IVXivx]+)[\.\s]+(.+)$", gauche)
    if m:
        titre = m.group(2).strip()
        sec = classer_titre(titre)
        if sec:
            return sec

    # Cas 4 : Abstract inline "Abstract—..." ou "Abstract. ..."
    if re.match(r"^abstract[\s\.\—\–\:]", stripped, re.IGNORECASE):
        return "abstract"

    return None
