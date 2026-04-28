#!/usr/bin/env python3
"""
Parseur d'articles scientifiques en format texte
Projet Scrum - Sprint 1
LIA / Avignon Université
"""

import re
import sys
import os
import shutil
import argparse
import subprocess
import tempfile
import time

# COULEURS ANSI 24-bit (hex → RGB)
RESET   = "\033[0m"
BOLD    = "\033[1m"
C_BLEU  = "\033[38;2;88;166;255m"   # #58A6FF  titres / headers
C_CYAN  = "\033[38;2;121;192;255m"  # #79C0FF  noms de fichiers
C_VERT  = "\033[38;2;63;185;80m"    # #3FB950  succès
C_ROUGE = "\033[38;2;248;81;73m"    # #F85149  erreurs
C_JAUNE = "\033[38;2;210;153;34m"   # #D29922  avertissements
C_GRIS  = "\033[38;2;139;148;158m"  # #8B949E  labels / stats


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

    # ── Passe 1.5 : extraction auteurs (entre titre et abstract) ──
    if titre_trouve:
        auteur_lignes = []
        for i in range(idx_fin_titre, min(idx_fin_titre + 15, len(lignes))):
            l = lignes[i].strip()
            if not l:
                continue
            if detecter_section(l):
                break
            if re.match(r"^abstract[\s\.\—\–\:]?", l, re.IGNORECASE):
                break
            # Heuristique : ligne d'auteurs contient des noms propres, virgules, "and"
            # Exclure les lignes qui ressemblent à des affiliations (université, lab, etc.)
            if re.search(r"@|universit|laboratoire|department|institute|lab\b|faculty", l, re.IGNORECASE):
                continue
            # Ligne probable d'auteurs : mots capitalisés séparés par virgules ou "and"
            if re.match(r"^[A-ZÀ-Ÿ]", l) and len(l) < 200:
                if re.search(r",|\band\b|·|;", l) or re.match(r"^([A-ZÀ-Ÿ][a-zà-ÿ]+[\s\.\-]*){2,6}$", l):
                    auteur_lignes.append(l)
        if auteur_lignes:
            sections["auteurs"] = " ".join(auteur_lignes)

    # ── Passe 2 : sections ──
    section_courante = None
    contenu_courant = []

    for ligne in lignes[idx_fin_titre:]:
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


def une_ligne(texte: str) -> str:
    """Transforme un texte multi-lignes en une seule ligne."""
    return re.sub(r"\s+", " ", texte).strip()


def formater_sortie_sprint2(sections: dict[str, str], nom_fichier: str) -> str:
    """
    Format Sprint 2 : fichier, titre, auteurs, résumé — chacun sur une ligne.
    """
    lignes = []
    lignes.append(f"Fichier : {nom_fichier}")
    lignes.append(f"Titre : {une_ligne(sections.get('titre', ''))}")
    lignes.append(f"Auteurs : {une_ligne(sections.get('auteurs', ''))}")
    lignes.append(f"Resume : {une_ligne(sections.get('abstract', ''))}")
    return "\n".join(lignes)


def afficher_statistiques(sections: dict[str, str]):
    print(f"\n{C_BLEU}{BOLD}── Statistiques ──────────────────────────────{RESET}")
    trouvees = [k for k, v in sections.items() if v.strip()]
    manquantes = [k for k, v in sections.items() if not v.strip()]
    print(f"  {C_GRIS}Sections trouvées  ({len(trouvees)}) :{RESET} {C_VERT}{', '.join(trouvees)}{RESET}")
    if manquantes:
        print(f"  {C_GRIS}Sections absentes  ({len(manquantes)}) :{RESET} {C_JAUNE}{', '.join(manquantes)}{RESET}")
    print(f"{C_BLEU}──────────────────────────────────────────────{RESET}\n")

# COMPARAISON

def comparer_outils(pdf_path: str):
    """
    Compare par benchmark deux méthodes d'extraction de PDF.
    """
    print(f"\n{C_BLEU}{BOLD}{'='*60}{RESET}")
    print(f"{C_BLEU}{BOLD} COMPARAISON pdftotext vs pdf2txt{RESET}")
    print(f"{C_GRIS} Fichier : {C_CYAN}{os.path.basename(pdf_path)}{RESET}")
    print(f"{C_BLEU}{BOLD}{'='*60}{RESET}\n")
    resultats = {}

    # les outils à tester
    for nom, convertir in [("pdftotext -layout", convert_pdftotext),
                            ("pdf2txt.py", convert_pdf2txt)]:
        print(f"{C_BLEU}{BOLD}── {nom} ──────────────────────────────{RESET}")
        try:
            texte = convertir(pdf_path) # Extrait texte brut
            sections = parser_article(texte) # Identification structurelle
            trouvees = [k for k, v in sections.items() if v.strip()] # section trouvées
            nb_mots = len(texte.split())
            mots_colles = len(re.findall(r"[a-z]{15,}", texte)) # mots louches >15 char

            qualite = f"{C_ROUGE}texte dégradé{RESET}" if mots_colles > 50 else f"{C_VERT}bon{RESET}"
            print(f"  {C_GRIS}Mots extraits        :{RESET} {nb_mots}")
            print(f"  {C_GRIS}Sections détectées   :{RESET} {len(trouvees)} → {C_VERT}{', '.join(trouvees)}{RESET}")
            print(f"  {C_GRIS}Mots collés (≥15c)   :{RESET} {mots_colles}  {qualite}")

            resultats[nom] = {"sections": len(trouvees), "mots_colles": mots_colles}
        except Exception as e:
            print(f"  {C_ROUGE}ERREUR : {e}{RESET}")
        print()
    print(f"{C_BLEU}{BOLD}── Verdict ──────────────────────────────────{RESET}")
    if resultats: # comparaison finale
        # le meilleur est celui qui a le mieux découpé les mots
        meilleur = min(resultats, key=lambda x: resultats[x]["mots_colles"])
        print(f"{C_VERT}{BOLD}Outil recommandé : {meilleur}{RESET}")
    print()



def traiter_dossier(dossier_pdf: str, outil: str = "pdftotext") -> None:
    """
    Parcourt dossier_pdf, parse chaque PDF et écrit les .txt dans
    dossier_pdf/output/ (le sous-dossier est effacé s'il existe).
    """
    if not os.path.isdir(dossier_pdf):
        print(f"Erreur : dossier introuvable : {dossier_pdf}", file=sys.stderr)
        sys.exit(1)

    # Sous-dossier de sortie
    dossier_sortie = os.path.join(dossier_pdf, "output")

    if os.path.exists(dossier_sortie):
        print(f"{C_JAUNE}Suppression de l'ancien dossier : {dossier_sortie}{RESET}", file=sys.stderr)
        shutil.rmtree(dossier_sortie)

    os.makedirs(dossier_sortie)
    print(f"{C_VERT}Dossier de sortie créé : {dossier_sortie}{RESET}", file=sys.stderr)

    # Lister les PDFs
    pdfs = sorted([
        f for f in os.listdir(dossier_pdf)
        if f.lower().endswith(".pdf")
    ])

    if not pdfs:
        print("Aucun fichier PDF trouvé dans le dossier.", file=sys.stderr)
        return

    convertir = convert_pdf2txt if outil == "pdf2txt" else convert_pdftotext
    ok = 0
    erreurs = []

    for nom_pdf in pdfs:
        chemin_pdf = os.path.join(dossier_pdf, nom_pdf)
        nom_base = os.path.splitext(nom_pdf)[0]
        chemin_txt = os.path.join(dossier_sortie, nom_base + ".txt")

        print(f"  {C_CYAN}{nom_pdf}{RESET}", file=sys.stderr, end=" ")

        try:
            texte_brut = convertir(chemin_pdf)
            sections = parser_article(texte_brut)
            sortie = formater_sortie_sprint2(sections, nom_pdf)

            with open(chemin_txt, "w", encoding="utf-8") as f:
                f.write(sortie + "\n")

            print(f"{C_VERT}✓{RESET}", file=sys.stderr)
            ok += 1

        except Exception as e:
            print(f"{C_ROUGE}✗ ERREUR : {e}{RESET}", file=sys.stderr)
            erreurs.append(nom_pdf)

    print(f"\n{C_BLEU}{'─'*50}{RESET}", file=sys.stderr)
    print(f"{BOLD}Traités : {C_VERT}{ok}{RESET}{BOLD}/{len(pdfs)}{RESET}  |  Erreurs : {C_ROUGE if erreurs else C_VERT}{len(erreurs)}{RESET}", file=sys.stderr)
    if erreurs:
        print(f"{C_ROUGE}Fichiers en erreur : {', '.join(erreurs)}{RESET}", file=sys.stderr)
    print(f"{C_GRIS}Sorties dans : {dossier_sortie}{RESET}", file=sys.stderr)

# ANIMATION DÉMARRAGE

def afficher_banner():
    """Affiche un banner animé au démarrage."""
    os.system("cls" if os.name == "nt" else "clear")
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

    # Dégradé bleu→cyan sur chaque ligne du logo
    GRAD = [
        "\033[38;2;88;166;255m",   # #58A6FF
        "\033[38;2;99;179;255m",
        "\033[38;2;110;192;255m",
        "\033[38;2;121;192;255m",  # #79C0FF
        "\033[38;2;132;205;255m",
        "\033[38;2;143;218;255m",
    ]

    LOGO = [
        r" ____   ___   _____   ____    _   _  _   _ ",
        r"|  _ \ |  _ \|  ___| |  _ \  | | | || \ | |",
        r"| |_) || | | | |_    | |_) | | | | ||  \| |",
        r"|  __/ | |_| |  _|   |  _ <  | |_| || |\  |",
        r"|_|    |____/|_|     |_| \_\  \___/ |_| \_|",
    ]
    SOUS_TITRE = "  Parseur d'articles scientifiques  ·  Sprint 2  ·  LIA Avignon"
    SEPARATEUR = "  " + "─" * 50

    print(HIDE_CURSOR, end="", file=sys.stderr)
    print(file=sys.stderr)

    # Animation : révèle le logo caractère par caractère ligne par ligne
    for i, ligne in enumerate(LOGO):
        couleur = GRAD[i % len(GRAD)]
        print(f"  {couleur}{BOLD}", end="", file=sys.stderr)
        for char in ligne:
            print(char, end="", flush=True, file=sys.stderr)
            time.sleep(0.004)
        print(RESET, file=sys.stderr)

    # Sous-titre qui apparaît lettre par lettre
    time.sleep(0.05)
    print(f"\n{C_CYAN}", end="", file=sys.stderr)
    for char in SOUS_TITRE:
        print(char, end="", flush=True, file=sys.stderr)
        time.sleep(0.018)
    print(RESET, file=sys.stderr)

    # Barre de chargement animée
    time.sleep(0.1)
    LARGEUR = 40
    print(f"\n  {C_GRIS}Initialisation ", end="", file=sys.stderr)
    print(f"{C_BLEU}[", end="", flush=True, file=sys.stderr)
    for i in range(LARGEUR):
        time.sleep(0.018)
        # dégradé vert sur la barre
        r = int(63  + (88  - 63)  * i / LARGEUR)
        g = int(185 + (166 - 185) * i / LARGEUR)
        b = int(80  + (255 - 80)  * i / LARGEUR)
        print(f"\033[38;2;{r};{g};{b}m█", end="", flush=True, file=sys.stderr)
    print(f"{C_BLEU}]{RESET} {C_VERT}{BOLD}prêt !{RESET}", file=sys.stderr)

    # Séparateur final
    time.sleep(0.05)
    print(f"\n{C_BLEU}{BOLD}{SEPARATEUR}{RESET}\n", file=sys.stderr)
    print(SHOW_CURSOR, end="", file=sys.stderr)


# POINT D'ENTRÉE

def main():
    ap = argparse.ArgumentParser(description="Parseur d'articles scientifiques PDF → texte structuré (Sprint 2)")
    ap.add_argument("dossier", help="Chemin vers le dossier contenant les fichiers PDF")
    ap.add_argument("--outil", choices=["pdftotext", "pdf2txt"], default="pdftotext", help="Outil de conversion PDF→texte (défaut : pdftotext)")
    args = ap.parse_args()

    afficher_banner()
    print(f"  {C_BLEU}{BOLD}Outil de conversion : {RESET}{C_CYAN}{args.outil}{RESET}", file=sys.stderr)
    print(file=sys.stderr)
    traiter_dossier(args.dossier, args.outil)

if __name__ == "__main__":
    main()
