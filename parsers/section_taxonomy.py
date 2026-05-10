"""Taxonomie centralisée des sections d'un article scientifique."""

MOTS_CLES: dict[str, list[str]] = {
    "abstract": ["abstract", "résumé", "resume", "summary"],
    "introduction": ["introduction", "introductory remarks"],
    "corps": [
        "method", "methods", "méthode", "approach", "approche", "background",
        "related work", "related works", "previous work", "travaux connexes",
        "système", "system", "model", "models", "modèle", "architecture",
        "framework", "formulation", "methodology", "méthodologie",
        "state of the art", "industrial context", "experiments", "experiment",
        "experimental setup", "evaluation", "results", "implementation",
        "data", "dataset", "corpus", "resources", "discussion and results",
        "single-document summarization", "multi-document summarization",
        "sentence boundary detection", "rst spanish treebank",
        "resources and statistics", "word representations",
    ],
    "conclusion": [
        "conclusion", "conclusions", "concluding remarks", "final remarks",
        "future work", "conclusion and future", "conclusions and future",
        "conclusion and perspectives", "discussion and future",
    ],
    "discussion": ["discussion", "general discussion", "analysis", "analyse"],
    "bibliographie": [
        "reference", "references", "bibliograph", "bibliography", "works cited",
        "literature cited", "références", "references bibliographiques",
    ],
}

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

SECTIONS_ORDRE: list[str] = [
    "titre", "auteurs", "emails", "affiliations", "abstract", "introduction",
    "corps", "conclusion", "discussion", "bibliographie",
]
