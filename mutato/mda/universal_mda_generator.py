#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Universal OWL-to-MDA converter with automatic schema detection.

Replaces the need for consumers to manually select a generator based on
their ontology's structural pattern.  Detection is fully automatic:

    d_owl = UniversalMDAGenerator(
        ontology_name='econ',
        absolute_path='/path/to/owls',
        namespace='http://graffl.ai/skills',
    ).generate()

The output dict is identical in shape to MDAGenerator.generate() regardless
of the underlying OWL pattern (CLASS_BASED, MIXED, INDIVIDUAL, SKOS).
"""

from mutato.core import configure_logging
from mutato.mda.mda_generator import MDAGenerator
from mutato.mda.owl_schema import OWLSchema
from mutato.mda.owl_schema_detector import OWLSchemaDetector
from mutato.mda.extractors import MixedAskOwlAPI
from mutato.finder.singlequery.svc import LoadOntologyModel
from mutato.finder.multiquery.dmo import ViewGeneratorLookup


class UniversalMDAGenerator:
    """ Auto-detecting OWL-to-MDA converter.

    Probes the ontology graph to determine its structural pattern, then
    delegates to the appropriate extraction strategy.  The output contract
    is identical to MDAGenerator.generate() for all patterns.
    """

    def __init__(self,
                 ontology_name: str,
                 absolute_path: str,
                 namespace: str):
        self.logger = configure_logging(__name__)
        self._ontology_name = ontology_name
        self._absolute_path = absolute_path
        self._namespace = namespace

    def _detect_schema(self) -> OWLSchema:
        loader = LoadOntologyModel(
            ontology_name=self._ontology_name,
            absolute_path=self._absolute_path,
            namespace=self._namespace,
        )
        graph = loader.process()
        return OWLSchemaDetector(graph).detect()

    def _generate_class_based(self) -> dict:
        """ Delegate to the existing MDAGenerator for CLASS_BASED ontologies. """
        return MDAGenerator(
            ontology_name=self._ontology_name,
            absolute_path=self._absolute_path,
            namespace=self._namespace,
        ).generate()

    def _generate_mixed(self) -> dict:
        """ Use MixedAskOwlAPI for MIXED class+individual ontologies.

        Runs the same generation pipeline as MDAGenerator but substitutes
        MixedAskOwlAPI for the standard AskOwlAPI.
        """
        api = MixedAskOwlAPI(
            ontology_name=self._ontology_name,
            absolute_path=self._absolute_path,
            namespace=self._namespace,
        )

        d_predicates: dict[str, list[str]] = api.predicates()

        d_by_predicate: dict[str, list[str]] = {}
        for prefix in d_predicates:
            predicates: list[str] = [
                f"{prefix}:{predicate}" for predicate in d_predicates[prefix]
            ]
            predicates = [
                p for p in predicates
                if p not in ['nil', 'rdfs:comment']
            ]
            for predicate in predicates:
                d_by_predicate[predicate] = api.by_predicate(predicate)

        d_synonyms_fwd = api.synonyms()

        d_ner = {entity: 'NER' for entity in api.labels()}

        d_lookup = ViewGeneratorLookup().process(d_synonyms_fwd)

        entities: list[str] = sorted(api.entities(), reverse=True)

        d_children: dict[str, list[str]] = {}
        for entity in entities:
            ch = api.children(entity)
            if ch:
                d_children[entity] = ch

        d_parents: dict[str, list[str]] = {}
        for entity in entities:
            pa = api.parents(entity)
            if pa:
                d_parents[entity] = pa

        def _ngrams() -> dict[int, list[str]]:
            result = {}
            for gram_level in range(1, 10):
                grams = api.ngrams(gram_level=gram_level)
                result[gram_level] = grams or []
            return result

        return {
            'children': d_children,
            'parents': d_parents,
            'trie': api.trie(),
            'ngrams': _ngrams(),
            'spans': api.spans(),
            'labels': api.keyed_labels(),
            'equivalents': api.equivalents(),
            'predicates': predicates,
            'by_predicate': d_by_predicate,
            'ner': d_ner,
            'synonyms': {
                'lookup': d_lookup,
                'fwd': api.synonyms(),
                'rev': api.synonyms_rev(),
            },
        }

    def generate(self) -> dict:
        """ Detect schema and produce the standard MDA dict.

        Returns:
            dict: MDA dict with keys: children, parents, trie, ngrams, spans,
                  labels, equivalents, predicates, by_predicate, ner, synonyms.
        """
        schema = self._detect_schema()
        self.logger.info(f"OWL schema detected: {schema.value} ({self._ontology_name})")

        if schema == OWLSchema.CLASS_BASED:
            return self._generate_class_based()

        if schema == OWLSchema.MIXED:
            return self._generate_mixed()

        # INDIVIDUAL and SKOS: fall back to CLASS_BASED pipeline until
        # dedicated extractors are implemented (see issue #4)
        self.logger.warning(
            f"Schema {schema.value} has no dedicated extractor yet; "
            f"falling back to CLASS_BASED pipeline"
        )
        return self._generate_class_based()
