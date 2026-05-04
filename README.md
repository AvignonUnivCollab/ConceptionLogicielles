# Parseur d'articles scientifiques (Projet Scrum - Sprint 1, 2 & 3)

## Description

Ce projet consiste en un analyseur (parseur) d'articles scientifiques au format PDF. Il convertit un article PDF en un fichier texte structuré (`.txt`) et/ou XML (`.xml`) selon les sections canoniques (Titre, Auteurs, Emails, Abstract, Introduction, Corps, Conclusion, Discussion, Bibliographie).

## Architecture

```
main.py                        ← point d'entrée CLI (-t / -x / les deux)
batch_processor.py             ← orchestration par lot d'un dossier PDF

converters/
  pdf_converter.py             ← interface PdfConverter + ConverterFactory
  benchmark.py                 ← comparaison des deux outils

parsers/
  article_parser.py            ← parsing en 3 passes (titre, auteurs, sections)
  email_extractor.py           ← extraction des emails (module dédié Sprint 3)
  section_detector.py          ← détection des titres de section
  section_taxonomy.py          ← mots-clés par section (OCP — seul fichier à modifier)
  text_cleaner.py              ← nettoyage du texte brut

formatters/
  article_formatter.py         ← interface ArticleFormatter + Sprint2Formatter (.txt)
  xml_formatter.py             ← XmlFormatter (.xml) — Sprint 3

utils/
  banner.py                    ← bannière CLI
  colors.py                    ← constantes couleurs ANSI
```

## Architecture / Choix techniques du Sprint 1

L'objectif du Sprint 1 était d'évaluer deux extracteurs de texte, `pdftotext` et `pdf2txt.py`, pour déterminer lequel produisait la meilleure base pour notre parseur. L'évaluation a porté sur :

- Le respect des frontières de phrases et des doubles colonnes.
- La bonne séparation des mots (détection de mots "collés").
- La conservation de la hiérarchie pour extraire les sections.

**Verdict** : `pdftotext` (utilisé avec le paramètre `-layout`) est l'outil retenu. Il préserve la structure du document original et produit significativement moins de problèmes de "mots collés" par rapport à `pdf2txt.py`.

## Nouveautés du Sprint 2

### Corrections

- **Fix bug `break` (passe 1)** : La boucle de détection du titre s'arrêtait à la première ligne non vide, même si ce n'était pas un titre valide. Corrigé en déplaçant le `break` à l'intérieur du `if`.
- **Optimisation passe 2** : La passe de détection des sections démarre maintenant après le titre (`idx_fin_titre`).

### Nouvelles fonctionnalités

- **Détection des auteurs (passe 1.5)** : Extraction des auteurs depuis les lignes situées entre le titre et l'abstract.
- **Format de sortie Sprint 2** :
  ```
  Fichier : article.pdf
  Titre : Titre de l'article
  Auteurs : Prénom Nom, Prénom Nom
  Resume : Texte de l'abstract sur une seule ligne...
  ```

## Nouveautés du Sprint 3

### Corrections

- **Fix `detecter_section`** : Le pattern de détection exige désormais une majuscule en début de ligne, évitant de classer à tort une continuation de titre comme section.
- **Fix écrasement des emails** : La section `emails` est protégée de l'écrasement par la passe 2.

### Nouvelles fonctionnalités

- **Module `email_extractor.py`** : Module dédié à l'extraction des emails, supportant les formats :
  - Simple : `alice@labo.fr`
  - Virgule/parenthèse finale : `alice@labo.fr,` / `(alice@labo.fr).`
  - Email coupé sur deux lignes (PDF) : `torres@univ-` + `avignon.fr`
  - Groupé avec accolades : `{alice, bob}@labo.fr`
  - Groupé avec parenthèses : `(alice,bob)@lif.univ-mrs.fr`
  - Notes de bas de page IEEE

- **`XmlFormatter`** : Nouvelle sortie XML UTF-8 avec la structure :
  ```xml
  <article>
    <preamble>article.pdf</preamble>
    <titre>Titre de l'article</titre>
    <auteurs>
      <auteur>
        <name>Prénom Nom</name>
        <mail>alice@labo.fr</mail>
      </auteur>
    </auteurs>
    <abstract>Résumé...</abstract>
    <biblio>Références bibliographiques...</biblio>
  </article>
  ```

- **Arguments `-t` / `-x`** : Choix du format de sortie au lancement. Les deux peuvent être combinés.

- **Format de sortie `.txt` mis à jour** :
  ```
  Fichier : article.pdf
  Titre : Titre de l'article
  Auteurs : Prénom Nom, Prénom Nom
  Emails : alice@labo.fr ; bob@labo.fr
  Resume : Texte de l'abstract sur une seule ligne...
  ```

## Comment exécuter le programme

**Prérequis** : Python 3 et `pdftotext` (poppler-utils) accessible dans le PATH.

```bash
# Sortie texte .txt uniquement (défaut si aucun argument)
python main.py <dossier> -t

# Sortie XML .xml uniquement
python main.py <dossier> -x

# Les deux formats simultanément
python main.py <dossier> -t -x

# Choisir l'outil de conversion
python main.py <dossier> -t --outil pdf2txt
```

Les fichiers générés sont placés dans `<dossier>/output/`.
