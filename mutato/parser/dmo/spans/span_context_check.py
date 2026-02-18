#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Filter Candidate Span Matches by Context """


from mutato.core import configure_logging, Stopwatch, isEnabledForDebug

class SpanContextCheck(object):
    """Filter Candidate Span Matches by Context

    Phase 3 in
        GRAFFL-CORE-0077#issuecomment-947342784

    Notes:
    -   Each candidate may optionally have a context that is required for the match.

    -   For example, this rule
            alpha+beta!gamma

        implies that alpha and beta can form a long-distance match,
            but for this match to be valid,
                'gamma' is a token that must be found in the context
    """

    def __init__(self,
                 d_rules: dict):
        """
        Created:
            20-Oct-2021
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/70
        """
        self.logger = configure_logging(__name__)
        self._d_rules = d_rules

    def _process(self,
                 tokens: list) -> list:

        normal = None

        matching_rules = []
        for d_rule in self._d_rules:

            def has_context_requirement() -> bool:
                if 'context' not in d_rule:
                    return False
                if not len(d_rule['context']):
                    return False
                return True

            if not has_context_requirement():
                matching_rules.append(d_rule)
                continue

            if not normal:
                normal = [x['normal'] for x in tokens]

            def has_context_match() -> bool:
                for token in d_rule['context']:
                    if token not in normal:
                        return False

                return True

            if has_context_match():
                matching_rules.append(d_rule)

        return matching_rules

    def process(self,
                tokens: list) -> list:

        sw = Stopwatch()

        matching_rules = self._process(tokens)

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Span Context Check Completed for {len(matching_rules)} rules in {str(sw)}")

        return matching_rules
