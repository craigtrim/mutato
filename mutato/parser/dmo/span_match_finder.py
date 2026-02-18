#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Find Candidate Span Matches """


from mutato.parser.dmo.spans import SpanContentCheck
from mutato.parser.dmo.spans import SpanContextCheck
from mutato.parser.dmo.spans import SpanDistanceCheck
from mutato.core import configure_logging, Stopwatch, isEnabledForDebug

class SpanMatchFinder(object):
    """ Find Candidate Span Matches

    The Span Match Pipeline is documented here
        GRAFFL-CORE-0077#issuecomment-947342784 """

    def __init__(self,
                 d_spans: dict,
                 span_keys: list):
        """_summary_

        Created:
            20-Oct-2021
            craigtrim@gmail.com
            *   renamed from 'perform-sliding-window'
                GRAFFL-CORE-0077
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   pass in-memory dictionaries in pursuit of
                https://github.com/grafflr/deepnlu/issues/13

        Args:
            d_spans (dict): full dictionary of span data
            span_keys (list): span dictionary keys sorted by length
        """
        self.logger = configure_logging(__name__)
        self._d_spans = d_spans
        self._span_keys = span_keys

    def _process(self,
                 tokens: list) -> list:

        # ----------------------------------------------------------
        # Find Candidate Spans via Content Matching
        # ----------------------------------------------------------
        matching_rules = SpanContentCheck(
            d_rules=self._d_spans,
            rule_keys=self._span_keys).process(tokens)

        if not matching_rules or not len(matching_rules):
            return None

        # ----------------------------------------------------------
        # Filter Candidate Spans via Distance Analysis
        # ----------------------------------------------------------
        matching_rules = SpanDistanceCheck(
            d_rules=matching_rules).process(tokens)

        if not matching_rules or not len(matching_rules):
            return None

        # ----------------------------------------------------------
        # Filter Candidate Spans via Context Analysis
        # ----------------------------------------------------------
        matching_rules = SpanContextCheck(
            d_rules=matching_rules).process(tokens)

        if not matching_rules or not len(matching_rules):
            return None

        return matching_rules

    def process(self,
                tokens: list) -> list:
        sw = Stopwatch()

        results = self._process(tokens)

        if isEnabledForDebug(self.logger):

            def total_results() -> int:
                if results:
                    return len(results)
                return 0

            self.logger.debug(
                f"Span Match Finder Completed: ({total_results}) in {str(sw)}")

        return results
