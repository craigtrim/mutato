#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Perform Sliding Window Extraction for Candidate Synonym Swapping """


from mutato.core import configure_logging, EnvIO, Stopwatch, isEnabledForInfo, isEnabledForDebug
from mutato.parser.dmo.exact import SlidingWindowExtract, SlidingWindowBlacklist, SlidingWindowLookup
from mutato.parser.dto import d_candidate_synonym_blacklist

class ExactMatchFinder(object):
    """ Perform Sliding Window Extraction for Candidate Synonym Swapping """

    def __init__(self,
                 gram_size: int,
                 d_lookup: dict):
        """
        Created:
            8-Oct-2021
            craigtrim@gmail.com
            *   GRAFFL-CORE-0004
        Updated:
            20-Oct-2021
            craigtrim@gmail.com
            *   renamed from 'perform-sliding-window'
                GRAFFL-CORE-0077
        """
        self.logger = configure_logging(__name__)
        self._d_lookup = d_lookup
        self._gram_size = gram_size
        self._lookup_keys = list(self._d_lookup.keys())

    def _process(self,
                 tokens: list) -> list:

        # -----------------------------------------------------------------------------
        # Purpose:  Must Check int(gram-size) and str(gram-size)
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/513
        #           ssuecomment-2608665973
        # -----------------------------------------------------------------------------
        gram_size_exists: bool = self._gram_size in self._d_lookup or \
            str(self._gram_size) in self._lookup_keys
        # -----------------------------------------------------------------------------

        # check if valid synonyms or entities exist at this gram size level
        if not gram_size_exists:

            # ... then there is no point in proceeding any further
            return None

        candidates = SlidingWindowExtract(
            tokens=tokens,
            gram_size=self._gram_size).process()

        if not candidates or not len(candidates):
            return None

        if self._gram_size == 1:
            candidates = [
                x for x in candidates
                if len([
                    token for token in x
                    if 'swaps' not in token
                ])
            ]

        if EnvIO.is_true('SLIDING_WINDOW_BLACKLIST'):  # optional step; defaults to False
            if self._gram_size in d_candidate_synonym_blacklist:
                blacklist = d_candidate_synonym_blacklist[self._gram_size]

                candidates = SlidingWindowBlacklist(
                    candidates=candidates,
                    blacklist=blacklist,
                    gram_size=self._gram_size).process()

                if not candidates or not len(candidates):
                    return None

        candidates = SlidingWindowLookup(
            candidates=candidates,
            gram_size=self._gram_size,
            d_runtime_kb=self._d_lookup).process()

        if not candidates or not len(candidates):
            return None

        return candidates

    def process(self,
                tokens: list) -> list:
        sw = Stopwatch()

        results = self._process(tokens)

        if isEnabledForInfo(self.logger):

            def total_results() -> int:
                if results:
                    return len(results)
                return 0

            if isEnabledForDebug(self.logger):
                self.logger.debug(
                    f"Sliding Window Completed gram-size={self._gram_size}, total-results={total_results()} in {str(sw)}")

        return results
