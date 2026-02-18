# !/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Generic Facade to Find Data in 1..* Ontology Models """


from functools import lru_cache
from collections import defaultdict

from mutato.finder.multiquery.dmo import (
    ModelResultMerge,
    ViewGeneratorLookup
)
from mutato.finder.multiquery.svc import (
    FindNER,
    FindSynonyms,
    FindTypes,
    FindEquivalents,
    LoadSynonyms,
    QueryNerDepth,
    QueryNerLabel,
    QueryNerTaxo
)
from mutato.finder.singlequery.bp import AskOwlAPI
from mutato.finder.singlequery.dto import QueryResultType
from mutato.core import configure_logging, Enforcer, isEnabledForDebug


class FindOntologyData(object):
    """ Generic Facade to Find Data in 1..* Ontology Models """

    def __init__(self,
                 ontologies: list,
                 absolute_path: str,
                 namespace: str):
        """ Change Log

        Created:
            26-May-2022
            craigtrim@gmail.com
            *   https://github.com/grafflr/deepnlu/issues/2
        Updated:
            24-Nov-2022
            craigtrim@gmail.com
            *   correct casing in labels-rev
                https://github.com/craigtrim/owl-finder/issues/1#issuecomment-1326750848
            *   corrected defect in children-and-self
                https://github.com/craigtrim/owl-finder/issues/1#issuecomment-1326754158
        Updated:
            16-Aug-2023
            craig@bast.ai
            *   add 'find-equivalents'
                https://bast-ai.atlassian.net/browse/COR-139

        Args:
            ontologies (list): one-or-more Ontology models to use in processing
            absolute_path (str): an absolute path that applies to all the OWL models
        """
        self.logger = configure_logging(__name__)
        if isEnabledForDebug(self.logger):
            Enforcer.is_list(ontologies)

        self._ontologies = ontologies
        self._absolute_path = absolute_path

        self._d_ontologies = self._load(
            ontologies=ontologies,
            absolute_path=absolute_path,
            namespace=namespace)

        self._merge = ModelResultMerge().process

        self._query_ner_label = QueryNerLabel(self._d_ontologies).process
        self._query_ner_depth = QueryNerDepth(self._d_ontologies).process
        self._query_ner_taxo = QueryNerTaxo(self._d_ontologies).process

        self._load_synonyms = LoadSynonyms(
            d_ontologies=self._d_ontologies,
            model_result_merge=self._merge)

        self._find_synonyms = FindSynonyms(
            d_synonyms_fwd=self.synonyms(),
            d_synonyms_rev=self.synonyms_rev())

        self._find_types = FindTypes(
            d_types_fwd=self.types(),
            d_types_rev=self.types_rev())

        self._find_equivalents = FindEquivalents(
            list(self._d_ontologies.values())).process

    def ontologies(self) -> list:
        return self._ontologies

    def absolute_path(self) -> str:
        return self._absolute_path

    def _load(self,
              ontologies: list[str],
              absolute_path: str,
              namespace: str) -> dict[str, AskOwlAPI]:
        """
        Loads ontologies and initializes AskOwlAPI instances for each ontology.

        Parameters:
            ontologies (list[str]): A list of ontology names.
            absolute_path (str): The absolute path where the ontologies are located.

        Returns:
            Dict[str, AskOwlAPI]: 
                A dictionary where:
                    - Each key is an ontology name from the input list, and
                    - The associated value is an initialized instance of AskOwlAPI for the corresponding ontology.

        Notes:
            - The method assumes that the `AskOwlAPI` class takes `ontology_name` and `absolute_path` as initialization parameters.
        """
        return {
            ontology_name: AskOwlAPI(
                ontology_name=ontology_name,
                absolute_path=absolute_path,
                namespace=namespace)
            for ontology_name in ontologies
        }

    @staticmethod
    def _to_entity_name(input_text: str) -> str:
        input_text = input_text.lower().strip()
        if ' ' in input_text:
            input_text = input_text.replace(' ', '_')
        return input_text

    @staticmethod
    def _sort_list(values: list) -> list:
        return sorted(set(values), reverse=False)

    @staticmethod
    def _type_check(input_text: str) -> None:
        """ Perform Consistent Type Checking

        Args:
            input_text (str): any input text

        Raises:
            TypeError: a type error if the input is empty
        """
        if not input_text or not len(input_text):
            raise TypeError

    def by_predicate(self,
                     predicate_name: str,
                     to_lowercase: bool = True) -> dict:
        """ Create a Subject-to-Objects dictionary by Predicate Name

        Sample Ontology:
            ###  http://{self._conf['domain']}/skills#Artifact
            :Artifact rdf:type owl:Class ;
                    rdfs:label "Artifact" ;
                    owl:backwardCompatibleWith "ARTIFACT"^^:grafflNER .

        Sample Output:
            {
                'Artifact': ['ARTIFACT']
            }

        Args:
            predicate_name (str): the name of the predicate
            to_lowercase (bool, optional): enforce case sensitive search. Defaults to True.

        Returns:
            dict: triples (keyed by subject)
        """
        return self._by_predicate(predicate_name, to_lowercase)

    @lru_cache
    def _by_predicate(self,
                      predicate_name: str,
                      to_lowercase: bool = True) -> dict:
        results = []
        for ontology_name in self._d_ontologies:
            results.append(
                self._d_ontologies[ontology_name].by_predicate(
                    predicate=predicate_name,
                    to_lowercase=to_lowercase))

        if not results:
            return None
        
        elif len(results) == 1:
            return results[0]

        return self._merge(
            sorted(set(results)),
            QueryResultType.DICT_OF_STR2LIST
        )

    def by_predicate_rev(self,
                         predicate_name: str,
                         to_lowercase: bool = True) -> dict:
        """ Create a Object-to-Subjects dictionary by Predicate Name

        Sample Ontology:
            ###  http://{self._conf['domain']}/skills#Artifact
            :Artifact rdf:type owl:Class ;
                    rdfs:label "Artifact" ;
                    owl:backwardCompatibleWith "ARTIFACT"^^:grafflNER .

        Sample Output:
            {
                'ARTIFACT': ['Artifact']
            }

        Args:
            predicate_name (str): the name of the predicate
            to_lowercase (bool, optional): enforce case sensitive search. Defaults to True.

        Returns:
            dict: triples (keyed by object)
        """
        return self._by_predicate_rev(predicate_name, to_lowercase)

    @lru_cache
    def _by_predicate_rev(self,
                          predicate_name: str,
                          to_lowercase: bool = True) -> dict:
        results = []
        for ontology_name in self._d_ontologies:
            results.append(
                self._d_ontologies[ontology_name].by_predicate(
                    reverse=True,
                    predicate=predicate_name,
                    to_lowercase=to_lowercase))

        if not results:
            return None
        elif len(results) == 1:
            return results[0]
        return self._merge(results, QueryResultType.DICT_OF_STR2LIST)

    def transitive(self,
                   input_text: str,
                   query: callable) -> list:
        """ Invoke any function in a transitive (recursive) manner

        Usage:
            self.transitive('<entity>', self.implies_by_entity)

        Args:
            input_text (str): any input text or entity
            query (callable): the function to use recursively

        Returns:
            list: the results (if any)
        """
        results = []

        def update(query_results: list | None):
            if query_results:
                [results.append(x) for x in query_results]

        update(query(input_text))
        for parent in self.parents(input_text):
            update(self.transitive(parent, query))

        return results

    # -----------------------------------------------------------------------------
    # Purpose:  Exclude Useless Predicates
    # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
    #           issuecomment-2433585518
    # Updated:  23-Oct-2024
    # -----------------------------------------------------------------------------
    # @lru_cache
    # def comments(self) -> dict:
    #     results = []
    #     for ontology_name in self._d_ontologies:
    #         results.append(self._d_ontologies[ontology_name].comments())

    #     if not results:
    #         return None
    #     elif len(results) == 1:
    #         return results[0]
    #     return self._merge(results, QueryResultType.DICT_OF_STR2LIST)
    # -----------------------------------------------------------------------------

    def effects(self) -> dict:
        """ Find Effects Relationships

        Sample:
            Given   ?a effects ?b
            Return  ?a : [?b]

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity effects
        """
        return self._by_predicate('effects')

    @lru_cache
    def effects_rev(self) -> dict:
        """ Find Effected By relationships

        Sample:
            Given   ?a effected by ?b
            Return  ?b : [?a]

        Returns:
            dict: reverse of effected by function
        """
        return self._by_predicate_rev('effects')

    @lru_cache
    def requires(self) -> dict:
        """ Find Requires Relationships

        Sample:
            Given   ?a requires ?b
            Return  ?a : [?b]

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity requires
        """
        return self._by_predicate('requires')

    @lru_cache
    def required_by(self) -> dict:
        """ Find Required By relationships

        Sample:
            Given   ?a requires ?b
            Return  ?b : [?a]

        Returns:
            dict: reverse of requires function
        """
        return self._by_predicate_rev('requires')

    def requires_by_entity(self,
                           input_text: str) -> list | None:
        """ Retrict Requires Relationship to a Single Entity

        Args:
            input_text (str): the entity to search for

        Returns:
            list | None: a list of zero-or-more the incoming entity requires
        """
        input_text = self._to_entity_name(input_text)
        if self.requires() and input_text in self.requires():
            return self.requires()[input_text]

    def required_by_entity(self,
                           input_text: str) -> list | None:
        """ Retrict Required-By Relationship to a Single Entity

        Args:
            input_text (str): the entity to search for

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity is required by
        """
        input_text = self._to_entity_name(input_text)
        if self.required_by() and input_text in self.required_by():
            return self.required_by()[input_text]

    @lru_cache
    def similar(self) -> dict:
        """ Find Similar Relationships

        Sample:
            Given       ?a similar ?b
            Return      ?a : [?b]

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity is similar to
        """
        return self._by_predicate('similarTo')

    @lru_cache
    def similar_rev(self) -> dict:
        """ Find Similar Inverse Relationships

        Sample:
            Given       ?a similar ?b
            Return      ?b : [?a]

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity is similar to
       """
        return self._by_predicate_rev('similarTo')

    def similar_by_entity(self,
                          input_text: str) -> dict:
        """ Find Similarity Relationships on a per-Entity basis
        This relationship is bi-directional

        Sample:
            Given       ?a similar ?b
                        ?x similar ?a
            Return      ?a : [?b, ?x]

        Rationale:
            if      ?x is similar to ?a
            then    ?a is similar to ?x

        Args:
            input_text (str): the entity to search for

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity is similar to
        """
        results = []
        input_text = self._to_entity_name(input_text)

        if self.similar() and input_text in self.similar():
            [results.append(x) for x in self.similar()[input_text]]

        if self.similar_rev() and input_text in self.similar_rev():
            [results.append(x) for x in self.similar_rev()[input_text]]

        return results

    @lru_cache
    def implies(self) -> dict:
        """ Find Implied Relationships

        Sample:
            Given       ?a implies ?b
            Return      ?a : [?b]

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity implies
        """
        return self._by_predicate('implies')

    @lru_cache
    def implies_by_entity(self,
                          input_text: str) -> dict:
        """ Retrict Implies Relationship to a Single Entity

        Args:
            input_text (str): the entity to search for

        Returns:
            list | None: a list of zero-or-more entities that the incoming entity implies
        """
        input_text = self._to_entity_name(input_text)
        if self.implies() and input_text in self.implies():
            return self.implies()[input_text]

    @lru_cache
    def implied_by(self) -> dict:
        """ Find Implied By relationships

        Sample:
            Given   ?a requires ?b
            Return  ?b : [?a]

        Returns:
            list | None: a list of zero-or-more entities that are implied by this entity
        """
        return self._by_predicate_rev('implies')

    @lru_cache
    def implied_by_entity(self,
                          input_text: str) -> dict:
        """ Retrict Implied By Relationship to a Single Entity

        Args:
            input_text (str): the entity to search for

        Returns:
            list | None: a list of zero-or-more entities that are implied by this entity
        """
        input_text = self._to_entity_name(input_text)
        if self.implied_by() and input_text in self.implied_by():
            return self.implied_by()[input_text]

    @lru_cache(maxsize=512, typed=False)
    def is_canon(self,
                 input_text: str) -> bool:
        """Check if Input Text is Canonical Entity

        Args:
            input_text (str): any input string

        Returns:
            bool: True if the input string is a Nursing Entity
        """
        return self._find_synonyms.is_canon(input_text)

    @lru_cache(maxsize=512, typed=False)
    def find_canon(self,
                   input_text: str) -> str | None:
        """Find the Canonical Representation of the Input String

        Args:
            input_text (str): any input string

        Returns:
            str | None: The Canonical Entity
        """
        return self._find_synonyms.find_canon(input_text)

    @lru_cache(maxsize=512, typed=False)
    def is_variant(self,
                   input_text: str) -> bool:
        """Check if Input Text is known variant for at least one Canonical Entry

        Args:
            input_text (str): any input string

        Returns:
            bool: True if the input string is a known synonym to a Nursing Entity
        """
        return self._find_synonyms.is_variant(input_text)

    @lru_cache(maxsize=512, typed=False)
    def find_variants(self,
                      input_text: str) -> list | None:
        """Find the Synonyms for a known Entity

        Args:
            input_text (str): any input string

        Returns:
            list | None: a list of synonyms for the input entity
        """
        return self._find_synonyms.find_variants(input_text)

    @lru_cache(maxsize=512, typed=False)
    def find_ner(self,
                 input_text: str) -> str | None:

        svc = FindNER(
            d_ner_depth=self.ner_depth(),
            d_ner_taxo=self.ner_taxonomy(),
            d_graffl_ner=self.graffl_ner(),
            d_spacy_ner=self.spacy_ner())

        return svc.find_ner(input_text)

    # TODO:  Find a way to fix this
    @lru_cache
    def graffl_ner(self) -> dict:
        return dict()
        # return self._query_ner_label('grafflNER')

    # TODO:  Find a way to fix this
    @lru_cache
    def graffl_ner_rev(self) -> dict:
        return dict()
        # return self._query_ner_label('grafflNER', reverse=True)

    # TODO:  Find a way to fix this
    @lru_cache
    def spacy_ner(self) -> dict:
        return dict()
        # return self._query_ner_label('spacyNER')

    # TODO:  Find a way to fix this
    @lru_cache
    def spacy_ner_rev(self) -> dict:
        return dict()
        # return self._query_ner_label('spacyNER', reverse=True)

    @lru_cache
    def ner_depth(self) -> dict:
        return self._query_ner_depth(reverse=False)

    @lru_cache
    def ner_depth_rev(self) -> dict:
        return self._query_ner_depth(reverse=True)

    @lru_cache
    def infer_by_requires(self) -> dict:
        raise NotImplementedError

    @lru_cache
    def labels(self, force_lowercase: bool = True) -> dict | None:
        """Find all the Labels keyed by Entity Name

        Returns:
            dict | None: a list of entity names with label string values
        """
        # the challenge with using 'to_lowercase=False' is that both the key and value retain their original case
        d_labels = self._by_predicate('rdfs:label', to_lowercase=False)
        if not d_labels or not len(d_labels):
            return None

        d = {}
        for k in d_labels:
            if force_lowercase:
                d[k.lower()] = d_labels[k]
            else:
                d[k] = d_labels[k]

        return d

    @lru_cache
    def labels_rev(self, force_lowercase: bool = True) -> dict | None:
        """Find all the Entity Names keyed by Label

        Notes:
            I need to maintain the integrity of label casing (preserved) vs
            entity-casing (enforced lower-case).  As a result, I finder it easier
            to perform a custom reversal in this function rather than use 'by_predicate_rev'

        Returns:
            dict | None: a list of labels with entity name values
        """
        d_labels = self.labels(force_lowercase)
        if not d_labels or not len(d_labels):
            return None

        d_rev = defaultdict(list)
        for entity in d_labels:
            for label in d_labels[entity]:
                d_rev[label].append(entity)

        return dict(d_rev)

    def label_by_entity(self,
                        input_text: str) -> str | None:
        """Find the Label for a known Entity

        Args:
            input_text (str): any input string

        Returns:
            str | None: a label for the entity (if found)
        """
        input_text = self._to_entity_name(input_text)
        if input_text not in self.labels():
            pass

        if input_text in self.labels():
            results = self.labels()[input_text]
            if results and len(results):
                return results[0]

    @lru_cache
    def ner_taxonomy(self) -> dict:
        return self._query_ner_taxo(reverse=False)

    @lru_cache
    def ner_taxonomy_rev(self) -> dict:
        return self._query_ner_taxo(reverse=True)

    def equivalents(self,
                    entities: list[str],
                    flat_list: bool = True,
                    underscore_entities: bool = True) -> dict[str, list[str]] | list[str] | None:
        """
        Find equivalent entities for a list of entities.

        Args:
        entities (list[str]): List of entities to find equivalents for.
        flat_list (bool): If True, returns a sorted list of unique equivalents;
                          if False, returns a dictionary of equivalents.

        Reference:
        https://bast-ai.atlassian.net/browse/COR-139

        Returns:
        Optional[Union[Dict[str, list[str]], list[str]]]: Either a sorted list of 
                                                         unique equivalent entities,
                                                         or a dictionary of equivalents.
        """
        d_equivalents = self._find_equivalents(entities)

        if not flat_list:
            return d_equivalents

        master = sorted({
            x for k in d_equivalents
            for x in d_equivalents[k]
        })

        if underscore_entities:
            master = [
                x.replace(' ', '_') for x in master
            ]

        return master

    def has_spans(self) -> bool:
        """ Check if the underlying Ontologies has spans

        Returns:
            bool: True if data exists
        """
        return self.spans() and len(self.spans())

    @lru_cache
    def spans(self) -> dict:
        results = []
        for ontology_name in self._d_ontologies:
            results.append(self._d_ontologies[ontology_name].spans())

        if not results:
            return None
        elif len(results) == 1:
            return results[0]

        return self._merge(results, QueryResultType.DICT_OF_STR2DICT)

    @lru_cache
    def span_keys(self) -> list | None:
        """ Return Span Keys sorted by Length

        Returns:
            list: list of span keys sorted by length
        """
        spans = self.spans()
        if spans and len(spans):
            return sorted(self.spans().keys(), key=len)

    def synonyms(self) -> dict:
        """ Return Synonyms keyed by Entity Name

        Returns:
            dict: dictionary of entities associated to a list of zero-or-more synonyms
        """
        return self._load_synonyms.synonyms()

    def synonyms_rev(self) -> dict:
        """ Return Entities keyed by Synonyms

        Returns:
            dict: dictionary of synonyms associated to a list of one-or-more entities
        """
        return self._load_synonyms.synonyms_rev()

    @lru_cache
    def trie(self) -> dict:
        results = []
        for ontology_name in self._d_ontologies:
            results.append(self._d_ontologies[ontology_name].trie())

        if not results:
            return None
        elif len(results) == 1:
            return results[0]
        return self._merge(results, QueryResultType.DICT_OF_STR2LIST)

    @lru_cache
    def types(self) -> dict:
        return self._by_predicate('rdfs:subClassOf')

    @lru_cache
    def types_rev(self) -> dict:
        return self._by_predicate_rev('rdfs:subClassOf')

    @lru_cache
    def uses(self) -> dict:
        return self._by_predicate('uses')

    @lru_cache
    def uses_rev(self) -> dict:
        return self._by_predicate_rev('uses')

    @lru_cache
    def has_parent(self,
                   input_text: str,
                   parent: str) -> bool:
        """ Simple Truth check
            Does the incoming input entity have the incoming parent as a parent?

        Args:
            input_text (str): a candidate concept

        Returns:
            bool: True if the described relationship exists
        """
        return self._find_types.has_parent(
            parent=parent,
            input_text=input_text)

    @lru_cache
    def has_ancestor(self,
                     input_text: str,
                     parent: str) -> bool:
        """ Simple Truth check
            Does the incoming input entity have the incoming parent as an ancestor?

        Args:
            input_text (str): a candidate concept

        Returns:
            bool: True if the described relationship exists
        """
        return self._find_types.has_ancestor(
            parent=parent,
            input_text=input_text)

    @lru_cache
    def entity_exists(self,
                      input_text: str) -> bool:
        """ Simple Truth check
            Does this value exist anywhere in the Ontology?

        Args:
            input_text (str): a candidate concept

        Returns:
            bool: True if the concept exists in the Ontology
        """
        return self._find_types.exists(input_text)

    @lru_cache
    def children(self,
                 input_text: str) -> list[str]:
        """ Return the Children for an Entity

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list[str]: the results
        """
        self._type_check(input_text)
        return self._sort_list(self._find_types.children(input_text))

    @lru_cache
    def children_and_self(self,
                          input_text: str) -> list[str]:
        """ Return the Children for an Entity,
            and the Entity itself, in a list of results

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list[str]: the results
        """
        self._type_check(input_text)
        if not self.entity_exists(input_text):
            return []

        input_text = input_text.lower().strip()
        results = self._find_types.children(input_text)
        if not results:
            results = []

        results.append(input_text)
        return self._sort_list(results)

    @lru_cache
    def descendants(self,
                    input_text: str) -> list:
        """ Return the Descendants for an Entity

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list: the list of results (if any)
        """
        self._type_check(input_text)
        return self._find_types.descendants(input_text)

    @lru_cache
    def descendants_and_self(self,
                             input_text: str) -> list:
        """ Return the Descendants for an Entity,
            and the Entity itself, in a list of results

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list: the list of results (if any)
        """
        self._type_check(input_text)
        if not self.entity_exists(input_text):
            return []

        input_text = input_text.lower().strip()
        results = self._find_types.descendants(input_text)
        if not results:
            results = []

        results.append(input_text)
        return self._sort_list(results)

    @lru_cache
    def parents(self,
                input_text: str) -> list:
        """ Return the Parents for an Entity

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list: the list of results (if any)
        """
        self._type_check(input_text)
        return self._find_types.parents(input_text)

    @lru_cache
    def parents_and_self(self,
                         input_text: str) -> list:
        """ Return the Parents for an Entity,
            and the Entity itself, in a list of results

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list: the list of results (if any)
        """
        self._type_check(input_text)
        if not self.entity_exists(input_text):
            return []

        input_text = input_text.lower().strip()
        results = self._find_types.parents(input_text)
        if not results:
            results = []

        results.append(input_text)
        return self._sort_list(results)

    @lru_cache
    def ancestors(self,
                  input_text: str) -> list:
        """ Return the Ancestors for an Entity

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list: the list of results (if any)
        """
        self._type_check(input_text)
        return self._sort_list(self._find_types.ancestors(input_text))

    @lru_cache
    def ancestors_and_self(self,
                           input_text: str) -> list:
        """ Return the Ancestors for an Entity,
            and the Entity itself, in a list of results

        Args:
            input_text (str): the input entity

        Raises:
            TypeError: Invalid Input

        Returns:
            list: the list of results (if any)
        """
        self._type_check(input_text)
        if not self.entity_exists(input_text):
            return []

        input_text = input_text.lower().strip()
        results = self._find_types.ancestors(input_text)
        if not results:
            results = []

        results.append(input_text)
        return self._sort_list(results)

    @lru_cache
    def lookup(self) -> dict | None:
        """ Generate n-Gram Spans suitable for Synonym Matching

        Reference:
            https://github.com/grafflr/ask-owl/issues/4
            https://github.com/grafflr/deepnlu/issues/21#issuecomment-1141524102

        Returns:
            dict: dictionary of values keyed by n-gram size
        """
        d_synonyms_fwd = self.synonyms()

        if not d_synonyms_fwd or not len(d_synonyms_fwd):
            return None

        return ViewGeneratorLookup().process(d_synonyms_fwd)

    def has_data(self) -> bool:
        """ Check if the underlying Ontologies have data

        Returns:
            bool: True if data exists
        """
        return self.synonyms() and len(self.synonyms())
