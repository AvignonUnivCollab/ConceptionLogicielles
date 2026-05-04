"""
Formateur de sortie XML pour le Sprint 3.

Produit un fichier XML utf-8 conforme à la structure demandée :
  <article>
    <preamble>nom_fichier</preamble>
    <titre>...</titre>
    <auteurs>
      <auteur>
        <name>...</name>
        <mail>...</mail>
      </auteur>
      ...
    </auteurs>
    <abstract>...</abstract>
    <biblio>...</biblio>
  </article>
"""

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

from formatters.article_formatter import ArticleFormatter


def _une_ligne(texte: str) -> str:
    """Compresse un texte multi-lignes en une seule ligne."""
    return re.sub(r"\s+", " ", texte).strip()


def _prettify(element: ET.Element) -> str:
    """Retourne le XML indenté en utf-8."""
    brut = ET.tostring(element, encoding="unicode")
    reparsed = minidom.parseString(brut)
    return reparsed.toprettyxml(indent="  ", encoding=None)


def _construire_auteurs(
    noms_bruts: str,
    emails: list[str],
) -> list[dict[str, str]]:
    """
    Associe chaque nom d'auteur à un email si possible.

    Les noms sont séparés par ' ; ' (format produit par article_parser).
    Les emails sont associés dans l'ordre d'apparition.
    Si moins d'emails que d'auteurs, les auteurs restants ont un email vide.
    """
    if not noms_bruts.strip():
        return []

    noms = [n.strip() for n in noms_bruts.split(";") if n.strip()]
    auteurs = []
    for i, nom in enumerate(noms):
        auteurs.append({
            "name": nom,
            "mail": emails[i] if i < len(emails) else "",
        })
    return auteurs


class XmlFormatter(ArticleFormatter):
    """
    Formateur Sprint 3 : produit un fichier XML structuré.
    Hérite de ArticleFormatter (OCP — extensible sans modifier l'existant).
    """

    def __init__(self, emails: list[str] | None = None):
        """
        :param emails: liste des emails extraits du document,
                       dans l'ordre d'apparition.
        """
        self._emails: list[str] = emails or []

    def format(self, sections: dict[str, str], nom_fichier: str) -> str:
        """
        Retourne une chaîne XML utf-8 représentant l'article.
        """
        article = ET.Element("article")

        # <preamble>
        ET.SubElement(article, "preamble").text = nom_fichier

        # <titre>
        ET.SubElement(article, "titre").text = _une_ligne(
            sections.get("titre", "")
        )

        # <auteurs>
        auteurs_el = ET.SubElement(article, "auteurs")
        auteurs_data = _construire_auteurs(
            sections.get("auteurs", ""),
            self._emails,
        )
        for auteur in auteurs_data:
            auteur_el = ET.SubElement(auteurs_el, "auteur")
            ET.SubElement(auteur_el, "name").text = auteur["name"]
            ET.SubElement(auteur_el, "mail").text = auteur["mail"]

        # <abstract>
        ET.SubElement(article, "abstract").text = _une_ligne(
            sections.get("abstract", "")
        )

        # <biblio>
        ET.SubElement(article, "biblio").text = _une_ligne(
            sections.get("bibliographie", "")
        )

        return _prettify(article)
