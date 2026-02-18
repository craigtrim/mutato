#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Issue: https://github.com/craigtrim/mutato/issues/4
""" OWL Schema Pattern Enumeration """

from enum import Enum


class OWLSchema(Enum):
    """ Represents the structural design pattern used by an OWL ontology.

    CLASS_BASED  - all entities are owl:Class; hierarchy via rdfs:subClassOf only.
                   Controlled vocabulary / TBox-only lexicon pattern.
    MIXED        - top-level taxonomy uses owl:Class + rdfs:subClassOf; leaf
                   concepts are owl:NamedIndividual with multiple rdf:type
                   memberships encoding polyhierarchy.
    INDIVIDUAL   - all entities are owl:NamedIndividual; no rdfs:subClassOf.
    SKOS         - entities are skos:Concept; hierarchy via skos:broader/narrower.
    """
    CLASS_BASED = 'class_based'
    MIXED = 'mixed'
    INDIVIDUAL = 'individual'
    SKOS = 'skos'
