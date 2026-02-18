# mutato

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org)
[![Version](https://img.shields.io/badge/version-0.5.22-informational)](https://github.com/Maryville-University-DLX/transcriptiq)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Monthly Downloads](https://img.shields.io/pypi/dm/mutato)](https://pypi.org/project/mutato/)
[![Total Downloads](https://static.pepy.tech/badge/mutato)](https://pepy.tech/project/mutato)
[![Tests](https://img.shields.io/badge/tests-961-brightgreen)](tests/)

Ontology-driven synonym swapping for semantic text enrichment. Mutato identifies terms in input text and replaces them with semantically equivalent synonyms sourced from OWL ontologies, enabling consistent, structured analysis of natural language content.

## Use Cases

- Normalize terminology across transcripts before downstream analysis
- Enrich tokens with ontology-backed synonym candidates
- Bridge informal language to structured vocabulary in NLP pipelines

## Quick Start

```python
from mutato.parser import owl_parse

results = owl_parse(tokens=["student", "learned", "math"], ontologies=[...])
```

## Installation

```bash
make all
```

This downloads the spaCy model, installs dependencies, runs tests, builds the package, and freezes requirements.

Or step by step:

```bash
make get_model   # download en_core_web_sm
make install     # poetry lock + install
make test        # run pytest
make build       # install + test + poetry build
make freeze      # export requirements.txt
```

## CLI

The `parse` command parses input text against an OWL ontology and prints canonical forms:

```bash
poetry run parse --ontology path/to/ontology.owl --input-text "fiscal policy analysis"
```

Three modes are available:

| Mode | Flag | Effect |
|---|---|---|
| Cached (default) | none | Load JSON snapshot; build it on first run |
| Rebuild cache | `--force-cache` | Regenerate snapshot, then parse |
| Live OWL | `--live` | Parse directly from the OWL file; no cache |

See [docs/cli.md](docs/cli.md) for the full reference, including the MIXED-schema caveat for `--live`.

## Architecture

Mutato is organized into four modules:

| Module | Purpose |
|---|---|
| `mutato.parser` | Main API -- synonym swapping and token matching |
| `mutato.finder` | Ontology lookup across single and multiple OWL graphs |
| `mutato.mda` | Metadata and NER enrichment generation |
| `mutato.core` | Shared utilities (file I/O, text, validation, timing) |

See [docs/architecture.md](docs/architecture.md) for design details.

## Matching Strategies

The parser applies multiple matching passes in order:

1. **Exact** -- literal string match against ontology terms
2. **Span** -- multi-token window matching
3. **Hierarchy** -- parent/child concept traversal
4. **spaCy** -- lemma and POS-aware NLP matching

## Requirements

- Python >= 3.10, < 3.14
- [Poetry](https://python-poetry.org) for dependency management
- spaCy `en_core_web_sm` model (installed via `make get_model`)

## Links

- [Issue Tracker](https://github.com/Maryville-University-DLX/transcriptiq/issues)
- [Source](https://github.com/Maryville-University-DLX/transcriptiq/libs/core/mutato-core)
