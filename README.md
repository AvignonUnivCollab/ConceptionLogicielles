# Parseur d'articles scientifiques (Projet Scrum - Sprint 1 & 2)

## Description

Ce projet consiste en un analyseur (parseur) d'articles scientifiques au format PDF. Il convertit un article PDF en un fichier texte brut structuré selon les sections canoniques (Titre, Auteurs, Abstract, Introduction, Corps, Conclusion, Discussion, Bibliographie).

## Architecture / Choix techniques du Sprint 1

L'objectif du Sprint 1 était d'évaluer deux extracteurs de texte, `pdftotext` et `pdf2txt.py`, pour déterminer lequel produisait la meilleure base pour notre parseur. L'évaluation a porté sur :

- Le respect des frontières de phrases et des doubles colonnes.
- La bonne séparation des mots (détection de mots "collés").
- La conservation de la hiérarchie pour extraire les sections.

**Verdict** : `pdftotext` (utilisé avec le paramètre `-layout`) est l'outil retenu. Il a montré de meilleurs résultats qualitatifs, car il préserve de manière optimale la structure du document original (les colonnes sont bien réparties, évitant l'entremêlement des phrases) et produit significativement moins de problèmes de "mots collés" par rapport à `pdf2txt.py`.

## Nouveautés du Sprint 2

### Corrections

- **Fix bug `break` (passe 1)** : La boucle de détection du titre s'arrêtait à la première ligne non vide, même si ce n'était pas un titre valide. Corrigé en déplaçant le `break` à l'intérieur du `if`.
- **Optimisation passe 2** : La passe de détection des sections démarre maintenant après le titre (`idx_fin_titre`) pour éviter de re-parcourir les premières lignes inutilement.

### Nouvelles fonctionnalités

- **Détection des auteurs (passe 1.5)** : Extraction des auteurs depuis les lignes situées entre le titre et l'abstract. L'heuristique filtre les affiliations (université, département, adresses email) et retient les lignes de noms propres capitalisés séparés par virgules, `and` ou points médians.
- **Format de sortie Sprint 2** : Chaque fichier de sortie commence maintenant par 4 lignes normalisées (une par champ) :
  ```
  Fichier : article.pdf
  Titre : Titre de l'article
  Auteurs : Prénom Nom, Prénom Nom
  Resume : Texte de l'abstract sur une seule ligne...
  ```
  Suivi du format détaillé complet (toutes les sections indentées).

## Comment exécuter le programme

1. **Prérequis** : Avoir Python 3 installé et la commande `pdftotext` (issue de _poppler-utils_) accessible dans votre système. La commande `pdf2txt.py` (issue de _pdfminer.six_) est également recommandée.

2. **Exécuter le script sur un fichier PDF** :

   ```bash
   python main.py fichier.pdf
   ```

   Cela va générer le fichier texte dans le même dossier (par exemple, `fichier_parse.txt`).

3. **Options disponibles** :
   - `--outil [pdftotext|pdf2txt]` : Forcer l'outil de conversion (défaut : `pdftotext`).
   - `--comparer` : Lancer l'analyse comparative entre les deux outils.
   - `--stats` : Afficher les statistiques de l'extraction.
   - `-o fichier.txt` : Définir manuellement le nom du fichier de sortie.
