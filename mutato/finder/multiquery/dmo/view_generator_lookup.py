#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" View Generator: Lookup Spans using N-Gram Input """


from mutato.core import configure_logging, Stopwatch, isEnabledForDebug
from mutato.finder.multiquery.dmo.span import OwlSpanAugment, OwlSpanGenerate

class ViewGeneratorLookup(object):
    """ View Generator: Lookup Spans using N-Gram Input """

    def __init__(self):
        """ Change Log

        Created:
            26-May-2022
            craigtrim@gmail.com
            *   https://github.com/grafflr/ask-owl/issues/4
        Created:
            30-May-2022
            craigtrim@gmail.com
            *   migrated from 'askowl' into 'deepnlu'
                https://github.com/grafflr/deepnlu/issues/21#issuecomment-1141518333
        """
        self.logger = configure_logging(__name__)

    @staticmethod
    def _sort(tokens: list) -> list:
        values = sorted(set(tokens), key=len)
        values.reverse()
        return values

    def process(self,
                d_results: dict) -> dict:

        sw = Stopwatch()

        d_results = OwlSpanGenerate().process(d_results)
        d_results = OwlSpanAugment().process(d_results)

        d_results[1] = self._sort(d_results[1])
        d_results[2] = self._sort(d_results[2])
        d_results[3] = self._sort(d_results[3])
        d_results[4] = self._sort(d_results[4])
        d_results[5] = self._sort(d_results[5])
        d_results[6] = self._sort(d_results[6])

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Generated {len(d_results)} OWL Spans in {str(sw)}")

        return d_results
