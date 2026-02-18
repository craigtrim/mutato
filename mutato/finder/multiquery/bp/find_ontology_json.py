# !/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Generic Facade to Find Data in a single Ontology JSON file """


from collections import defaultdict

from mutato.core import configure_logging
from mutato.finder.singlequery.bp import AskJsonAPI
from mutato.finder.multiquery.dmo import OwlFindCanon

class FindOntologyJSON(object):
    """ Generic Facade to Find Data in a single Ontology JSON file """

    def __init__(self,
                 d_owl: dict,
                 ontology_name: str):
        """ Change Log

        Created:
            26-May-2024
            craigtrim@gmail.com
            *   https://github.com/Maryville-University-DLX/transcriptiq/issues/21
        """
        self.logger = configure_logging(__name__)
        self.d_owl = d_owl
        self.ontology_name = ontology_name
        self._ask_json_api = AskJsonAPI(d_owl)

    def ontologies(self) -> list[str]:
        return [self.ontology_name]

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

    def predicates(self) -> list[str]:
        """
        Retrieves the list of predicates from the JSON API.

        Returns:
            A list of strings representing the predicates.
        """
        return self._ask_json_api.predicates()

    def by_predicate(self,
                     predicate_name: str) -> dict:
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

        Returns:
            dict: triples (keyed by subject)
        """
        return self._by_predicate(predicate_name)

    def _by_predicate(self, predicate_name: str) -> dict:
        """
        Retrieves ontology data based on the given predicate name.

        Args:
            predicate_name (str): The name of the predicate.

        Returns:
            dict: The ontology data retrieved based on the predicate name.
        """
        return self._ask_json_api.by_predicate(predicate_name)

    def by_predicate_rev(self,
                         predicate_name: str) -> dict:
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
        return self._by_predicate_rev(predicate_name)

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

    def _by_predicate_rev(self, predicate_name: str) -> dict:
        """
        Create a Object-to-Subjects dictionary by Predicate Name

        Args:
            predicate_name (str): the name of the predicate

        Returns:
            dict: triples (keyed by object)
        """
        d_rev = defaultdict(list)
        for k in self._by_predicate(predicate_name):
            [d_rev[k].append(x) for x in self._by_predicate(predicate_name)[k]]
        return dict(d_rev)

    # -----------------------------------------------------------------------------
    # Purpose:  Exclude Useless Predicates
    # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
    #           issuecomment-2433585518
    # Updated:  23-Oct-2024
    # -----------------------------------------------------------------------------
    # def comments(self) -> dict:
    #     """
    #     Get the dictionary of comments.

    #     Returns:
    #         dict: The dictionary of comments.
    #     """
    #     return self._ask_json_api.comments()
    # -----------------------------------------------------------------------------

    def effects(self) -> dict:
        """
        Get the dictionary of effects.

        Returns:
            dict: The dictionary of effects.
        """
        return self._by_predicate('effects')

    def effects_rev(self) -> dict:
        """
        Create a Object-to-Subjects dictionary by 'effects' Predicate Name

        Returns:
            dict: triples (keyed by object)
        """
        return self.by_predicate_rev('effects')

    def requires(self) -> dict:
        """
        Get the dictionary of requirements.

        Returns:
            dict: The dictionary of requirements.
        """
        return self._by_predicate("requires")

    def required_by(self) -> dict:
        """
        Create a Object-to-Subjects dictionary by 'requires' Predicate Name

        Returns:
            dict: triples (keyed by object)
        """
        return self._by_predicate_rev('requires')

    def requires_by_entity(self, input_text: str) -> list | None:
        """
        Get the list of requirements by the given input text.

        Args:
            input_text (str): The input text.

        Returns:
            list | None: The list of requirements.
        """
        input_text = self._to_entity_name(input_text)
        if self.requires() and input_text in self.requires():
            return self.requires()[input_text]

    def required_by_entity(self, input_text: str) -> list | None:
        """
        Get the list of entities that are required by the given input text.

        Args:
            input_text (str): The input text.

        Returns:
            list | None: The list of entities.
        """
        input_text = self._to_entity_name(input_text)
        if self.required_by() and input_text in self.required_by():
            return self.required_by()[input_text]

    def similar(self) -> dict:
        """
        Get the dictionary of similar entities.

        Returns:
            dict: The dictionary of similar entities.
        """
        return self._by_predicate('similarTo')

    def similar_rev(self) -> dict:
        """
        Create a Object-to-Subjects dictionary by 'similarTo' Predicate Name

        Returns:
            dict: triples (keyed by object)
        """
        return self._by_predicate_rev('similarTo')

    def similar_by_entity(self, input_text: str) -> dict:
        """
        Get the dictionary of similar entities by the given input text.

        Args:
            input_text (str): The input text.

        Returns:
            dict: The dictionary of similar entities.
        """
        results = []
        input_text = self._to_entity_name(input_text)

        if self.similar() and input_text in self.similar():
            [results.append(x) for x in self.similar()[input_text]]

        if self.similar_rev() and input_text in self.similar_rev():
            [results.append(x) for x in self.similar_rev()[input_text]]

        return results

    def implies(self) -> dict:
        """
        Get the dictionary of implied entities.

        Returns:
            dict: The dictionary of implied entities.
        """
        return self._by_predicate('implies')

    def implies_by_entity(self, input_text: str) -> dict:
        """
        Get the dictionary of implied entities by the given input text.

        Args:
            input_text (str): The input text.

        Returns:
            dict: The dictionary of implied entities.
        """
        input_text = self._to_entity_name(input_text)
        if self.implies() and input_text in self.implies():
            return self.implies()[input_text]

    def implied_by(self) -> dict:
        """
        Get the dictionary of entities that are implied by other entities.

        Returns:
            dict: The dictionary of implied entities.
        """
        return self._by_predicate_rev('implies')

    def implied_by_entity(self, input_text: str) -> dict:
        """
        Get the dictionary of entities that are implied by the given input text.

        Args:
            input_text (str): The input text.

        Returns:
            dict: The dictionary of implied entities.
        """
        input_text = self._to_entity_name(input_text)
        if self.implied_by() and input_text in self.implied_by():
            return self.implied_by()[input_text]

    def is_canon(self, input_text: str) -> bool:
        """
        Check if the given input text is a canonical form.

        Args:
            input_text (str): The input text.

        Returns:
            bool: True if the input text is a canonical form, False otherwise.
        """
        return self._ask_json_api.synonyms().get(input_text) is not None

    def find_canon(self, input_text: str) -> str | None:
        """
        Finds the canonical form of the given input text.

        Args:
            input_text (str): The input text to find the canonical form for.

        Returns:
            str | None: The canonical form of the input text, or None if no canonical form is found.
        """
        find_canon = OwlFindCanon(
            d_synonyms_fwd=self._ask_json_api.synonyms(),
            d_synonyms_rev=self._ask_json_api.synonyms_rev()
        ).process

        return find_canon(input_text)

    def is_variant(self,
                   input_text: str) -> bool:
        """
        Check if the given input text is a variant.

        Args:
            input_text (str): The input text.

        Returns:
            bool: True if the input text is a variant, False otherwise.
        """
        return self._ask_json_api.synonyms_rev().get(input_text) is not None

    def find_variants(self,
                      input_text: str) -> list[str] | None:
        """
        Find the variants of the given input text.

        Args:
            input_text (str): The input text to find the variants for.

        Returns:
            list[str] | None: The list of variants, or None if no variants are found.
        """
        return self._ask_json_api.synonyms().get(input_text)

    def find_ner(self, input_text: str) -> str | None:
        """
        Find the named entity recognition (NER) for the given input text.

        Args:
            input_text (str): The input text to find the NER for.

        Returns:
            str | None: The NER for the input text, or None if no NER is found.
        """
        return self._ask_json_api.find_ner(input_text)

    def labels(self) -> dict[str, str] | None:
        """
        Get the dictionary of labels.

        Returns:
            dict | None: The dictionary of labels, or None if no labels exist.
        """
        return self._ask_json_api.labels()

    def labels_rev(self) -> dict[str, str] | None:
        """
        Get the reverse dictionary of labels.

        Returns:
            dict | None: The reverse dictionary of labels, or None if no labels exist.
        """
        d_labels = self.labels()
        if not d_labels or not len(d_labels):
            return None

        d_rev = {}
        for entity in d_labels:
            for label in d_labels[entity]:
                d_rev[label] = entity

        return d_rev

    def label_by_entity(self, input_text: str) -> str | None:
        """
        Get the label for the given input text.

        Args:
            input_text (str): The input text.

        Returns:
            str | None: The label for the input text, or None if no label is found.
        """
        input_text = self._to_entity_name(input_text)
        if input_text not in self.labels():
            pass

        if input_text in self.labels():
            label_result = self.labels()[input_text]
            assert isinstance(label_result, str)
            return label_result

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

    def spans(self) -> dict:
        """Get the spans dictionary.

        Returns:
            dict: The spans dictionary.
        """
        return self._ask_json_api.spans()

    def span_keys(self) -> list | None:
        """Get the sorted list of span keys.

        Returns:
            list | None: The sorted list of span keys, or None if no spans exist.
        """
        spans = self.spans()
        if spans and len(spans):
            return sorted(self.spans().keys(), key=len)

    def synonyms(self) -> dict:
        """Get the synonyms dictionary.

        Returns:
            dict: The synonyms dictionary.
        """
        return self._ask_json_api.synonyms()

    def synonyms_rev(self) -> dict:
        """Get the reverse synonyms dictionary.

        Returns:
            dict: The reverse synonyms dictionary.
        """
        return self._ask_json_api.synonyms_rev()

    def trie(self) -> dict:
        """Get the trie dictionary.

        Returns:
            dict: The trie dictionary.
        """
        return self._ask_json_api.trie()

    def types(self) -> dict:
        """Get the types dictionary.

        Returns:
            dict: The types dictionary.
        """
        return self._ask_json_api.by_predicate("rdfs:subClassOf")

    def types_rev(self) -> dict:
        """Get the reverse types dictionary.

        Returns:
            dict: The reverse types dictionary.
        """
        return self._by_predicate_rev('rdfs:subClassOf')

    def uses(self) -> dict:
        """Get the uses dictionary.

        Returns:
            dict: The uses dictionary.
        """
        return self._by_predicate('uses')

    def uses_rev(self) -> dict:
        """Get the reverse uses dictionary.

        Returns:
            dict: The reverse uses dictionary.
        """
        return self._by_predicate_rev('uses')

    def lookup(self) -> dict | None:
        """
        Performs a lookup in the ontology using the synonyms API.

        Returns:
            A dictionary containing the lookup results, or None if no results are found.
        """
        return self._ask_json_api.synonyms_lookup()

    def has_data(self) -> bool:
        """ Check if the underlying Ontologies have data

        Returns:
            bool: True if data exists
        """
        return self.synonyms() and len(self.synonyms())

    def entity_exists(self, input_text: str) -> bool:
        """
        Check if the given entity exists in the ontology.

        Args:
            input_text (str): The input entity.

        Returns:
            bool: True if the entity exists, False otherwise.
        """
        return input_text in self._ask_json_api.entities()

    def children(self, input_text: str) -> list[str]:
        """
        Get the children of the given entity.

        Args:
            input_text (str): The input entity.

        Returns:
            list[str]: The list of children entities.
        """
        return self._ask_json_api.children(input_text)

    def children_and_self(self, input_text: str) -> list[str]:
        """
        Get the children of the given entity, including the entity itself.

        Args:
            input_text (str): The input entity.

        Returns:
            list[str]: The list of children entities, including the entity itself.
        """
        return [input_text] + self.children(input_text)

    def descendants(self, input_text: str) -> list:
        """
        Get the descendants of the given entity.

        Args:
            input_text (str): The input entity.

        Returns:
            list: The list of descendant entities.
        """
        return self._ask_json_api.descendants(input_text)

    def descendants_and_self(self, input_text: str) -> list:
        """
        Get the descendants of the given entity, including the entity itself.

        Args:
            input_text (str): The input entity.

        Returns:
            list: The list of descendant entities, including the entity itself.
        """
        return [input_text] + self.descendants(input_text)

    def parents(self, input_text: str) -> list:
        """
        Get the parents of the given entity.

        Args:
            input_text (str): The input entity.

        Returns:
            list: The list of parent entities.
        """
        return self._ask_json_api.parents(input_text)

    def parents_and_self(self, input_text: str) -> list:
        """
        Get the parents of the given entity, including the entity itself.

        Args:
            input_text (str): The input entity.

        Returns:
            list: The list of parent entities, including the entity itself.
        """
        return [input_text] + self.parents(input_text)

    def has_parent(self, input_text: str, parent: str) -> bool:
        """
        Check if the given entity has the specified parent.

        Args:
            input_text (str): The input entity.
            parent (str): The parent entity.

        Returns:
            bool: True if the entity has the parent, False otherwise.
        """
        return parent in self.parents(input_text)

    def ancestors(self, input_text: str) -> list:
        """
        Get the ancestors of the given entity.

        Args:
            input_text (str): The input entity.

        Returns:
            list: The list of ancestor entities.
        """
        return self._ask_json_api.ancestors(input_text)

    def ancestors_and_self(self, input_text: str) -> list:
        """
        Get the ancestors of the given entity, including the entity itself.

        Args:
            input_text (str): The input entity.

        Returns:
            list: The list of ancestor entities, including the entity itself.
        """
        return [input_text] + self.ancestors(input_text)

    def has_ancestor(self, input_text: str, parent: str) -> bool:
        """
        Check if the given entity has the specified ancestor.

        Args:
            input_text (str): The input entity.
            parent (str): The ancestor entity.

        Returns:
            bool: True if the entity has the ancestor, False otherwise.
        """
        return parent in self.ancestors(input_text)
