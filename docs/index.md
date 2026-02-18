# mutato

OWL ontology-backed synonym swapping for NLP pipelines.

Mutato identifies terms in input text and replaces them with semantically equivalent synonyms sourced from OWL ontologies, enabling consistent, structured analysis of natural language content.

## Quick Start

```python
from mutato.parser import owl_parse

results = owl_parse(tokens=["student", "learned", "math"], ontologies=[...])
```

## Matching Strategies

The parser applies multiple matching passes in order:

1. **Exact** — literal string match against ontology terms
2. **Span** — multi-token window matching
3. **Hierarchy** — parent/child concept traversal
4. **spaCy** — lemma and POS-aware NLP matching

## Installation

```bash
make all
```

This downloads the spaCy model, installs dependencies, runs tests, builds the package, and freezes requirements.

## Use Cases

- Normalize terminology across transcripts before downstream analysis
- Enrich tokens with ontology-backed synonym candidates
- Bridge informal language to structured vocabulary in NLP pipelines

## Requirements

- Python >= 3.10, < 3.14
- [Poetry](https://python-poetry.org) for dependency management
- spaCy `en_core_web_sm` model (installed via `make get_model`)
