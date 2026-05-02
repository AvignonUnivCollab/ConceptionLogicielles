"""
Parseur structurel d'un article scientifique.

Responsabilité unique : à partir d'un texte brut nettoyé, produire
un dictionnaire `{section: contenu}` en trois passes successives :
  1. Extraction du titre
  2. Extraction des auteurs
  3. Découpage des sections thématiques
"""

import re

from parsers.section_taxonomy import SECTIONS_ORDRE
from parsers.section_detector import detecter_section
from parsers.text_cleaner import (
    nettoyer_texte,
    supprimer_sauts_excessifs,
)


# Heuristiques locales
def _est_titre_article(ligne: str) -> bool:
    s = ligne.strip()
    if not s or len(s) < 5:
        return False
    if s.endswith((".com", ".fr", ".org", "@")):
        return False
    # Exclure les dates, numéros de volume, lignes d'affiliation
    if re.search(r"\d{4}|\bvol\b|\bno\b|@|universit|institute|department", s, re.IGNORECASE):
        return False
    mots = s.split()
    return 2 <= len(mots) <= 20


def _est_ligne_affiliation(ligne: str) -> bool:
    """
    Détecte les lignes d'affiliation institutionnelle.
    Couvre : universités, labos, emails, adresses postales, CP, codes pays.
    """
    return bool(re.search(
        r"@|universit|laboratoir|department|institute|lab\b|faculty"
        r"|école|ecole|polytechnique|chemin|avenue|rue\b"
        r"|c\.p\.|succ\.|h\d[a-z]\s?\d[a-z]\d"   # codes postaux canadiens
        r"|\b\d{4,5}\b.*\b(france|canada|germany|spain|usa|uk)\b",
        ligne,
        re.IGNORECASE,
    ))


def _est_ligne_date_ou_volume(ligne: str) -> bool:
    """Détecte les lignes de date ou de référence de journal (ex: 'November 21, 2007')."""
    return bool(re.match(
        r"^\s*(january|february|march|april|may|june|july|august|september"
        r"|october|november|december|\d{1,2}\s+\w+\s+\d{4}|\d{4})\b",
        ligne,
        re.IGNORECASE,
    ))


def _est_ligne_auteurs(ligne: str) -> bool:
    """
    Détecte une ligne probable d'auteurs.

    Critères positifs :
      - Commence par une majuscule
      - Contient des séparateurs typiques (virgule, 'and', ·, ;)
        OU ressemble à un nom propre composé (Prénom Nom)
      - Peut contenir des exposants numériques/lettres d'affiliation (ex: 'Alice¹, Bob²')

    Critères négatifs :
      - Ligne d'affiliation institutionnelle
      - Ligne de date
      - Trop longue (> 200 caractères)
    """
    l = ligne.strip()
    if not l or len(l) >= 200:
        return False
    if not re.match(r"^[A-ZÀ-Ÿ]", l):
        return False
    if _est_ligne_affiliation(l):
        return False
    if _est_ligne_date_ou_volume(l):
        return False

    # Nettoyer les exposants d'affiliation avant d'analyser (¹²³⁴ ou 1,2)
    l_clean = re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹⁰\u00B9\u00B2\u00B3]", "", l)
    l_clean = re.sub(r"\s*\(\s*B\s*\)", "", l_clean)  # (B) = corresponding author Springer

    # Séparateurs typiques entre auteurs
    if re.search(r",|\band\b|·|;", l_clean):
        return True

    # Nom simple : Prénom [Initiale.] Nom (2 à 5 mots en majuscule)
    if re.match(r"^([A-ZÀ-Ÿ][a-zà-ÿ\-]+[\s\.\,]*){2,5}$", l_clean.strip()):
        return True

    return False


# Les trois passes d'extraction
def _extraire_titre(lignes: list[str]) -> tuple[str, int]:
    """
    Passe 1 : cherche le titre dans les premières lignes.
    Le titre s'arrête dès qu'une ligne ressemble à des auteurs,
    une affiliation, une section ou un abstract.
    Retourne (texte_titre, index_fin_titre).
    """
    for i, ligne in enumerate(lignes):
        stripped = ligne.strip()
        if not stripped:
            continue
        if not _est_titre_article(ligne):
            continue

        titre_lignes = [stripped]
        j = i + 1
        while j < len(lignes) and j < i + 6:
            nl = lignes[j].strip()
            if not nl:
                j += 1
                continue
            # Arrêt si on détecte une section, un abstract, des auteurs ou une affiliation
            if detecter_section(nl):
                break
            if re.match(r"^abstract[\s\.\—\–\:]?", nl, re.IGNORECASE):
                break
            if _est_ligne_auteurs(nl):
                break
            if _est_ligne_affiliation(nl):
                break
            if _est_ligne_date_ou_volume(nl):
                break
            if _est_titre_article(lignes[j]) and not re.search(r"@|\d{4,}", nl):
                titre_lignes.append(nl)
                j += 1
            else:
                break

        return " ".join(titre_lignes), j

    return "", 0


def _extraire_auteurs(lignes: list[str], debut: int) -> str:
    """
    Passe 1.5 : cherche les auteurs dans les lignes qui suivent le titre,
    avant l'abstract. Ignore les affiliations et les dates.

    On s'arrête dès qu'on rencontre une section, un abstract,
    ou une ligne qui n'est ni auteur ni affiliation (ex: résumé de conférence).
    """
    auteur_lignes = []
    # On scanne jusqu'à 25 lignes après le titre pour couvrir les formats Springer
    for i in range(debut, min(debut + 25, len(lignes))):
        l = lignes[i].strip()
        if not l:
            continue
        if detecter_section(l):
            break
        if re.match(r"^abstract[\s\.\—\–\:]?", l, re.IGNORECASE):
            break
        if _est_ligne_date_ou_volume(l):
            continue  # on saute la date mais on continue (cas Das_Martins)
        if _est_ligne_affiliation(l):
            continue  # on saute l'affiliation mais on continue
        if _est_ligne_auteurs(l):
            auteur_lignes.append(l)

    return " ; ".join(auteur_lignes) if auteur_lignes else ""


# Regex pour l'extraction des emails
_EMAIL_RE       = re.compile(r'[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}')
_MULTI_EMAIL_RE = re.compile(r'\{([^}]+)\}@([\w\.\-]+)')


def _extraire_emails(lignes: list[str], debut: int) -> list[str]:
    """
    Passe 1.6 : extrait toutes les adresses email trouvées dans la zone
    d'en-tête (entre le titre et l'abstract).

    Gère les formats courants :
      - email simple     : alice@labo.fr
      - emails groupés   : {alice, bob}@labo.fr
      - emails en ligne  : Alice Martin <alice@labo.fr>
    """
    emails: list[str] = []
    seen: set[str] = set()

    def _ajouter(addr: str) -> None:
        addr = addr.strip().lower()
        if addr and addr not in seen:
            seen.add(addr)
            emails.append(addr)

    for i in range(debut, min(debut + 35, len(lignes))):
        l = lignes[i]
        stripped = l.strip()
        if not stripped:
            continue
        if detecter_section(stripped):
            break
        if re.match(r"^abstract[\s\.\—\–\:]?", stripped, re.IGNORECASE):
            break

        # Format groupé : {alice, bob}@domain.com
        for m in _MULTI_EMAIL_RE.finditer(l):
            domain = m.group(2)
            for localpart in m.group(1).split(","):
                _ajouter(f"{localpart.strip()}@{domain}")

        # Emails standards (évite de re-capturer ceux déjà traités via {})
        for addr in _EMAIL_RE.findall(l):
            _ajouter(addr)

    return emails


def _extraire_sections(lignes: list[str]) -> dict[str, str]:
    """
    Passe 2 : parcourt les lignes et accumule le contenu par section.
    """
    sections: dict[str, str] = {k: "" for k in SECTIONS_ORDRE}
    section_courante: str | None = None
    contenu_courant: list[str] = []

    def _sauvegarder() -> None:
        if section_courante and contenu_courant:
            contenu = "\n".join(contenu_courant).strip()
            if contenu:
                sep = "\n\n" if sections[section_courante] else ""
                sections[section_courante] += sep + contenu

    for ligne in lignes:
        stripped = ligne.strip()

        nom_sec = detecter_section(ligne)
        if nom_sec:
            _sauvegarder()
            section_courante = nom_sec
            if nom_sec == "abstract":
                reste = re.sub(
                    r"^abstract[\s\.\—\–\:\*]+", "", stripped, flags=re.IGNORECASE
                ).strip()
                contenu_courant = [reste] if reste else []
            else:
                contenu_courant = []
            continue

        # Abstract seul centré sur sa ligne
        if re.match(r"^\s*abstract\s*$", stripped, re.IGNORECASE):
            _sauvegarder()
            section_courante = "abstract"
            contenu_courant = []
            continue

        if section_courante:
            contenu_courant.append(ligne)

    _sauvegarder()
    return sections


# Point d'entrée public
def parser_article(texte: str) -> dict[str, str]:
    """
    Parse un texte brut et retourne les sections de l'article.

    :param texte: texte extrait du PDF (non nettoyé).
    :return: dictionnaire {clé_section: contenu}.
    """
    sections: dict[str, str] = {k: "" for k in SECTIONS_ORDRE}

    texte = nettoyer_texte(texte)
    lignes = texte.split("\n")

    titre, idx_fin_titre = _extraire_titre(lignes)
    sections["titre"]   = titre
    sections["auteurs"] = _extraire_auteurs(lignes, idx_fin_titre)
    sections["emails"]  = " ; ".join(_extraire_emails(lignes, idx_fin_titre))

    sections_corps = _extraire_sections(lignes[idx_fin_titre:])
    for cle, contenu in sections_corps.items():
        if cle not in ("titre", "auteurs"):
            sections[cle] = contenu

    #normaliser les sauts de ligne
    for cle in sections:
        if sections[cle]:
            sections[cle] = supprimer_sauts_excessifs(sections[cle])

    return sections