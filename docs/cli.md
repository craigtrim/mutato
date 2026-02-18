# CLI Reference

## Overview

The `parse` command tokenizes input text against an OWL ontology and returns the input with matched entity spans replaced by their canonical forms.

```bash
poetry run parse --ontology path/to/ontology.owl --input-text "some text to parse"
```

---

## Flags

| Flag | Required | Description |
|---|---|---|
| `--ontology PATH` | yes | Path to the `.owl` file |
| `--input-text TEXT` | yes | Input text to parse |
| `--namespace URI` | no | RDF namespace URI (auto-derived from the ontology name if omitted) |
| `--force-cache` | no | Rebuild the JSON cache, then parse via the refreshed snapshot |
| `--live` | no | Parse directly from the OWL file; no cache interaction |

`--force-cache` and `--live` are mutually exclusive.

---

## Execution Modes

### Default (cached path)

On first run the OWL file is parsed once, all views are computed, and the result is written to a JSON snapshot at `~/.cache/mutato/<stem>.json`. Subsequent runs load the snapshot directly, skipping all RDF and SPARQL work.

```bash
poetry run parse --ontology econ.owl --input-text "fiscal policy analysis"
# First run: builds and writes cache
# Subsequent runs: loads cache
```

This is the recommended path for repeated use.

### --force-cache

Discards any existing snapshot and rebuilds it from the OWL file before parsing. Use this whenever the ontology changes and the cached snapshot needs to be refreshed.

```bash
poetry run parse --ontology econ.owl --input-text "fiscal policy analysis" --force-cache
```

Equivalent to deleting `~/.cache/mutato/econ.json` and running the default path.

### --live

Parses directly from the OWL file on every run. No snapshot is read or written. The full RDF graph is loaded and SPARQL views are built from scratch each time.

```bash
poetry run parse --ontology econ.owl --input-text "fiscal policy analysis" --live
```

Useful when iterating on an ontology before committing a cache rebuild. Slower at startup.

---

## The MIXED Schema Caveat

When `--live` is used, the CLI loads the ontology via `FindOntologyData`, which uses plain `AskOwlAPI` under the hood. `AskOwlAPI` traverses `owl:Class` entities connected by `rdfs:subClassOf` but does not traverse `owl:NamedIndividual` leaf entities.

MIXED ontologies (such as `econ.owl`) encode their leaf concepts as `owl:NamedIndividual` with polyhierarchy via `rdf:type`. These entities are invisible to the `--live` path.

The CLI detects this condition automatically and emits a `WARNING`:

```
econ.owl uses schema MIXED (owl:NamedIndividual leaf entities).
The --live path uses AskOwlAPI, which does not traverse individual leaves;
entity coverage will be lower than the cached path. Run without --live
(or with --force-cache after editing the ontology) for full results.
```

The parse still runs; it will match any class-level entities that exist. For full coverage, use the default cached path or `--force-cache`.

See [architecture.md](architecture.md) for a description of the MIXED schema pattern and `OWLSchemaDetector`.

---

## Cache Location

Snapshots are stored at:

```
~/.cache/mutato/<ontology-stem>.json
```

For example, `econ.owl` caches to `~/.cache/mutato/econ.json`.

The cache is keyed by the OWL filename stem. If two different ontologies share a filename (in different directories), they will collide. Rename one or manage the cache manually.

---

## Trade-offs

| Mode | Startup | Coverage | Cache interaction |
|---|---|---|---|
| Default (cached) | Fast (JSON load) | Full | Reads snapshot; writes on first run |
| `--force-cache` | Slow (OWL parse) | Full | Rebuilds and writes snapshot |
| `--live` | Slow (OWL parse) | Reduced for MIXED | None |

---

## Examples

Parse a single phrase (cached):

```bash
poetry run parse \
  --ontology /path/to/econ.owl \
  --input-text "labor market analysis trends"
```

Force a cache rebuild after editing the ontology:

```bash
poetry run parse \
  --ontology /path/to/econ.owl \
  --input-text "fiscal policy analysis" \
  --force-cache
```

Iterate on an ontology without touching the cache:

```bash
poetry run parse \
  --ontology /path/to/econ.owl \
  --input-text "fiscal policy analysis" \
  --live
```

Pass an explicit namespace (needed for some ontologies on `--live`):

```bash
poetry run parse \
  --ontology /path/to/my_ontology.owl \
  --input-text "some text" \
  --namespace "http://example.org/my_ontology#" \
  --live
```
