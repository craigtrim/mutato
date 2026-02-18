#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Perform Exact Matching """


from mutato.core import (
from mutato.parser.dmo import (
from mutato.finder.multiquery.bp import FindOntologyData

    Enforcer,
    Stopwatch,
    configure_logging,
    isEnabledForInfo,
    isEnabledForDebug,
)


class PerformExactMatching(object):
    """ Perform Exact Matching """

    def __init__(self,
                 find_ontology_data: FindOntologyData):
        """ Change Log

        Created:
            20-Oct-2021
            craigtrim@gmail.com
            *   refactored out of 'mutato-api'
                GRAFFL-CORE-0077
        Updated:
            26-May-2022
            craigtrim@gmail.com
            *   treat 'ontologies' param as a list
                https://github.com/grafflr/deepnlu/issues/7
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   remove all params in place of 'find-ontology-data'
                https://github.com/grafflr/deepnlu/issues/13
        Updated:
            25-Nov-2022
            craigtrim@gmail.com
            *   modify how 'exact-match-swapper' is called
                https://github.com/craigtrim/owl-parser/issues/1
        Updated:
            29-Nov-2022
            craigtrim@gmail.com
            *   perform early return in loop
                https://github.com/craigtrim/owl-parser/issues/10#issuecomment-1331531086
        Updated:
            12-Oct-2024
            ctrim@maryville.edu
            *   increase gram-size to 10
                https://github.com/Maryville-University-DLX/transcriptiq/issues/324

        Args:
            find_ontology_data (FindOntologyData): an instantiation of this object
        """
        self.logger = configure_logging(__name__)
        self._d_lookup = find_ontology_data.lookup()
        self._exact_match_swapper = ExactMatchSwapper(
            find_ontology_data).process

    def _process(self,
                 tokens: list) -> list:

        gram_size = 10  # 324
        while gram_size > 0:

            exact_match_finder = ExactMatchFinder(
                gram_size=gram_size,
                d_lookup=self._d_lookup).process

            results = exact_match_finder(tokens)

            if not results:
                gram_size -= 1
                continue

            for exact_match in results:

                d_swap = self._exact_match_swapper(exact_match)
                ids = [x['id'] for x in d_swap['swaps']['tokens']]

                merged = []
                for token in tokens:
                    if token['id'] not in ids:
                        merged.append(token)
                    elif token['id'] == ids[0]:
                        merged.append(d_swap)

                # -----------------------------------------------------------
                # Purpose:  Use Early Return
                # Issue:    https://github.com/craigtrim/owl-parser/issues/10
                #           issuecomment-1331531086
                # Updated:  29-Nov-2022
                # -----------------------------------------------------------
                return self._process(merged)

        return tokens

    def process(self,
                tokens: list) -> list:

        if isEnabledForDebug(self.logger):
            Enforcer.is_list(tokens)

        sw = Stopwatch()

        swaps = self._process(tokens)

        if isEnabledForDebug(self.logger):
            summary = SwapResultSummarizer().process(swaps)
            self.logger.debug(
                f"Exact Swapping Completed: ({summary}) in {str(sw)}")

        return swaps
