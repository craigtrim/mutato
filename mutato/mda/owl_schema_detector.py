#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Auto-detect the structural pattern of an OWL ontology graph """

from rdflib import Graph, RDF, OWL
from rdflib.namespace import SKOS

from mutato.mda.owl_schema import OWLSchema
from mutato.core import configure_logging


class OWLSchemaDetector:
    """ Runs lightweight SPARQL probes against an rdflib Graph to determine
    which OWL structural pattern is in use — without any consumer configuration.

    Detection priority (first match wins):
        1. skos:Concept triples present → SKOS
        2. owl:NamedIndividual + rdfs:subClassOf both present → MIXED
        3. owl:NamedIndividual present, no rdfs:subClassOf → INDIVIDUAL
        4. Otherwise → CLASS_BASED
    """

    def __init__(self, graph: Graph):
        self.logger = configure_logging(__name__)
        self._graph = graph

    def _has_skos_concepts(self) -> bool:
        return any(self._graph.triples((None, RDF.type, SKOS.Concept)))

    def _has_named_individuals(self) -> bool:
        return any(self._graph.triples((None, RDF.type, OWL.NamedIndividual)))

    def _has_subclass_of(self) -> bool:
        from rdflib import RDFS
        return any(self._graph.triples((None, RDFS.subClassOf, None)))

    def detect(self) -> OWLSchema:
        """ Probe the graph and return the detected OWLSchema.

        Returns:
            OWLSchema: the detected schema pattern
        """
        if self._has_skos_concepts():
            self.logger.debug("Detected schema: SKOS")
            return OWLSchema.SKOS

        has_individuals = self._has_named_individuals()
        has_subclasses = self._has_subclass_of()

        if has_individuals and has_subclasses:
            self.logger.debug("Detected schema: MIXED")
            return OWLSchema.MIXED

        if has_individuals:
            self.logger.debug("Detected schema: INDIVIDUAL")
            return OWLSchema.INDIVIDUAL

        self.logger.debug("Detected schema: CLASS_BASED")
        return OWLSchema.CLASS_BASED
