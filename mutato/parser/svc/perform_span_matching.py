#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Perform Span Matching """


from mutato.core import (
    Stopwatch,
    Enforcer,
    configure_logging,
    isEnabledForDebug,
    isEnabledForInfo
)
from mutato.finder.multiquery.bp import FindOntologyData
from mutato.parser.dmo import SpanMatchFinder, SpanMatchSwapper


class PerformSpanMatching(object):
    """Perform Span Matching

    Sample Input:
        the history of nursing

    Sample Rule:
        nursing_history ~ nurse+history

    Sample Match:
        "history of nursing" == nursing_history

    Sample Output:
        the nursing_history
    """

    def __init__(self,
                 find_ontology_data: FindOntologyData):
        """ Change Log

        Created:
            20-Oct-2021
            craigtrim@gmail.com
            *   GRAFFL-CORE-0077
        Updated:
            26-May-2022
            craigtrim@gmail.com
            *   treat 'ontologies' param as a list
                https://github.com/grafflr/deepnlu/issues/7
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   remove 'ontologies' and integrate 'find-ontology-data'
                https://github.com/grafflr/deepnlu/issues/13
        Updated:
            1-Aug-2023
            craigtrim@gmail.com
            *   choose optimal rule when multiple rules exist
                https://bast-ai.atlassian.net/browse/COR-137

        Args:
            find_ontology_data (FindOntologyData): an instantiation of this object
        """
        self.logger = configure_logging(__name__)
        self._span_match_finder = SpanMatchFinder(
            d_spans=find_ontology_data.spans(),
            span_keys=find_ontology_data.span_keys()).process
        self._span_match_swapper = SpanMatchSwapper(find_ontology_data)

    def _process(self,
                 tokens: list) -> list:

        matching_rules = self._span_match_finder(tokens)
        if not matching_rules or not len(matching_rules):
            return tokens

        # COR-137-10660
        if len(matching_rules) > 1:

            # Use the max function with a key that counts the number of underscores in the canon attribute
            matching_rules = [
                max(
                    matching_rules,
                    key=lambda rule: rule['canon'].count('_')
                )
            ]

        tokens = self._span_match_swapper.process(
            tokens=tokens,
            matching_rules=matching_rules)

        return tokens

    def process(self,
                tokens: list) -> list:

        if isEnabledForInfo(self.logger):
            sw = Stopwatch()
            Enforcer.is_list(tokens)

        swaps = self._process(tokens)

        if isEnabledForDebug(self.logger):
            self.logger.debug(f"Span Swapping Completed in {str(sw)}")

        return swaps
