"""
Extraction des adresses email depuis le texte brut d'un article.

Responsabilité unique : trouver toutes les adresses email présentes
dans les premières lignes du document (zone titre/auteurs/affiliations).
"""

import re


# Regex standard pour une adresse email
_PATTERN_EMAIL = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# Nombre de lignes à scanner depuis le début du document
_ZONE_ENTETE = 60


def extraire_emails(texte: str) -> list[str]:
    """
    Retourne la liste des emails trouvés dans l'en-tête du document.
    Les doublons sont supprimés tout en conservant l'ordre d'apparition.
    """
    lignes = texte.split("\n")[:_ZONE_ENTETE]
    entete = "\n".join(lignes)

    emails_vus: set[str] = set()
    emails: list[str] = []
    for email in _PATTERN_EMAIL.findall(entete):
        email_lower = email.lower()
        if email_lower not in emails_vus:
            emails_vus.add(email_lower)
            emails.append(email)
    return emails
