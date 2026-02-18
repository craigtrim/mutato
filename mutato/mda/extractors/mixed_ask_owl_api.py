#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Issue: https://github.com/craigtrim/mutato/issues/4
""" AskOwlAPI variant for mixed class/individual OWL ontologies.

In a MIXED ontology, leaf concepts are owl:NamedIndividual with multiple
rdf:type memberships encoding polyhierarchy, while top-level taxonomy still
uses owl:Class + rdfs:subClassOf.

Overrides three methods that in the base class assume class-only structure:
    - children(entity)   - also finds individuals typed as the entity
    - parents(entity)    - also reads rdf:type for individual parents
    - ngrams(gram_level) - uses rdfs:label enumeration instead of rdfs:subClassOf
"""

from functools import lru_cache

from mutato.finder.singlequery.bp import AskOwlAPI
from mutato.finder.singlequery.dto import QueryResultType

# OWL built-in local names to exclude from parent results
_OWL_BUILTINS = {
    'NamedIndividual', 'Thing', 'Class', 'Ontology',
    'ObjectProperty', 'DatatypeProperty', 'AnnotationProperty',
}


class MixedAskOwlAPI(AskOwlAPI):
    """ AskOwlAPI variant for MIXED class+individual OWL ontologies. """

    @lru_cache(maxsize=1024)
    def ngrams(self, gram_level: int) -> list | None:
        """ Enumerate all labelled entities and filter by word count.

        The base class queries rdfs:subClassOf which misses individuals.
        Here we enumerate all subjects that have an rdfs:label instead.

        Args:
            gram_level (int): 1 = unigrams, 2 = bigrams, etc.

        Returns:
            list | None: entity local names matching the gram level
        """
        sparql = 'SELECT ?a WHERE { ?a rdfs:label ?b }'

        results = self._execute_query(
            sparql=sparql,
            to_lowercase=True,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

        if not results:
            return None

        return [x for x in results if x.count('_') == gram_level - 1]

    @lru_cache(maxsize=1024)
    def children(self, entity: str) -> list | None:
        """ Return direct children: subclasses OR individuals typed as entity.

        Args:
            entity (str): entity local name (original casing)

        Returns:
            list | None: child entity local names
        """
        sparql = """
            SELECT ?a WHERE {
                { ?a rdfs:subClassOf :#ENTITY }
                UNION
                { ?a rdf:type :#ENTITY .
                  ?a rdf:type owl:NamedIndividual }
            }
        """.replace('#ENTITY', entity)

        results = self._execute_query(
            sparql=sparql,
            to_lowercase=False,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

        return results or []

    @lru_cache(maxsize=1024)
    def parents(self, entity: str) -> list | None:
        """ Return direct parents: superclasses OR rdf:type classes for individuals.

        Filters out OWL built-in type names (NamedIndividual, Thing, etc.).

        Args:
            entity (str): entity local name (original casing)

        Returns:
            list | None: parent entity local names
        """
        sparql = """
            SELECT ?a WHERE {
                { :#ENTITY rdfs:subClassOf ?a . FILTER(isIRI(?a)) }
                UNION
                { :#ENTITY rdf:type ?a .
                  FILTER(isIRI(?a) &&
                         ?a != owl:NamedIndividual &&
                         ?a != owl:Thing &&
                         ?a != owl:Class) }
            }
        """.replace('#ENTITY', entity)

        results = self._execute_query(
            sparql=sparql,
            to_lowercase=False,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

        if not results:
            return []

        return [r for r in results if r not in _OWL_BUILTINS]
