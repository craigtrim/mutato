# Architecture

## Overview

Mutato is a multi-pass synonym swapping pipeline built on top of OWL ontologies and spaCy. Given a list of tokens, it identifies spans that match ontology entities and replaces them with canonical forms, enriching each token with swap metadata.

The system is organized into four packages:

| Package | Role |
|---|---|
| `mutato.parser` | Entry point and matching orchestration |
| `mutato.finder` | Ontology loading and query layer |
| `mutato.mda` | Static ontology analysis and pre-computation |
| `mutato.core` | Shared utilities (file I/O, text, validation, timing) |

---

## Entry Point

```python
from mutato.parser import owl_parse

results = owl_parse(
    tokens=list[dict],       # tokenized input from LingPatLab
    ontology_name=str,       # name of the OWL ontology to load
    absolute_path=str        # directory containing the OWL file
)
```

`owl_parse` is a thin wrapper that constructs a `FindOntologyData` instance and hands it to `MutatoAPI`, then calls `swap_input_tokens`.

---

## Matching Pipeline

`MutatoAPI.swap_input_tokens` runs three matching passes in order. The full pipeline repeats up to two times (i.e., a second sweep after the first completes).

### Pass 1 -- Exact Matching

**Class**: `PerformExactMatching`

Tries n-gram sizes from 10 down to 1. For each size, it extracts candidate windows via `SlidingWindowExtract`, filters them through a runtime blacklist, then checks against the pre-built n-gram lookup table. On the first match, it creates a swap token, merges it into the token list, and restarts from size 10.

### Pass 2 -- Span Matching

**Class**: `PerformSpanMatching`

Applies only when the ontology defines span rules. `SpanMatchFinder` runs three checks in sequence:

1. `SpanContentCheck` -- token sequence matches rule pattern
2. `SpanDistanceCheck` -- matched tokens fall within a distance threshold
3. `SpanContextCheck` -- surrounding tokens support the match

When multiple rules match, the most specific one wins (the rule whose canonical name contains the most underscores). `SpanMatchSwapper` then applies the winning rule.

### Pass 3 -- Hierarchy Matching

**Class**: `PerformHierarchyMatching`

Tries n-gram sizes from 9 down to 2 (no unigrams). Candidate windows are filtered to those whose tokens carry ancestor or descendant metadata. `HierarchyMatchSwapper` attempts to locate a canonical match via the taxonomy graph. This pass loops internally until no further matches are found.

---

## Token Structures

### Input Token

Produced by LingPatLab before being passed to Mutato:

```python
{
    "id": int,
    "x": int,          # character start offset
    "y": int,          # character end offset
    "text": str,       # original surface form
    "normal": str,     # normalized (lowercase, alphanumeric)
    "lemma": str,
    "pos": str,
    "dep": str,
    "ent_type": str
}
```

### Swap Token

Produced by `SwapTokenGenerator` when a match is found. The matched span collapses into a single token:

```python
{
    "id": int,         # id of the first matched token
    "x": int,          # start of first matched token
    "y": int,          # end of last matched token
    "text": str,       # joined surface text of matched span
    "normal": str,     # canonical entity name
    "ner": str | None,
    "swaps": {
        "tokens": list[dict],   # original tokens that were replaced
        "canon": str,           # canonical entity name
        "type": str,            # "exact" | "span" | "hierarchy"
        "ontologies": list[str],
        "confidence": float     # 100.0
    }
}
```

---

## Finder Layer

The finder layer handles all ontology I/O and is split into two sub-packages.

### singlequery

Operates on a single OWL file.

- `OwlGraphConnector` -- loads the OWL/Turtle file into an RDFLib `Graph`
- `AskOwlAPI` -- wraps the graph with a SPARQL query interface; all results are lazy and cached via `@lru_cache`

The core query pattern:

```sparql
SELECT ?a ?b WHERE { ?a <predicate> ?b }
```

`AskOwlAPI` exposes derived views built from these raw triples:

| Method | Description |
|---|---|
| `synonyms()` / `synonyms_rev()` | Forward and reverse synonym indexes |
| `spans()` | Long-range matching patterns |
| `trie()` | Hierarchical token structure |
| `parents()` / `children()` | Direct taxonomy relationships |
| `ancestors()` / `descendants()` | Transitive taxonomy traversal |
| `equivalents()` | `owl:equivalentClass` mappings |

### multiquery

Operates across one or more OWL files simultaneously.

- `FindOntologyData` -- facade over a list of `AskOwlAPI` instances; merges results and re-exposes the same interface
- `FindOntologyJSON` -- same interface but reads from a pre-loaded JSON dict instead of OWL files

`FindOntologyData` also builds the n-gram lookup table (`ViewGeneratorLookup`) used by the exact matching pass:

```python
d_lookup = {
    1: ["nursing", "care", "medication"],
    2: ["nursing care", "medication administration"],
    ...
    10: [...]
}
```

---

## Ontology File Conventions

OWL files are expected in Turtle format. A typical entity definition:

```turtle
:nursing_care rdf:type owl:Class ;
    rdfs:label "Nursing Care" ;
    rdfs:seeAlso "nursing", "patient_care" ;
    skos:altLabel "care delivery" ;
    :inflection "caring for patients" ;
    rdfs:subClassOf :assessment ;
    owl:equivalentClass :nurse_intervention ;
    rdfs:implies :patient_safety ;
    rdfs:requires :clinical_knowledge .
```

Mutato reads labels, altLabels, seeAlso, and inflection entries as synonym sources. The `subClassOf` chain forms the taxonomy used in hierarchy matching.

---

## MDA Generator

`MDAGenerator` pre-computes a static snapshot of an ontology into a JSON-serializable dict. It is useful for cache warming, offline analysis, and loading ontologies without incurring RDF parse overhead at runtime.

Output structure:

```python
{
    "synonyms": {"fwd": {...}, "rev": {...}, "lookup": {...}},
    "children": {entity: [children]},
    "parents": {entity: [parents]},
    "spans": {span_name: {...}},
    "trie": {...},
    "labels": {entity: label_str},
    "equivalents": {entity: [...]},
    "ner": {entity: "NER"},
    "by_predicate": {predicate: {subject: [objects]}}
}
```

---

## Design Patterns

| Pattern | Where Used |
|---|---|
| Facade | `FindOntologyData` over multiple `AskOwlAPI` instances; `MutatoAPI` over matching services |
| Strategy | Four independent matching passes with a common `process(tokens) -> list` interface |
| Builder | `SwapTokenGenerator` constructs swap token DTOs from raw components |
| Lazy + Cache | `@lru_cache` on all `AskOwlAPI` and `FindOntologyData` query methods |
| Pipeline | `MutatoAPI` chains passes sequentially; each pass receives the previous output |
| Dependency Injection | All service classes receive dependencies via constructor |

---

## Caching

All ontology queries are cached at the `AskOwlAPI` level using `@lru_cache(maxsize=512)`. `FindOntologyData` adds a second caching layer for merged multi-ontology results. The matching passes themselves are not cached because token lists mutate between iterations.

---

## Configuration

| Environment Variable | Default | Effect |
|---|---|---|
| `SLIDING_WINDOW_BLACKLIST` | `False` | Enable blacklist filtering in exact matching |

SpaCy matching (`PerformSpacyMatching`) exists in the codebase but is not wired into the default pipeline.

---

## Tests

| Test File | What It Covers |
|---|---|
| [tests/owl/test_ask_owl_api.py](../tests/owl/test_ask_owl_api.py) | `AskOwlAPI` -- labels, predicates, entities, taxonomy queries |
| [tests/owl/parser/test_mutato_api_01.py](../tests/owl/parser/test_mutato_api_01.py) | `MutatoAPI` with `FindOntologyData` -- basic swap |
| [tests/owl/parser/test_mutato_api_02.py](../tests/owl/parser/test_mutato_api_02.py) | Span distance configuration via `SPAN_DISTANCE` env var |
| [tests/owl/parser/test_mutato_api_03.py](../tests/owl/parser/test_mutato_api_03.py) | Span matching -- multi-token entity detection |
| [tests/owl/parser/test_mutato_api_04.py](../tests/owl/parser/test_mutato_api_04.py) | Pre-loaded spaCy model injection |
| [tests/owl/parser/test_mutato_api_05.py](../tests/owl/parser/test_mutato_api_05.py) | Bigram span matching and distance thresholds |
| [tests/owl/parser/test_mutato_api_06.py](../tests/owl/parser/test_mutato_api_06.py) | `MutatoAPI` with pre-computed `FindOntologyJSON` |
| [tests/owl/parser/test_mutato_api_07.py](../tests/owl/parser/test_mutato_api_07.py) | bNode handling with `FindOntologyJSON` |
| [tests/owl/parser/test_mutato_api_08.py](../tests/owl/parser/test_mutato_api_08.py) | Punctuation normalization (`/`, `-`) in synonyms |
| [tests/owl/parser/test_mutato_api_09.py](../tests/owl/parser/test_mutato_api_09.py) | `by_predicate` filtering -- exclusion of `class` key and self-referential values |
| [tests/owl/parser/test_mutato_api_10.py](../tests/owl/parser/test_mutato_api_10.py) | `AskOwlAPI.equivalents()` -- no spaces in values |
| [tests/owl/parser/test_mutato_api_11.py](../tests/owl/parser/test_mutato_api_11.py) | Connector words preserved in entity names |
| [tests/owl/parser/test_mutato_api_12.py](../tests/owl/parser/test_mutato_api_12.py) | Preposition stripping in multi-word entities |
| [tests/owl/finder/test_generate_plus_spans_1.py](../tests/owl/finder/test_generate_plus_spans_1.py) | `GeneratePlusSpans` -- single span rule expansion |
| [tests/owl/finder/test_generate_plus_spans_2.py](../tests/owl/finder/test_generate_plus_spans_2.py) | `GeneratePlusSpans` -- multiple anchor patterns |
| [tests/owl/finder/test_generate_plus_spans_3.py](../tests/owl/finder/test_generate_plus_spans_3.py) | `GeneratePlusSpans` -- overlapping span hierarchies |
| [tests/owl/finder/test_find_ontology_json_03.py](../tests/owl/finder/test_find_ontology_json_03.py) | `FindOntologyData` (live OWL) integrated with `MutatoAPI` |
