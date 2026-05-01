"""
Taxonomie des sections d'un article scientifique.

Centralise les mots-clés et exclusions utilisés par le détecteur de sections.
Modifier ce fichier suffit pour étendre ou adapter la classification (OCP).
"""

# Mots-clés associés à chaque section canonique
MOTS_CLES: dict[str, list[str]] = {
    "abstract": [
        "abstract", "résumé", "summary",
    ],
    "introduction": [
        "introduction",
    ],
    "corps": [
        "method", "méthode", "approach", "approche", "background",
        "related work", "related works", "travaux connexes",
        "système", "system", "model", "modèle", "architecture",
        "framework", "formulation", "methodology", "méthodologie",
        "state of the art", "industrial context",
        "single-document summarization", "multi-document summarization",
        "sentence boundary detection", "rst spanish treebank",
        "resources and statistics", "word representations",
    ],
    "conclusion": [
        "conclusion", "conclusions", "future work",
        "conclusion and future", "conclusion and perspectives",
        "discussion and future",
    ],
    "discussion": [
        "discussion", "analyse", "analysis",
    ],
    "bibliographie": [
        "reference", "references", "bibliograph", "bibliography",
    ],
}

# Sous-sections à ignorer (classées dans "corps" mais non promues en section)
SOUS_SECTIONS_CORPS: list[str] = [
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

# Ordre canonique des sections dans la sortie
SECTIONS_ORDRE: list[str] = [
    "titre",
    "auteurs",
    "abstract",
    "introduction",
    "corps",
    "conclusion",
    "discussion",
    "bibliographie",
]
