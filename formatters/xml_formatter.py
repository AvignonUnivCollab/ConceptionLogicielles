"""
Formateur de sortie XML pour le Sprint 4.

Produit un fichier XML utf-8 conforme à la structure demandée :
  <article>
    <preamble>nom_fichier</preamble>
    <titre>...</titre>
    <auteurs>
      <auteur>
        <name>...</name>
        <mail>...</mail>
        <affiliation>...</affiliation>
      </auteur>
      ...
    </auteurs>
    <abstract>...</abstract>
    <introduction>...</introduction>
    <corps>...</corps>
    <conclusion>...</conclusion>
    <discussion>...</discussion>
    <biblio>...</biblio>
  </article>
"""

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

from formatters.article_formatter import ArticleFormatter


# Caractères interdits en XML 1.0 (hors tab, LF, CR)
_CARACTERES_INVALIDES_XML = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uFFFE\uFFFF]"
)


def _nettoyer_xml(texte: str) -> str:
    """
    Supprime les caractères invalides en XML 1.0 et compresse
    le texte en une seule ligne.
    """
    texte = _CARACTERES_INVALIDES_XML.sub("", texte)
    return re.sub(r"\s+", " ", texte).strip()


def _prettify(element: ET.Element) -> str:
    """Retourne le XML indenté."""
    brut = ET.tostring(element, encoding="unicode", xml_declaration=False)
    # Nettoyage de sécurité sur la chaîne brute entière
    brut = _CARACTERES_INVALIDES_XML.sub("", brut)
    reparsed = minidom.parseString(f'<?xml version="1.0" encoding="utf-8"?>{brut}')
    return reparsed.toprettyxml(indent="  ", encoding=None)


def _construire_auteurs(
    noms_bruts: str,
    emails_bruts: str,
    affiliation: str = "",
) -> list[dict[str, str]]:
    """
    Associe chaque nom d'auteur à un email et une affiliation.
    Les noms et emails sont séparés par ' ; ' (format produit par article_parser).
    Si moins d'emails que d'auteurs, les auteurs restants ont un email vide.
    L'affiliation est partagée par tous les auteurs (bloc commun de l'article).
    """
    if not noms_bruts.strip():
        return []

    noms   = [n.strip() for n in noms_bruts.split(";") if n.strip()]
    emails = [e.strip() for e in emails_bruts.split(";") if e.strip()] if emails_bruts else []
    return [
        {
            "name":        nom,
            "mail":        emails[i] if i < len(emails) else "",
            "affiliation": affiliation,
        }
        for i, nom in enumerate(noms)
    ]


class XmlFormatter(ArticleFormatter):
    """
    Formateur Sprint 4 : produit un fichier XML structuré.
    Hérite de ArticleFormatter (OCP — extensible sans modifier l'existant).
    Les emails et affiliations sont lus directement depuis le dict sections.
    """

    def format(self, sections: dict[str, str], nom_fichier: str) -> str:
        """Retourne une chaîne XML utf-8 représentant l'article."""
        article = ET.Element("article")

        ET.SubElement(article, "preamble").text = nom_fichier

        ET.SubElement(article, "titre").text = _nettoyer_xml(
            sections.get("titre", "")
        )

        affiliation = _nettoyer_xml(sections.get("affiliations", ""))
        auteurs_el = ET.SubElement(article, "auteurs")
        for auteur in _construire_auteurs(
            sections.get("auteurs", ""),
            sections.get("emails", ""),
            affiliation,
        ):
            auteur_el = ET.SubElement(auteurs_el, "auteur")
            ET.SubElement(auteur_el, "name").text = _nettoyer_xml(auteur["name"])
            ET.SubElement(auteur_el, "mail").text = auteur["mail"]
            ET.SubElement(auteur_el, "affiliation").text = auteur["affiliation"]

        ET.SubElement(article, "abstract").text = _nettoyer_xml(
            sections.get("abstract", "")
        )

        ET.SubElement(article, "introduction").text = _nettoyer_xml(
            sections.get("introduction", "")
        )

        ET.SubElement(article, "corps").text = _nettoyer_xml(
            sections.get("corps", "")
        )

        ET.SubElement(article, "conclusion").text = _nettoyer_xml(
            sections.get("conclusion", "")
        )

        ET.SubElement(article, "discussion").text = _nettoyer_xml(
            sections.get("discussion", "")
        )

        ET.SubElement(article, "biblio").text = _nettoyer_xml(
            sections.get("bibliographie", "")
        )

        return _prettify(article)