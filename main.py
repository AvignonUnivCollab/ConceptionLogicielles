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
    """Conversion avec pdftotext -layout (poppler-utils)."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["pdftotext", "-layout", pdf_path, tmp_path],
            check=True, capture_output=True
        )
        with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def convert_pdf2txt(pdf_path: str) -> str:
    """Conversion avec pdf2txt.py (pdfminer.six)."""
    result = subprocess.run(
        ["pdf2txt.py", pdf_path],
        capture_output=True, text=True, errors="replace"
    )
    return result.stdout


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
