#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Perform the RDF Query """


from collections import defaultdict

from mutato.core import configure_logging
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.plugins.sparql.processor import SPARQLResult
from mutato.finder.singlequery.dto import QueryResultType

class OwlQueryExtract(object):
    """ Perform the RDF Query """

    def __init__(self,
                 graph: Graph):
        """ Change Log

        Created:
            13-Oct-2021
            craigtrim@gmail.com
            *   refactored out of 'owl-data-extract'
                Build Owl2PY dictionary for backwardCompatibilityTypes
        Updated:
            2-Feb-2022
            craigtrim@gmail.com
            *   do not split designated string datatypes
                https://github.com/craigtrim/askowl/issues/3
        Updated:
            25-May-2022
            craigtrim@gmail.com
            *   refactor into 'ask-owl' repo
                https://github.com/craigtrim/askowl/issues/1
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   expose ability to lowercase output
                https://github.com/craigtrim/askowl/issues/4
        Updated:
            26-May-2024
            ctrim@maryville.edu
            *   use str(value) instead of value.title()
                https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2132567127
        Updated:
            13-Dec-2024
            ctrim@maryville.edu
            *   handle blank-nodes (BNodes)
                https://github.com/Maryville-University-DLX/transcriptiq/issues/439

        Args:
            graph (Graph): an instantiated RDF graph
        """
        self.logger = configure_logging(__name__)
        self._graph = graph

    def _log_no_rows_found(self,
                           query_type: QueryResultType) -> None:
        self.logger.debug(
            f"Result Set Transformation Failure: No Rows Found (Transform: {query_type.name})")

    def _transform(self,
                   value: object,
                   to_lowercase: bool,
                   iteration_count: int = 0) -> str | list[str]:

        if isinstance(value, URIRef):
            value = str(value).split('#')[-1].strip()

            if to_lowercase:
                value = value.lower()
            return value

        elif isinstance(value, Literal):
            value = str(value).strip()
            if to_lowercase:
                value = value.lower()
            return value

        elif isinstance(value, BNode):
            self.logger.debug(f"Encountered Blank Node: {value}")

            # -----------------------------------------------------------------------------
            # Purpose:  Recursively Traverse the Blank Node (owl:intersectionOf)
            # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/439
            # Updated:  13-Dec-2024
            # -----------------------------------------------------------------------------
            contents = []
            for _, o in self._graph.predicate_objects(subject=value):

                result: str | list[str] = self._transform(
                    value=o,
                    to_lowercase=to_lowercase,
                    iteration_count=iteration_count + 1
                )

                if isinstance(result, list):
                    [
                        contents.append(x) for x in result
                    ]
                else:
                    contents.append(result)

            return contents

        else:
            self.logger.error(f"DataType Not Recognized: {type(value)}")
            raise NotImplementedError

    def _list_of_strings(self,
                         query_results: SPARQLResult,
                         to_lowercase: bool) -> list:
        results = []

        rows = [x for x in query_results if len(x) >= 1]

        if not len(rows):
            self._log_no_rows_found(QueryResultType.LIST_OF_STRINGS)
            return None

        for row in rows:

            value: str | list[str] = self._transform(row[0], to_lowercase)
            if isinstance(value, list):
                [
                    results.append(x) for x in value
                ]
            else:
                results.append(value)

        return results

    def _dict_of_str2str(self,
                         query_results: SPARQLResult,
                         to_lowercase: bool) -> dict:
        d = {}

        rows = [x for x in query_results if len(x) >= 2]
        if not len(rows):
            self._log_no_rows_found(QueryResultType.DICT_OF_STR2STR)
            return None

        for row in rows:
            keys: list[str] = self._transform(row[0], to_lowercase)

            if not isinstance(keys, list):
                keys = [keys]

            value: str | list[str] = self._transform(row[1], to_lowercase)

            for key in keys:
                if isinstance(value, list):
                    [
                        d[key].append(x) for x in value
                    ]

                else:
                    d[key] = value

        return d

    def _dict_of_str2list(self,
                          query_results: SPARQLResult,
                          to_lowercase: bool) -> dict:
        d = defaultdict(list)

        rows = [x for x in query_results if len(x) >= 2]
        if not len(rows):
            self._log_no_rows_found(QueryResultType.DICT_OF_STR2LIST)
            return None

        for row in rows:

            keys: list[str] = self._transform(row[0], to_lowercase)
            value: str | list[str] = self._transform(row[1], to_lowercase)

            if not isinstance(keys, list):
                keys = [keys]

            for key in keys:
                if isinstance(value, list):
                    [d[key].append(x) for x in value]
                else:
                    d[key].append(value)

        return dict(d)

    def _update(self,
                query_results: SPARQLResult,
                to_lowercase: bool,
                result_type: QueryResultType) -> object:

        if result_type == QueryResultType.LIST_OF_STRINGS:
            return self._list_of_strings(query_results, to_lowercase)

        elif result_type == QueryResultType.DICT_OF_STR2STR:
            return self._dict_of_str2str(query_results, to_lowercase)

        elif result_type == QueryResultType.DICT_OF_STR2LIST:
            return self._dict_of_str2list(query_results, to_lowercase)

        else:
            raise NotImplementedError

    def process(self,
                query: str,
                to_lowercase: bool,
                result_type: QueryResultType) -> dict:
        try:

            result = self._graph.query(query)
            if result_type == QueryResultType.DO_NOT_TRANSFORM:
                return result

            svcresult = self._update(
                query_results=result,
                to_lowercase=to_lowercase,
                result_type=result_type)

            return svcresult
        except Exception as e:
            self.logger.error(f"Parsing Exception (Query={query})")
            raise ValueError('OWL Query Failed')
