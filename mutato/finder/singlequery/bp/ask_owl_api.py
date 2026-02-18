#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" API for the ask-owl Microservice """


from functools import lru_cache
from collections import defaultdict

from mutato.finder.singlequery.svc import (
from mutato.finder.singlequery.dto import QueryResultType
        from rdflib.plugins.sparql.processor import SPARQLResult
from mutato.core import configure_logging, Enforcer, isEnabledForDebug

        result: SPARQLResult = self._execute_query(
            reverse=False,
            sparql=sparql_query,
            result_type=result_type,
            to_lowercase=to_lowercase)

        return result

    @lru_cache(maxsize=6, typed=False)
    def ngrams(self,
               gram_level: 1) -> list | None:
        """ Generate n-Grams by Size

        Args:
            gram_level (1): the gram level to query for

        Returns:
            list | None: the n-Gram results (if any)
        """
        sparql = 'SELECT ?a WHERE { ?a rdfs:subClassOf ?b }'

        results = self._execute_query(
            sparql=sparql,
            to_lowercase=True,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

        if not results or not len(results):
            return None

        return [x for x in results if x.count('_') == gram_level - 1]

    @lru_cache
    def trie(self) -> dict | None:
        """ Generate Entities in a Trie View

        Sample Input:
            ['First Quarter Results', 'First Quarter GDP', 'First Time']

        Sample Output:
            {
                'First': {
                    'Quarter': ['Results', 'GDP'],
                    'Time': [],
                }
            }

        Reference:
            https://github.com/craigtrim/askowl/issues/8

        Args:
            to_lowercase (bool, optional): lowercase all data. Defaults to True.

        Returns:
            dict: dictionary of values keyed by n-gram size
        """
        sparql = 'SELECT ?a ?b WHERE  {  ?a rdfs:subClassOf ?b }'
        d_results = self._execute_query(
            sparql=sparql,
            to_lowercase=True,
            result_type=QueryResultType.DICT_OF_STR2LIST,
        )

        if not d_results or not len(d_results):
            return None

        return GenerateViewTrie().process(d_results)

    # --------------------------------------------------------------------------------------------------------
    # Purpose:      Eliminate Functions that are not used
    # Issue:        https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2132487666
    # Updated:      26-May-2024
    # --------------------------------------------------------------------------------------------------------
    # @lru_cache(typed=False)
    # def by_subject_predicate(self,
    #                          predicate: str,
    #                          subject: str,
    #                          to_lowercase: bool = True) -> list:
    #     """ Retrieve a list of values by custom subject and custom predicate

    #     Args:
    #         predicate (str): the predicate name
    #         subject (str): the subject name
    #         to_lowercase (str, optional): optionally lowercase all results.  Defaults to True.

    #     Returns:
    #         list: a list of values for this predicate
    #     """
    #     sparql = 'SELECT ?b WHERE { #PREFIX:#SUBJECT rdf:type owl:Class ; #PREFIX:#PREDICATE ?b }'
    #     sparql = sparql.replace('#PREFIX', self.prefix)
    #     sparql = sparql.replace('#PREDICATE', predicate)
    #     sparql = sparql.replace('#SUBJECT', subject)

    #     d_results = self._execute_query(
    #         sparql=sparql,
    #         to_lowercase=to_lowercase,
    #         result_type=QueryResultType.LIST_OF_STRINGS,
    #     )

    #     return d_results
    # --------------------------------------------------------------------------------------------------------

    @lru_cache(typed=False)
    def by_predicate(self,
                     predicate: str,
                     to_lowercase: bool = True,
                     reverse: bool = False) -> list:
        """ Retrieve a list of values by custom predicate

        Args:
            predicate (str): the predicate name
            to_lowercase (str, optional): optionally lowercase all results.  Defaults to True.
            reverse (bool, optional): reverses the subject/object order. Defaults to False.
                if "?x implies ?y" and reverse=False
                    the results will be { ?x: [?y-1, ?y-2, ..., ?y-N]}
                if "?x implies ?y" and reverse=True
                    the results will be { ?y-1: [x], ?y-2: [x], ?y-N: [x]}

        Returns:
            dict: a dict of values for this predicate
        """
        sparql = 'SELECT ?a ?b WHERE { ?a #PREFIX:#PREDICATE ?b }'

        def get_prefix() -> str:
            if ':' in predicate:
                return predicate.split(':')[0].strip()
            return self.prefix

        def get_predicate() -> str:
            if ':' in predicate:
                return predicate.split(':')[-1].strip()
            return predicate

        _prefix = get_prefix()
        _predicate = get_predicate()

        sparql = sparql.replace('#PREFIX', _prefix)
        sparql = sparql.replace('#PREDICATE', _predicate)

        d_results = self._execute_query(
            sparql=sparql,
            reverse=reverse,
            to_lowercase=to_lowercase,
            result_type=QueryResultType.DICT_OF_STR2LIST,
        )

        # ------------------------------------------------------------------------------
        # Purpose:  Ensure list[str] is de-duplicated and doesn't contain key
        #           Exclude 'class' as it contains everything
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/1059
        # Updated:  13-Oct-2025
        # ------------------------------------------------------------------------------
        d_results = {
            k: [x for x in sorted(set(v)) if x != k]
            for k, v in d_results.items()
            if k not in ['class']
        }
        # ------------------------------------------------------------------------------

        return d_results

    @lru_cache
    def keyed_labels(self) -> list:
        """ Retrieve rdfs:label values from the Graph

        Returns:
            list: a list of labels
        """
        sparql = 'SELECT ?x ?a ?a WHERE { ?x rdfs:label ?a }'

        return self._execute_query(
            sparql=sparql,
            to_lowercase=False,
            result_type=QueryResultType.DICT_OF_STR2STR)

    @lru_cache
    def labels(self) -> list:
        """ Retrieve rdfs:label values from the Graph

        Returns:
            list: a list of labels
        """
        sparql = 'SELECT ?a WHERE { ?x rdfs:label ?a }'
        return self._execute_query(
            sparql=sparql,
            to_lowercase=False,
            result_type=QueryResultType.LIST_OF_STRINGS)

    @lru_cache
    def entities(self) -> list:
        """ Retrieve entities from the Graph

        Returns:
            list: a list of entities
        """
        sparql = 'SELECT ?x WHERE { ?x rdfs:label ?a }'

        # ----------------------------------------------------------------------------------------------------
        # Purpose:  Do Not LowerCase Entities
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2133849129
        # Updated:  27-May-2024
        # ----------------------------------------------------------------------------------------------------
        is_lowercase = False
        # ----------------------------------------------------------------------------------------------------

        return self._execute_query(
            sparql=sparql, to_lowercase=is_lowercase,
            result_type=QueryResultType.LIST_OF_STRINGS)

    @lru_cache
    def parents(self, entity: str):
        sparql = """
            SELECT ?a WHERE  { :#ENTITY rdfs:subClassOf ?a }
        """.replace('#ENTITY', entity)

        # ----------------------------------------------------------------------------------------------------
        # Purpose:  Do Not LowerCase Entities
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2133849129
        # Updated:  27-May-2024
        # ----------------------------------------------------------------------------------------------------
        is_lowercase = False
        # ----------------------------------------------------------------------------------------------------

        return self._execute_query(
            sparql=sparql, to_lowercase=is_lowercase,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

    @lru_cache
    def ancestors(self, entity: str) -> list[str]:
        sparql = """
            SELECT ?a WHERE  { :#ENTITY rdfs:subClassOf+ ?a }
        """.replace('#ENTITY', entity)

        # ----------------------------------------------------------------------------------------------------
        # Purpose:  Do Not LowerCase Entities
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2133849129
        # Updated:  27-May-2024
        # ----------------------------------------------------------------------------------------------------
        is_lowercase = False
        # ----------------------------------------------------------------------------------------------------

        results: list[str] = self._execute_query(
            sparql=sparql, to_lowercase=is_lowercase,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

        if results:
            return sorted(results, reverse=True)

        return results

    @lru_cache
    def children(self, entity: str):
        sparql = """
            SELECT ?a WHERE  { ?a rdfs:subClassOf :#ENTITY }
        """.replace('#ENTITY', entity)

        # ----------------------------------------------------------------------------------------------------
        # Purpose:  Do Not LowerCase Entities
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2133849129
        # Updated:  27-May-2024
        # ----------------------------------------------------------------------------------------------------
        is_lowercase = False
        # ----------------------------------------------------------------------------------------------------

        return self._execute_query(
            sparql=sparql, to_lowercase=is_lowercase,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

    @lru_cache
    def descendants(self, entity: str):
        sparql = """
            SELECT ?a WHERE  { ?a rdfs:subClassOf+ :#ENTITY }
        """.replace('#ENTITY', entity)

        # ----------------------------------------------------------------------------------------------------
        # Purpose:  Do Not LowerCase Entities
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2133849129
        # Updated:  27-May-2024
        # ----------------------------------------------------------------------------------------------------
        is_lowercase = False
        # ----------------------------------------------------------------------------------------------------

        return self._execute_query(
            sparql=sparql, to_lowercase=is_lowercase,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

    # -----------------------------------------------------------------------------
    # Purpose:  Exclude Useless Predicates
    # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
    #           issuecomment-2433585518
    # Updated:  23-Oct-2024
    # -----------------------------------------------------------------------------
    # @lru_cache
    # def comments(self) -> list:
    #     """ Retrieve rdfs:comment values from the Graph

    #     Returns:
    #         list: a list of labels
    #     """
    #     sparql = 'SELECT ?a ?b WHERE { ?a rdfs:comment ?b }'

    #     d_results = self._execute_query(
    #         sparql=sparql,
    #         to_lowercase=False,
    #         result_type=QueryResultType.DICT_OF_STR2LIST,
    #     )

    #     return d_results
    # -----------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Purpose:      Eliminate Functions that are not used
    # Issue:        https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2132487666
    # Updated:      26-May-2024
    # --------------------------------------------------------------------------------------------------------
    # @lru_cache
    # def see_also(self,
    #              to_lowercase: bool = True) -> list:
    #     """ Retrieve rdfs:seeAlso values from the Graph

    #     Args:
    #         to_lowercase (str, optional): optionally lowercase all results.  Defaults to True.

    #     Returns:
    #         list: a list of see-also values
    #     """
    #     sparql = 'SELECT ?a WHERE { ?x rdfs:seeAlso ?a }'
    #     return self._execute_query(
    #         sparql=sparql,
    #         to_lowercase=to_lowercase,
    #         result_type=QueryResultType.LIST_OF_STRINGS)
    # --------------------------------------------------------------------------------------------------------
    # @lru_cache
    # def backward_compatible_with(self,
    #                              to_lowercase: bool = True) -> list:
    #     """ Retrieve owl:backwardCompatibleWith values from the Graph

    #     Args:
    #         to_lowercase (str, optional): optionally lowercase all results.  Defaults to True.

    #     Returns:
    #         list: a list of see-also values
    #     """
    #     sparql = 'SELECT ?a WHERE { ?x rdfs:seeAlso ?a }'
    #     return self._execute_query(
    #         sparql=sparql,
    #         to_lowercase=to_lowercase,
    #         result_type=QueryResultType.LIST_OF_STRINGS)
    # --------------------------------------------------------------------------------------------------------

    @lru_cache
    def types(self,
              to_lowercase: bool = True) -> list:
        """ Retrieve rdf:type values from the Graph

        Args:
            to_lowercase (str, optional): optionally lowercase all results.  Defaults to True.

        Returns:
            list: a list of labels
        """
        sparql = 'SELECT ?a WHERE { ?a rdf:type ?x }'
        return self._execute_query(
            sparql=sparql,
            to_lowercase=to_lowercase,
            result_type=QueryResultType.LIST_OF_STRINGS)

    @lru_cache
    def _synonym_query(self) -> dict | None:
        """ Generate n-Gram Spans suitable for Synonym Matching

        Reference:
            https://github.com/craigtrim/askowl/issues/8

        Returns:
            dict: dictionary of values keyed by n-gram size
        """
        sparql = """
        SELECT ?a ?b
        WHERE
        {
            {
                { ?a rdfs:label ?b }
                OPTIONAL {?a rdfs:seeAlso ?b}
                OPTIONAL {?a skos:altLabel ?b}
                OPTIONAL {?a :inflection ?b}
            } 
            UNION
            {
                { ?a rdfs:seeAlso ?b }
                OPTIONAL {?a rdfs:label ?b}
                OPTIONAL {?a skos:altLabel ?b}
                OPTIONAL {?a :inflection ?b}
            }
            UNION
            {
                { ?a skos:altLabel ?b }
                OPTIONAL {?a rdfs:label ?b}
                OPTIONAL {?a rdfs:seeAlso ?b}
                OPTIONAL {?a :inflection ?b}
            }
            UNION
            {
                { ?a :inflection ?b }
                OPTIONAL {?a rdfs:label ?b}
                OPTIONAL {?a rdfs:seeAlso ?b}
                OPTIONAL {?a skos:altLabel ?b}
            }
        }
        """
        d_results = self._execute_query(
            sparql=sparql,
            to_lowercase=True,
            result_type=QueryResultType.DICT_OF_STR2LIST,
        )

        if not d_results or not len(d_results):
            return None

        d_normalized = defaultdict(list)
        for k in d_results:
            for synonym in d_results[k]:
                synonyms = [x.strip() for x in synonym.split(',')]
                synonyms = [x for x in synonyms if x and len(x)]
                [d_normalized[k].append(x) for x in synonyms]

        return d_normalized

    @lru_cache
    def predicates(self) -> dict | None:
        """
        Retrieves the predicates from the OWL API.

        Returns:
            A dictionary containing the predicates grouped by prefix, or None if no predicates are found.
        """
        d_predicates: dict[str, list[str]] = {}
        s_unique: set[str] = set()

        for prefix in ['rdfs', 'skos', 'owl', 'rdf']:

            sparql = """
            SELECT DISTINCT ?p
            WHERE
            {
                ?s ?p ?o .
                FILTER(STRSTARTS(STR(?p), STR(#PREFIX:)))
            }
            """.replace('#PREFIX', prefix)

            predicates = self._execute_query(
                sparql=sparql,
                to_lowercase=False,
                result_type=QueryResultType.LIST_OF_STRINGS,
            )

            if predicates and len(predicates):
                d_predicates[prefix] = predicates

                [
                    s_unique.add(x)
                    for x in predicates
                    if x and len(x)
                ]

        predicates = self._execute_query(
            sparql=f"""SELECT DISTINCT ?p WHERE {{ ?s ?p ?o . }}""",
            to_lowercase=False,
            result_type=QueryResultType.LIST_OF_STRINGS,
        )

        d_predicates[""] = [
            predicate for predicate in predicates
            if predicate not in s_unique
        ]

        return d_predicates

    @lru_cache
    def synonyms(self) -> dict | None:
        """ Generate a Dictionary of Entities keyed to Synonym Lists

        Reference:
            https://github.com/craigtrim/askowl/issues/8

        Returns:
            dict: dictionary of entities keyed by synonym
        """
        d_results = self._synonym_query()

        if not d_results or not len(d_results):
            return None

        return GenerateViewSynonyms().process(d_results)

    @lru_cache
    def synonyms_rev(self) -> dict:
        """ Reverse Synonym Dictionary:
        Synonyms are keyed to one-or-more Entities

        Reference:
            https://github.com/craigtrim/askowl/issues/8

        Returns:
            dict: dictionary of synonyms keyed by entity
        """
        d_results = self._synonym_query()

        if not d_results or not len(d_results):
            return None

        return GenerateViewSynonyms().process(d_results, reverse=True)

    @lru_cache
    def equivalents(self) -> dict[str, list[str]] | None:
        """
        Retrieves equivalent classes from an RDF graph and organizes them into a bidirectional mapping.

        This method queries an RDF graph to find pairs of classes that are marked as equivalent through the
        owl:equivalentClass property. It then constructs a dictionary where each key is a class label (a string),
        and the associated value is a list of labels (strings) for classes that are equivalent to the key class.

        Returns:
            Optional[Dict[str, list[str]]]: 
                A dictionary where:
                    - Each key is a class label (string), and
                    - The associated value is a list of labels (strings) for classes that are equivalent to the key class.
                The dictionary is bidirectional, meaning that if 'A' is equivalent to 'B', the dictionary will include
                {'A': ['B'], 'B': ['A']}.

                Returns None if no equivalent classes are found in the RDF graph.

        Example:
            If the RDF graph contains equivalent pairs (A, B) and (C, D),
            the output might be {'A': ['B'], 'B': ['A'], 'C': ['D'], 'D': ['C']}.

        Exceptions:
            This method may raise an exception if the SPARQL query execution fails (e.g., malformed query, connection error).
            In such cases, this method will catch the exception, log an appropriate message, and return None.

        Notes:
            - The equivalence relation is assumed to be symmetric, meaning that if A is equivalent to B, B is also equivalent to A.
            - The method ensures the uniqueness of equivalent classes for each key.
        """
        sparql = '''
        SELECT 
            ?a 
            ?b
        WHERE 
        {
            ?a  owl:equivalentClass ?b ;
                rdfs:label ?a_label .
            ?b rdfs:label ?b_label .
        }
        '''

        try:
            d_results = self._execute_query(
                sparql=sparql,
                to_lowercase=True,
                result_type=QueryResultType.DICT_OF_STR2LIST,
            )
        except Exception as e:
            # Log the exception with an appropriate message
            self.logger.error(f"SPARQL query execution failed: {e}")
            return None

        if not d_results:
            return None

        # ensure bidirectional equivalence
        d_bidir = defaultdict(set)
        for k, values in d_results.items():
            for v in values:
                d_bidir[k].add(v)
                d_bidir[v].add(k)

        # convert sets to lists
        return {k: list(v) for k, v in d_bidir.items()}

    @lru_cache
    def spans(self) -> dict | None:
        """ Entity Spans for Long-Range Matching

        Reference:
            https://github.com/craigtrim/askowl/issues/5

        Returns:
            dict: dictionary of spans keyed by entity name
        """
        # sparql = 'SELECT ?a ?b WHERE { { ?a rdfs:label ?b } UNION { ?a rdfs:seeAlso ?b } }'
        sparql = """
        SELECT ?a ?b
        WHERE 
        {
            { ?a rdfs:label ?b } 
            UNION 
            { ?a rdfs:seeAlso ?b } 
            UNION 
            { ?a skos:altLabel ?b } 
            UNION 
            { ?a :inflection ?b }
        }
        """

        d_results = self._execute_query(
            sparql=sparql,
            to_lowercase=True,
            result_type=QueryResultType.DICT_OF_STR2LIST,
        )

        if not d_results or not len(d_results):
            return None

        d_merged = defaultdict(list)

        def merge(d: dict) -> None:
            if not d:
                return None

            # Change Log:
            # https://github.com/craigtrim/owl-parser/issues/7
            # Ensuring output dict is str:list[str]
            for k in d:
                [d_merged[k].append(x) for x in d[k]]

        merge(GeneratePlusSpans().process(d_results))
        merge(GenerateViewSpans().process(d_results))

        d_merged = dict(d_merged)

        # -----------------------------------------------------------------------------
        # Purpose:  Eliminate Leading Spaces in Keys
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
        #           issuecomment-2435940321
        # Updated:  24-Oct-2024
        # -----------------------------------------------------------------------------
        d_merged = {
            k.strip(): d_merged[k]
            for k in d_merged
        }
        # -----------------------------------------------------------------------------

        if isEnabledForDebug(self.logger):
            Enforcer.is_dict_of_list_of_dicts(d_merged)

        return d_merged
