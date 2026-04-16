# Parseur d'articles scientifiques (Projet Scrum - Sprint 1)

## Description

Ce projet consiste en un analyseur (parseur) d'articles scientifiques au format PDF. Il convertit un article PDF en un fichier texte brut structuré selon les sections canoniques (Titre, Auteurs, Abstract, Introduction, Corps, Conclusion, Discussion, Bibliographie).

## Architecture / Choix techniques du Sprint 1

L'objectif du Sprint 1 était d'évaluer deux extracteurs de texte, `pdftotext` et `pdf2txt.py`, pour déterminer lequel produisait la meilleure base pour notre parseur. L'évaluation a porté sur :

- Le respect des frontières de phrases et des doubles colonnes.
- La bonne séparation des mots (détection de mots "collés").
- La conservation de la hiérarchie pour extraire les sections.

**Verdict** : `pdftotext` (utilisé avec le paramètre `-layout`) est l'outil retenu. Il a montré de meilleurs résultats qualitatifs, car il préserve de manière optimale la structure du document original (les colonnes sont bien réparties, évitant l'entremêlement des phrases) et produit significativement moins de problèmes de "mots collés" par rapport à `pdf2txt.py`.

## Comment exécuter le programme

1. **Prérequis** : Avoir Python 3 installé et la commande `pdftotext` (issue de _poppler-utils_) accessible dans votre système. La commande `pdf2txt.py` (issue de _pdfminer.six_) est également recommandée.
2. **Exécuter le script sur un fichier PDF** :

   ```bash
   python main.py fichier.pdf
   ```

   Cela va générer le fichier texte dans le même dossier (par exemple, `fichier_parse.txt`).

3. **Options disponibles** :
   - `--outil [pdftotext|pdf2txt]` : Forcer le programme à utiliser un outil spécifique pour la conversion.
   - `--comparer` : Lancer l'analyse comparative de qualité (Sprint 1) entre les deux outils sur le document.
   - `--stats` : Afficher les statistiques de l'extraction (quelles sections ont été trouvées ou manquent).
   - `-o fichier.txt` : Définir manuellement le nom du fichier de sortie.
