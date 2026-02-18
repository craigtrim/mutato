#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""High-level OntologyParser: the primary public API for mutato consumers."""

from pathlib import Path


class OntologyParser:
    """Parse input text against an OWL ontology.

    Two construction paths:

        # From an OWL file (builds the JSON dict internally):
        parser = OntologyParser('/path/to/econ.owl')

        # From a pre-built dict (e.g. loaded from S3):
        parser = OntologyParser.from_dict(d_owl, name='econ')

    Both paths expose the same interface::

        d = parser.to_dict()        # JSON-serialisable dict; upload to S3/cache
        s = parser.parse('some text')  # returns canonical plain-text string
    """

    def __init__(self, owl_path: str | Path, namespace: str | None = None):
        from mutato.mda.universal_mda_generator import UniversalMDAGenerator

        p = Path(owl_path).expanduser().resolve()
        self._name = p.stem
        self._d_owl = UniversalMDAGenerator(
            ontology_name=p.stem,
            absolute_path=str(p.parent),
            namespace=namespace,
        ).generate()
        self._api = self._make_api(self._d_owl, self._name)

    @classmethod
    def from_dict(cls, d_owl: dict, name: str) -> 'OntologyParser':
        """Restore a parser from a pre-built dict (e.g. fetched from S3)."""
        obj = cls.__new__(cls)
        obj._name = name
        obj._d_owl = d_owl
        obj._api = cls._make_api(d_owl, name)
        return obj

    @staticmethod
    def _make_api(d_owl: dict, name: str):
        from mutato.finder.multiquery.bp import FindOntologyJSON
        from mutato.parser import MutatoAPI
        return MutatoAPI(find_ontology_data=FindOntologyJSON(d_owl=d_owl, ontology_name=name))

    def to_dict(self) -> dict:
        """Return the JSON-serialisable MDA dict for external storage."""
        return self._d_owl

    def parse(self, text: str) -> str:
        """Parse *text* and return a plain-text string with canonical forms."""
        tokens = self._api.swap_input_text(text)
        if not tokens:
            return text
        return ' '.join(
            t['swaps']['canon'] if t.get('swaps') else t['text'].strip()
            for t in tokens
            if t.get('swaps') or t['text'].strip()
        )
