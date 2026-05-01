"""
Convertisseurs PDF → texte brut.

Architecture :
  - PdfConverter   : interface abstraite (OCP / DIP)
  - PdfToTextConverter : implémentation via `pdftotext -layout`
  - Pdf2TxtConverter   : implémentation via `pdf2txt.py`
  - ConverterFactory   : fabrique centralisée (DIP)
"""

import os
import subprocess
import tempfile
from abc import ABC, abstractmethod


class PdfConverter(ABC):
    """Interface commune pour toute conversion PDF → texte."""

    @abstractmethod
    def convert(self, pdf_path: str) -> str:
        """Retourne le contenu textuel extrait du PDF."""


class PdfToTextConverter(PdfConverter):
    """Conversion via `pdftotext -layout` (preserve la mise en page)."""

    def convert(self, pdf_path: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run(
                ["pdftotext", "-layout", pdf_path, tmp_path],
                check=True,
                capture_output=True,
            )
            with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class Pdf2TxtConverter(PdfConverter):
    """Conversion via `pdf2txt.py` (pdfminer)."""

    def convert(self, pdf_path: str) -> str:
        result = subprocess.run(
            ["pdf2txt.py", pdf_path],
            capture_output=True,
            text=True,
            errors="replace",
        )
        return result.stdout


class ConverterFactory:
    """
    Fabrique de convertisseurs.
    Permet d'ajouter de nouveaux outils sans modifier le reste du code (OCP).
    """

    _registry: dict[str, type[PdfConverter]] = {
        "pdftotext": PdfToTextConverter,
        "pdf2txt":   Pdf2TxtConverter,
    }

    @classmethod
    def create(cls, name: str) -> PdfConverter:
        """
        Retourne une instance du convertisseur demandé.

        :raises ValueError: si le nom n'est pas enregistré.
        """
        if name not in cls._registry:
            available = ", ".join(cls._registry)
            raise ValueError(
                f"Convertisseur inconnu : '{name}'. Disponibles : {available}"
            )
        return cls._registry[name]()

    @classmethod
    def available_names(cls) -> list[str]:
        return list(cls._registry.keys())
