#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Query the in-memory Ontology Model """


from collections import defaultdict

from rdflib import Graph
from mutato.finder.singlequery.dmo import OwlQueryExtract
from mutato.finder.singlequery.dto import QueryResultType
from mutato.core import configure_logging, Stopwatch, isEnabledForDebug

class QueryOntologyModel(object):
    """ Query the in-memory Ontology Model """

    def __init__(self,
                 graph: Graph):
        """ Change Log

        Created:
            25-May-2022
            craigtrim@gmail.com
            *   https://github.com/craigtrim/askowl/issues/1
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   expose ability to lowercase output
                https://github.com/craigtrim/askowl/issues/4
        Updated:
            22-Jan-2025
            ctrim@maryville.edu
            *   add 'nill' filter
                https://github.com/Maryville-University-DLX/transcriptiq/issues/512

        Args:
            graph (Graph): the instantiated RDF graph
        """
        self.logger = configure_logging(__name__)
        self._execute_query = OwlQueryExtract(graph).process

    @staticmethod
    def _reverse_order(d_results: dict,
                       result_type: QueryResultType) -> dict:

        if result_type == QueryResultType.DICT_OF_STR2LIST:
            d_rev = defaultdict(list)
            for k in d_results:
                for v in d_results[k]:
                    d_rev[v].append(k)
            return dict(d_rev)

        raise NotImplementedError

    def process(self,
                sparql: str,
                result_type: QueryResultType,
                reverse: bool = False,
                to_lowercase: bool = True) -> dict | list:
        """ Execute a SPARQL query on the RDF Graph

        Args:
            sparql (str): the SPARQL query to execute
            result_type (QueryResultType): the type of transformation to perform on the result set
            reverse (bool, optional): reverses the subject/object order. Defaults to False.
                if "?x implies ?y" and reverse=False
                    the results will be { ?x: [?y-1, ?y-2, ..., ?y-N]}
                if "?x implies ?y" and reverse=True
                    the results will be { ?y-1: [x], ?y-2: [x], ?y-N: [x]}
            to_lowercase (bool, optional): Ensures all output is lower-cased. Defaults to True.

        Returns:
            dict or list: the result set
        """

        sw = Stopwatch()

        d_results = self._execute_query(
            query=sparql,
            to_lowercase=to_lowercase,
            result_type=result_type
        )

        if not d_results or not len(d_results):
            if isEnabledForDebug(self.logger):
                self.logger.debug(
                    f"Ontology Model Service Completed: (No Results Found) in {str(sw)}")
            return None

        # -----------------------------------------------------------------------------
        # Purpose:  Filter out 'nil' instances
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/512
        # Updated:  22-Jan-2025
        # -----------------------------------------------------------------------------
        def isnn(value: any) -> bool:  # is-not-nil
            return value and str(value) not in ['nil']
        # -----------------------------------------------------------------------------
        if result_type == QueryResultType.DICT_OF_STR2LIST:
            d_results = {
                key: [
                    value for value in d_results[key] if isnn(value)
                ] for key in d_results if isnn(key)
            }
        elif result_type == QueryResultType.DICT_OF_STR2STR:
            d_results = {
                key: d_results[key] for key in d_results
                if isnn(key) and isnn(d_results[key])
            }
        elif result_type == QueryResultType.LIST_OF_STRINGS:
            d_results = [
                result for result in d_results
                if isnn(result)
            ]
        # -----------------------------------------------------------------------------

        if reverse:
            d_results = self._reverse_order(
                d_results=d_results,
                result_type=result_type)

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Ontology Model Service Completed: ({len(d_results)}) for {sparql} in {str(sw)}")

        return d_results
