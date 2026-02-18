#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Filter Extracted Candidate Sequences """


from mutato.core import configure_logging, Stopwatch, isEnabledForDebug

class SlidingWindowBlacklist(object):
    """ Filter Extracted Candidate Sequences """

    def __init__(self,
                 candidates: list,
                 gram_size: int,
                 blacklist: list):
        """
        Created:
            8-Oct-2021
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/14#issuecomment-939029052
        """
        self.logger = configure_logging(__name__)
        self._gram_size = gram_size
        self._blacklist = blacklist
        self._candidates = candidates

    def _process(self) -> list:
        filtered = []

        for candidate in self._candidates:

            normalized_text = ' '.join([
                x['normal']
                for x in candidate
            ]).strip().lower()
            
            if normalized_text not in self._blacklist:
                filtered.append(candidate)

        return filtered

    def process(self) -> list:
        sw = Stopwatch()

        results = self._process()

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Sliding Window Blacklist Completed for gram-size {self._gram_size} in {str(sw)}")

        return results
