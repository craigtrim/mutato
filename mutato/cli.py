#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Mutato CLI: parse input text against an OWL ontology."""

import json
import logging
import sys
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
_log = logging.getLogger(__name__)

_CACHE_ROOT = Path.home() / '.cache' / 'mutato'


def _cache_path(ontology_path: Path) -> Path:
    _CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return _CACHE_ROOT / f'{ontology_path.stem}.json'


def _reconstruct(tokens: list, fallback: str) -> str:
    parts = [
        t['swaps']['canon'] if t.get('swaps') else t['text'].strip()
        for t in tokens
        if t.get('swaps') or t['text'].strip()
    ]
    return ' '.join(parts) if parts else fallback


def _warn_if_mixed(ontology_path: Path) -> None:
    """Emit a WARNING if the ontology uses the MIXED schema.

    The --live path uses plain AskOwlAPI, which does not traverse
    owl:NamedIndividual leaves present in MIXED ontologies.  Entity
    coverage will therefore be lower than the JSON-cached path for
    such ontologies.
    """
    try:
        from rdflib import Graph
        from mutato.mda.owl_schema_detector import OWLSchemaDetector
        from mutato.mda.owl_schema import OWLSchema

        g = Graph()
        g.parse(str(ontology_path), format='turtle')
        schema = OWLSchemaDetector(g).detect()

        if schema == OWLSchema.MIXED:
            _log.warning(
                '%s uses schema MIXED (owl:NamedIndividual leaf entities). '
                'The --live path uses AskOwlAPI, which does not traverse '
                'individual leaves; entity coverage will be lower than the '
                'cached path. Run without --live (or with --force-cache after '
                'editing the ontology) for full results.',
                ontology_path.name,
            )
    except Exception as exc:
        _log.debug('Schema detection skipped: %s', exc)


def _parse_live(ontology_path: Path, input_text: str) -> str:
    from mutato.finder.multiquery.bp import FindOntologyData
    from mutato.parser import MutatoAPI

    _warn_if_mixed(ontology_path)
    _log.info('Parsing via live OWL -- no JSON cache')

    finder = FindOntologyData(
        ontologies=[ontology_path.stem],
        absolute_path=str(ontology_path.parent),
        namespace=None,
    )
    api = MutatoAPI(find_ontology_data=finder)
    tokens = api.swap_input_text(input_text)
    return _reconstruct(tokens, input_text) if tokens else input_text


def main():
    parser = argparse.ArgumentParser(
        prog='parse',
        description=(
            'Parse input text against an OWL ontology and swap matched terms '
            'to their canonical forms.'
        ),
    )
    parser.add_argument(
        '--ontology', required=True, metavar='PATH',
        help='Path to the .owl file.',
    )
    parser.add_argument(
        '--input-text', required=True, metavar='TEXT',
        help='Input text to parse.',
    )
    parser.add_argument(
        '--namespace', default=None, metavar='URI',
        help='RDF namespace URI (auto-derived from the ontology name if omitted).',
    )

    cache_group = parser.add_mutually_exclusive_group()
    cache_group.add_argument(
        '--force-cache',
        action='store_true',
        help=(
            'Rebuild the JSON cache from the OWL file even if a cached copy '
            'already exists, then parse via the refreshed cache. Use this after '
            'editing an OWL file to ensure the snapshot is up to date. '
            'Cannot be combined with --live.'
        ),
    )
    cache_group.add_argument(
        '--live',
        action='store_true',
        help=(
            'Parse directly from the OWL file without reading or writing the '
            'JSON cache. Slower at startup because the full RDF graph is loaded '
            'and SPARQL views are built on every run. Useful when iterating on '
            'an ontology before committing a cache rebuild. '
            'WARNING: MIXED-schema ontologies (those with owl:NamedIndividual '
            'leaf entities, such as econ.owl) will return fewer matches on this '
            'path than the cached path; a WARNING is emitted automatically when '
            'this is detected. Use the default cached path (or --force-cache) '
            'for full coverage. Cannot be combined with --force-cache.'
        ),
    )

    args = parser.parse_args()

    ontology_path = Path(args.ontology).expanduser().resolve()
    if not ontology_path.exists():
        _log.error('Ontology file not found: %s', ontology_path)
        sys.exit(1)

    if args.live:
        print(_parse_live(ontology_path, args.input_text))
        return

    from mutato.api import OntologyParser

    cp = _cache_path(ontology_path)

    if args.force_cache or not cp.exists():
        _log.info('Building JSON cache from OWL -> %s', cp)
        op = OntologyParser(ontology_path, namespace=args.namespace)
        cp.write_text(json.dumps(op.to_dict(), indent=2))
    else:
        _log.info('Loading cache -> %s', cp)
        op = OntologyParser.from_dict(
            json.loads(cp.read_text()),
            name=ontology_path.stem,
        )

    print(op.parse(args.input_text))


if __name__ == '__main__':
    main()
