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
- `MixedAskOwlAPI` -- subclass of `AskOwlAPI` for MIXED ontologies; overrides `ngrams`, `children`, and `parents` to include `owl:NamedIndividual` leaves

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

## OWL Schema Detection

`OWLSchemaDetector` probes an rdflib `Graph` to identify which structural pattern an ontology uses. Detection is automatic and requires no consumer configuration.

| Schema | Detection criteria |
|---|---|
| `CLASS_BASED` | Only `owl:Class` entities connected via `rdfs:subClassOf` |
| `MIXED` | Both `owl:Class`/`rdfs:subClassOf` taxonomy and `owl:NamedIndividual` leaf entities |
| `INDIVIDUAL` | Only `owl:NamedIndividual` entities, no `rdfs:subClassOf` present |
| `SKOS` | Entities typed as `skos:Concept` (highest priority) |

Detection runs in priority order: SKOS > MIXED > INDIVIDUAL > CLASS_BASED.

`UniversalMDAGenerator` wraps both `MDAGenerator` and `MixedAskOwlAPI` behind a single interface. It calls `OWLSchemaDetector` internally and routes to the appropriate extraction strategy without any consumer input.

```python
from mutato.mda import UniversalMDAGenerator

d_owl = UniversalMDAGenerator(
    ontology_name="my_ontology",
    absolute_path="/path/to/owls",
    namespace="http://example.org/my_ontology#"
).generate()
```

The output dict is identical in shape to `MDAGenerator.generate()` for all schema patterns. `UniversalMDAGenerator` is the recommended entry point when the ontology structure is not known in advance.

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
| `SPAN_DISTANCE` | `4` | Maximum token distance between span anchor and trailing token in span matching |

SpaCy matching (`PerformSpacyMatching`) exists in the codebase but is not wired into the default pipeline.

---

## Tests

### AskOwlAPI / singlequery

| Test File | What It Covers |
|---|---|
| [tests/owl/test_ask_owl_api.py](../tests/owl/test_ask_owl_api.py) | `AskOwlAPI` -- labels, predicates, entities, taxonomy queries |
| [tests/owl/test_ask_json_api.py](../tests/owl/test_ask_json_api.py) | `AskJsonAPI` -- all view methods against a pre-generated JSON file |
| [tests/owl/parser/test_ask_owl_api_equivalents.py](../tests/owl/parser/test_ask_owl_api_equivalents.py) | `AskOwlAPI.equivalents()` -- no spaces in values |

### MutatoAPI with live OWL

| Test File | What It Covers |
|---|---|
| [tests/owl/parser/test_mutato_api_owl_basic_swap.py](../tests/owl/parser/test_mutato_api_owl_basic_swap.py) | `MutatoAPI` with `FindOntologyData` -- basic swap |
| [tests/owl/parser/test_mutato_api_owl_span_distance.py](../tests/owl/parser/test_mutato_api_owl_span_distance.py) | Span distance configuration via `SPAN_DISTANCE` env var |
| [tests/owl/parser/test_mutato_api_owl_multiword_span.py](../tests/owl/parser/test_mutato_api_owl_multiword_span.py) | Span matching -- multi-token entity detection |
| [tests/owl/parser/test_mutato_api_owl_span_preposition.py](../tests/owl/parser/test_mutato_api_owl_span_preposition.py) | Preposition stripping in multi-word span entities |
| [tests/owl/parser/test_mutato_api_owl_negation_span.py](../tests/owl/parser/test_mutato_api_owl_negation_span.py) | Negation span matching |
| [tests/owl/parser/test_mutato_api_owl_conjunction_span.py](../tests/owl/parser/test_mutato_api_owl_conjunction_span.py) | Connector words preserved in entity names |
| [tests/owl/parser/test_mutato_api_owl_edge_cases.py](../tests/owl/parser/test_mutato_api_owl_edge_cases.py) | Edge cases -- empty input, unknown tokens, partial matches |
| [tests/owl/parser/test_mutato_api_owl_medical_sentence.py](../tests/owl/parser/test_mutato_api_owl_medical_sentence.py) | Medical sentence parsing -- realistic clinical text |
| [tests/owl/parser/test_mutato_api_token_structure.py](../tests/owl/parser/test_mutato_api_token_structure.py) | Swap token structure -- required fields and types |
| [tests/owl/parser/test_mutato_api_roundtrip.py](../tests/owl/parser/test_mutato_api_roundtrip.py) | OWL-to-JSON roundtrip -- `MDAGenerator` then `FindOntologyJSON` |

### MutatoAPI with pre-computed JSON

| Test File | What It Covers |
|---|---|
| [tests/owl/parser/test_mutato_api_json_bnode.py](../tests/owl/parser/test_mutato_api_json_bnode.py) | bNode handling with `FindOntologyJSON` |
| [tests/owl/parser/test_mutato_api_json_punctuation.py](../tests/owl/parser/test_mutato_api_json_punctuation.py) | Punctuation normalization (`/`, `-`) in synonyms |
| [tests/owl/parser/test_mutato_api_json_by_predicate.py](../tests/owl/parser/test_mutato_api_json_by_predicate.py) | `by_predicate` filtering -- exclusion of `class` key and self-referential values |
| [tests/owl/parser/test_mutato_api_json_apostrophe.py](../tests/owl/parser/test_mutato_api_json_apostrophe.py) | Apostrophe normalization in synonym lookup |
| [tests/owl/parser/test_mutato_api_json_idempotency.py](../tests/owl/parser/test_mutato_api_json_idempotency.py) | Repeated calls with identical input always produce identical output |
| [tests/owl/parser/test_mutato_api_json_multi_entity.py](../tests/owl/parser/test_mutato_api_json_multi_entity.py) | Multiple entity matches in a single input |

### OWL Schema Detection and Universal Generator

| Test File | What It Covers |
|---|---|
| [tests/owl/schema/test_owl_schema_detector.py](../tests/owl/schema/test_owl_schema_detector.py) | `OWLSchemaDetector` -- correct detection across all four patterns, determinism, synthetic edge cases |
| [tests/owl/schema/test_universal_mda_generator.py](../tests/owl/schema/test_universal_mda_generator.py) | `UniversalMDAGenerator` -- output shape parity with `MDAGenerator` and structural validation for MIXED |

### Econ Skills -- MIXED ontology parsing quality

| Test File | What It Covers |
|---|---|
| [tests/owl/parser/test_econ_skills_basic.py](../tests/owl/parser/test_econ_skills_basic.py) | Direct skill detection from `econ-20160218.owl` -- exact match, case invariance, negative cases |
| [tests/owl/parser/test_econ_skills_spans.py](../tests/owl/parser/test_econ_skills_spans.py) | Span matching with interleaved filler words -- bigram anchor invariant, distance thresholds |
| [tests/owl/parser/test_econ_skills_sentences.py](../tests/owl/parser/test_econ_skills_sentences.py) | Realistic prose and resume-style sentences -- single and multiple skills per sentence |

### FindOntologyJSON / FindOntologyData

| Test File | What It Covers |
|---|---|
| [tests/owl/finder/test_find_ontology_json_hierarchy.py](../tests/owl/finder/test_find_ontology_json_hierarchy.py) | `FindOntologyJSON` hierarchy traversal |
| [tests/owl/finder/test_find_ontology_json_hierarchy_ops.py](../tests/owl/finder/test_find_ontology_json_hierarchy_ops.py) | `FindOntologyJSON` ancestors, descendants, has_ancestor |
| [tests/owl/finder/test_find_ontology_json_structure.py](../tests/owl/finder/test_find_ontology_json_structure.py) | `FindOntologyJSON` output structure and required key presence |
| [tests/owl/finder/test_find_ontology_json_canon_ops.py](../tests/owl/finder/test_find_ontology_json_canon_ops.py) | `FindOntologyJSON` canonical lookup operations |
| [tests/owl/finder/test_find_ontology_json_from_file.py](../tests/owl/finder/test_find_ontology_json_from_file.py) | `FindOntologyJSON` loaded from a persisted JSON file |
| [tests/owl/finder/test_find_ontology_data_api.py](../tests/owl/finder/test_find_ontology_data_api.py) | `FindOntologyData` (live OWL) integrated with `MutatoAPI` |
| [tests/owl/finder/test_find_ontology_data_exact_match.py](../tests/owl/finder/test_find_ontology_data_exact_match.py) | `FindOntologyData` exact match path |

### GeneratePlusSpans

| Test File | What It Covers |
|---|---|
| [tests/owl/finder/test_generate_plus_spans_single.py](../tests/owl/finder/test_generate_plus_spans_single.py) | `GeneratePlusSpans` -- single span rule expansion |
| [tests/owl/finder/test_generate_plus_spans_overlap.py](../tests/owl/finder/test_generate_plus_spans_overlap.py) | `GeneratePlusSpans` -- multiple anchor patterns |
| [tests/owl/finder/test_generate_plus_spans_complex.py](../tests/owl/finder/test_generate_plus_spans_complex.py) | `GeneratePlusSpans` -- overlapping span hierarchies |
