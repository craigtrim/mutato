#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Filter Extracted Candidate against known KBs """


from mutato.core import configure_logging, Stopwatch, isEnabledForDebug

class SlidingWindowLookup(object):
    """ Filter Extracted Candidate against known KBs """

    def __init__(self,
                 candidates: list,
                 gram_size: int,
                 d_runtime_kb: dict):
        """ Change Log:

        Created:
            8-Oct-2021
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/14#issuecomment-939029052
        Updated:
            22-Jan-2025
            ctrim@maryville.edu
            *   Check for int(gram-size) and str(gram-size)
                https://github.com/Maryville-University-DLX/transcriptiq/issues/513

        Args:
            candidates (list): _description_
            gram_size (int): _description_
            d_runtime_kb (dict): _description_
        """
        self.logger = configure_logging(__name__)
        self._gram_size = gram_size
        self._candidates = candidates

        def get_runtime_kb() -> dict:
            # -----------------------------------------------------------------------------
            # Purpose:  Check for int(gram-size) and str(gram-size)
            # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/513
            # Updated:  22-Jan-2025
            # -----------------------------------------------------------------------------
            if self._gram_size in d_runtime_kb:
                return d_runtime_kb[self._gram_size]
            if str(self._gram_size) in d_runtime_kb:
                return d_runtime_kb[str(self._gram_size)]

        self._d_runtime_kb = get_runtime_kb()

    def _process(self) -> list:
        filtered = []
        for token in self._candidates:
            normal = ' '.join([x['normal'] for x in token]).lower()

            if normal in self._d_runtime_kb:
                filtered.append(token)

        return filtered

    def process(self) -> list | None:
        sw = Stopwatch()

        results = self._process()

        if not len(results):
            if isEnabledForDebug(self.logger):
                self.logger.debug(
                    f"Sliding Window Lookup Completed for gram-size {self._gram_size} with no results in {str(sw)}")
            return None

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Sliding Window Lookup Completed for gram-size {self._gram_size} with {len(results)} results in {str(sw)}")

        return results
