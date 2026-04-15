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

    # Sous-sections → corps (on les ignore comme nouvelles sections)
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

    # Extraire la partie gauche (avant grand espace = double colonne)
    gauche = re.split(r"\s{4,}", norm)[0].strip()

    # Cas 1 : titre seul sans numéro
    #   ex : "Abstract", "Introduction", "References"
    if re.match(r"^[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s\-]{1,60}$", gauche):
        sec = classer_titre(gauche)
        if sec:
            return sec

    # Cas 2 : numéro arabe + titre
    #   ex : "1 Introduction", "2.1 Early Work", "3     The RST..."
    m = re.match(r"^(\d+[\.\d]*)\s+(.+)$", gauche)
    if m:
        titre = m.group(2).strip()
        sec = classer_titre(titre)
        if sec:
            return sec

    # Cas 3 : numéro romain IEEE + titre
    #   ex : "I. INTRODUCTION", "VI. EXPERIMENTS AND RESULTS"
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


# PARSING PRINCIPAL

SECTIONS_ORDRE = ["titre", "auteurs", "abstract", "introduction",
                  "corps", "conclusion", "discussion", "bibliographie"]


def est_titre_article(ligne: str) -> bool:
    s = ligne.strip()
    if not s or len(s) < 5:
        return False
    if s.endswith((".com", ".fr", ".org", "@")):
        return False
    mots = s.split()
    return 2 <= len(mots) <= 20


def parser_article(texte: str) -> dict[str, str]:
    sections = {k: "" for k in SECTIONS_ORDRE}
    texte = nettoyer_texte(texte)
    lignes = texte.split("\n")

    # ── Passe 1 : extraction titre ──
    titre_trouve = False
    idx_fin_titre = 0
    for i, ligne in enumerate(lignes):
        stripped = ligne.strip()
        if not stripped:
            continue
        if not titre_trouve and est_titre_article(ligne):
            titre_lignes = [stripped]
            j = i + 1
            while j < len(lignes) and j < i + 5:
                nl = lignes[j].strip()
                if not nl:
                    j += 1; continue
                if detecter_section(nl):
                    break
                if re.match(r"^abstract[\s\.\—\–\:]?", nl, re.IGNORECASE):
                    break
                if est_titre_article(lignes[j]) and not re.search(r"@|\d{4,}", nl):
                    titre_lignes.append(nl)
                    j += 1
                else:
                    break
            sections["titre"] = " ".join(titre_lignes)
            titre_trouve = True
            idx_fin_titre = j
            break

    # ── Passe 2 : sections ──
    section_courante = None
    contenu_courant = []

    for ligne in lignes:
        stripped = ligne.strip()

        nom_sec = detecter_section(ligne)
        if nom_sec:
            # Sauvegarder section précédente
            if section_courante and contenu_courant:
                contenu = "\n".join(contenu_courant).strip()
                if contenu:
                    if not sections[section_courante]:
                        sections[section_courante] = contenu
                    else:
                        sections[section_courante] += "\n\n" + contenu
            section_courante = nom_sec
            # Abstract inline : garder le texte après le mot-clé
            if nom_sec == "abstract":
                reste = re.sub(r"^abstract[\s\.\—\–\:\*]+", "", stripped,
                               flags=re.IGNORECASE).strip()
                contenu_courant = [reste] if reste else []
            else:
                contenu_courant = []
            continue

        # Abstract seul sur sa ligne (centré)
        if re.match(r"^\s*abstract\s*$", stripped, re.IGNORECASE):
            if section_courante and contenu_courant:
                contenu = "\n".join(contenu_courant).strip()
                if contenu and not sections[section_courante]:
                    sections[section_courante] = contenu
            section_courante = "abstract"
            contenu_courant = []
            continue

        # Sauter les lignes de header de page (ex: "WiSeBE: Window-Based...")
        if section_courante and re.match(r"^\s{10,}", ligne) and len(stripped) > 30:
            # ligne très indentée = probable header de page dans Springer
            if re.search(r"[A-Z]\.\-[A-Z]\.", stripped):  # pattern auteur
                continue

        if section_courante:
            contenu_courant.append(ligne)

    # Sauvegarder la toute dernière section de l'article (souvent 'bibliographie')
    if section_courante and contenu_courant:
        contenu = "\n".join(contenu_courant).strip()
        if contenu and not sections[section_courante]:
            sections[section_courante] = contenu

    # Post-traitement : on enlève les trous / sauts de lignes abusifs
    for k in sections:
        if sections[k]:
            sections[k] = re.sub(r"\n{3,}", "\n\n", sections[k]).strip()

    return sections

# FORMATAGE

LABELS = {
    "titre":        "Titre",
    "auteurs":      "Auteurs",
    "abstract":     "Abstract",
    "introduction": "Introduction",
    "corps":        "Corps",
    "resultats":    "Résultats",
    "conclusion":   "Conclusion",
    "discussion":   "Discussion",
    "bibliographie": "Bibliographie",
}


def formater_sortie(sections: dict[str, str]) -> str:
    """
    Transforme le dictionnaire des sections en un texte propre et indenté.
    """
    lignes = []
    for cle, label in LABELS.items():
        contenu = sections.get(cle, "").strip()
        if contenu:
            lignes.append(f"{label} :")
            # Indentation du contenu pour que ça soit bien lisible
            for l in contenu.split("\n"):
                lignes.append(f"    {l}")
            lignes.append("")
    
    return "\n".join(lignes)


def afficher_statistiques(sections: dict[str, str]):
    print("\n── Statistiques ──────────────────────────────")
    trouvees = [k for k, v in sections.items() if v.strip()]
    manquantes = [k for k, v in sections.items() if not v.strip()]
    print(f"  Sections trouvées  ({len(trouvees)}) : {', '.join(trouvees)}")
    if manquantes:
        print(f"  Sections absentes  ({len(manquantes)}) : {', '.join(manquantes)}")
    print("──────────────────────────────────────────────\n")

# COMPARAISON

def comparer_outils(pdf_path: str):
    """
    Compare par benchmark deux méthodes d'extraction de PDF.
    """
    print(f"\n{'='*60}")
    print(f" COMPARAISON pdftotext vs pdf2txt")
    print(f" Fichier : {os.path.basename(pdf_path)}")
    print(f"{'='*60}\n")
    resultats = {}

    # les outils à tester
    for nom, convertir in [("pdftotext -layout", convert_pdftotext),
                            ("pdf2txt.py", convert_pdf2txt)]:
        print(f"── {nom} ──────────────────────────────")
        try:
            texte = convertir(pdf_path) # Extrait texte brut
            sections = parser_article(texte) # Identification structurelle
            trouvees = [k for k, v in sections.items() if v.strip()] # section trouvées
            nb_mots = len(texte.split())
            mots_colles = len(re.findall(r"[a-z]{15,}", texte)) # mots louches >15 char

            print(f"  Mots extraits        : {nb_mots}")
            print(f"  Sections détectées   : {len(trouvees)} → {', '.join(trouvees)}")
            print(f"  Mots collés (≥15c)   : {mots_colles}  {'texte dégradé' if mots_colles > 50 else 'bon'}")
            
            resultats[nom] = {"sections": len(trouvees), "mots_colles": mots_colles}
        except Exception as e:
            print(f"  ERREUR : {e}")
        print()
    print("── Verdict ──────────────────────────────────")
    if resultats: # comparaison finale
        # le meilleur est celui qui a le mieux découpé les mots
        meilleur = min(resultats, key=lambda x: resultats[x]["mots_colles"])
        print(f"Outil recommandé : {meilleur}")
    print()

# POINT D'ENTRÉE

def main():
    ap = argparse.ArgumentParser(
        description="Parseur d'articles scientifiques PDF → texte structuré"
    )
    ap.add_argument("pdf", help="Chemin vers le fichier PDF")
    ap.add_argument("--outil", choices=["pdftotext", "pdf2txt"], default="pdftotext")
    ap.add_argument("--comparer", action="store_true")
    ap.add_argument("--sortie", "-o", default=None)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Erreur : fichier introuvable → {args.pdf}", file=sys.stderr)
        sys.exit(1)

    if args.comparer:
        comparer_outils(args.pdf)
        return

    print(f"Conversion avec {args.outil}...", file=sys.stderr)
    texte_brut = (convert_pdf2txt(args.pdf) if args.outil == "pdf2txt"
                  else convert_pdftotext(args.pdf))

    print("Parsing des sections...", file=sys.stderr)
    sections = parser_article(texte_brut)
    sortie = formater_sortie(sections)

    if args.stats:
        afficher_statistiques(sections)

    fichier_sortie = args.sortie or (
        os.path.splitext(os.path.basename(args.pdf))[0] + "_parse.txt"
    )
    with open(fichier_sortie, "w", encoding="utf-8") as f:
        f.write(sortie)

    print(f"Fichier créé : {fichier_sortie}", file=sys.stderr)


if __name__ == "__main__":
    main()
