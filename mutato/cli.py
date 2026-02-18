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


def main():
    parser = argparse.ArgumentParser(
        prog='parse',
        description='Parse input text against an OWL ontology and swap matched terms to their canonical forms.',
    )
    parser.add_argument('--ontology', required=True, metavar='PATH',
                        help='Path to the .owl file')
    parser.add_argument('--input-text', required=True, metavar='TEXT',
                        help='Input text to parse')
    parser.add_argument('--namespace', default=None, metavar='URI',
                        help='RDF namespace URI (auto-derived from ontology name if omitted)')
    parser.add_argument('--force-cache', action='store_true',
                        help='Rebuild the JSON cache even if it already exists')
    args = parser.parse_args()

    from mutato.api import OntologyParser

    ontology_path = Path(args.ontology).expanduser().resolve()
    if not ontology_path.exists():
        _log.error(f'Ontology file not found: {ontology_path}')
        sys.exit(1)

    cp = _cache_path(ontology_path)

    if args.force_cache or not cp.exists():
        _log.info(f'Building JSON cache from OWL -> {cp}')
        op = OntologyParser(ontology_path, namespace=args.namespace)
        cp.write_text(json.dumps(op.to_dict(), indent=2))
    else:
        _log.info(f'Loading cache -> {cp}')
        op = OntologyParser.from_dict(
            json.loads(cp.read_text()),
            name=ontology_path.stem,
        )

    print(op.parse(args.input_text))


if __name__ == '__main__':
    main()
