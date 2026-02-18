# MDA Pre-Computation

## The Problem

The default runtime path loads an OWL file cold on every process start. RDFLib parses the Turtle graph, SPARQL views are computed lazily, and synonym/n-gram indexes are built on first access. For large ontologies this adds meaningful latency before the first `owl_parse` call can execute.

## The Solution

`MDAGenerator` walks the ontology once and emits a plain Python dict containing every derived view the matching pipeline needs. Serialize that dict to JSON, commit it alongside your OWL file, and load it at runtime via `FindOntologyJSON` instead of `FindOntologyData`. The RDF layer is never touched again.

---

## Step 1 -- Generate the Static File

Run this once whenever the OWL file changes:

```python
import json
from mutato.mda import MDAGenerator

gen = MDAGenerator(
    ontology_name="my_ontology",
    absolute_path="/path/to/owl/files",
    namespace="http://example.org/my_ontology#"
)

d_mda = gen.generate()

with open("/path/to/owl/files/my_ontology.json", "w") as f:
    json.dump(d_mda, f, indent=2)
```

`generate()` computes and returns:

| Key | Contents |
|---|---|
| `synonyms.fwd` | Canonical entity name to list of surface variants |
| `synonyms.rev` | Surface variant to list of canonical names |
| `synonyms.lookup` | N-gram size to list of n-gram strings (the matching index) |
| `ngrams` | N-gram lists by gram level 1-9 |
| `parents` / `children` | Direct taxonomy edges |
| `trie` | Hierarchical token tree |
| `spans` | Long-range matching rules |
| `labels` | Entity name to display label |
| `equivalents` | `owl:equivalentClass` mappings |
| `ner` | Entity name to NER label (hardcoded `"NER"`) |
| `by_predicate` | Raw triples keyed by predicate, then subject |
| `predicates` | List of all predicate names found in the ontology |

Predicates `rdfs:comment` and `nil` are excluded from `by_predicate` as they add no value to the NLP stage.

---

## Step 2 -- Load at Runtime

Replace `FindOntologyData` with `FindOntologyJSON`:

```python
import json
from mutato.finder.multiquery.bp import FindOntologyJSON
from mutato.parser.bp import MutatoAPI

with open("/path/to/owl/files/my_ontology.json") as f:
    d_owl = json.load(f)

finder = FindOntologyJSON(
    d_owl=d_owl,
    ontology_name="my_ontology"
)

api = MutatoAPI(finder=finder)
results = api.swap_input_tokens(tokens)
```

`FindOntologyJSON` satisfies the same interface as `FindOntologyData` so nothing else in the pipeline changes.

---

## Step 3 -- Keep the JSON in Sync

The static file is a snapshot. It goes stale whenever the OWL file is edited. A simple rule: regenerate on every ontology change before committing.

You can wire this into your build with a dedicated Makefile target:

```makefile
.PHONY: mda

mda:
	poetry run python -c "\
	import json; \
	from mutato.mda import MDAGenerator; \
	d = MDAGenerator('my_ontology', './resources/ontologies', 'http://example.org/my_ontology#').generate(); \
	json.dump(d, open('./resources/ontologies/my_ontology.json', 'w'), indent=2)"
```

Then incorporate it into your workflow:

```makefile
build: install test mda
	poetry build
```

---

## What Gets Skipped

`FindOntologyJSON` does not use RDFLib at all. The following are bypassed entirely at runtime:

- OWL file discovery and parsing (`OwlGraphConnector`)
- SPARQL query execution (`AskOwlAPI`)
- Lazy view generation (`ViewGeneratorLookup`, `GenerateViewSpans`, `GenerateViewTrie`, etc.)
- `@lru_cache` warming on first access

All of that work was already done at generation time.

---

## Trade-offs

| Factor | FindOntologyData (live OWL) | FindOntologyJSON (pre-computed) |
|---|---|---|
| Startup cost | High (RDF parse + view build) | Low (JSON load only) |
| Ontology changes | Instant (re-parse on restart) | Requires regeneration |
| Memory | Lazy (views built on demand) | Eager (full dict in memory) |
| SPARQL flexibility | Full query access | Views are fixed at generation time |
| Suitable for | Development, iteration | Production, deployed services |

---

## Multi-Ontology Support

`FindOntologyJSON` wraps a single dict. If your pipeline loads multiple ontologies via `FindOntologyData`, generate a JSON file per ontology and load each independently:

```python
finders = []
for name in ["ontology_a", "ontology_b"]:
    with open(f"/path/to/{name}.json") as f:
        finders.append(FindOntologyJSON(d_owl=json.load(f), ontology_name=name))

# Use the first finder or compose results as needed
```

For true multi-ontology merging at the `FindOntologyData` level, the live OWL path is currently the supported route. JSON-backed multi-ontology merging would require a custom facade combining multiple `FindOntologyJSON` instances.

---

## Tests

| Test File | What It Covers |
|---|---|
| [tests/owl/test_ask_json_api.py](../tests/owl/test_ask_json_api.py) | `AskJsonAPI` -- all view methods against a pre-generated JSON file |
| [tests/owl/finder/test_mda_generator_medicopilot.py](../tests/owl/finder/test_mda_generator_medicopilot.py) | `MDAGenerator.generate()` output keys and JSON serialization |
| [tests/owl/finder/test_mda_generator_courses.py](../tests/owl/finder/test_mda_generator_courses.py) | `MDAGenerator.generate()` against a courses ontology |
| [tests/owl/finder/test_find_ontology_json_01.py](../tests/owl/finder/test_find_ontology_json_01.py) | `FindOntologyJSON` full API surface -- predicates, labels, taxonomy |
| [tests/owl/finder/test_find_ontology_json_02.py](../tests/owl/finder/test_find_ontology_json_02.py) | `FindOntologyJSON` + `MutatoAPI` end-to-end swap via pre-computed JSON |
