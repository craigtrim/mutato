#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Extract Tokens using a Sliding Window Algorithm """


from mutato.core import configure_logging, Stopwatch, isEnabledForDebug

class SlidingWindowExtract(object):
    """ Extract Tokens using a Sliding Window Algorithm """

    def __init__(self,
                 tokens: list,
                 gram_size: int):
        """
        Created:
            6-Oct-2021
            craigtrim@gmail.com
            *   GRAFFL-CORE-0004
        """
        self.logger = configure_logging(__name__)
        self._tokens = tokens
        self._gram_size = gram_size

    def _process(self) -> list:
        results = []
        tokens = self._tokens

        if self._gram_size == len(tokens):
            return [tokens]

        if self._gram_size == 1:
            return [[x] for x in tokens]

        x = 0
        y = x + self._gram_size

        while y <= len(tokens):
            results.append(tokens[x: y])

            x += 1
            y = x + self._gram_size

        return results

    def process(self) -> list:
        sw = Stopwatch()

        results = self._process()

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Sliding Window Extract Completed for gram-size {self._gram_size} with {len(results)} results in {str(sw)}")

        return results
