# !/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Merge Multiple Model results into a single and cohesive structure """


from collections import defaultdict

from mutato.core import configure_logging
from mutato.finder.singlequery.dto import QueryResultType

class ModelResultMerge(object):
    """ Merge Multiple Model results into a single and cohesive structure """

    def __init__(self):
        """ Change Log

        Created:
            26-May-2022
            craigtrim@gmail.com
            *   https://github.com/grafflr/deepnlu/issues/2
        Updated:
            24-Nov-2022
            craigtrim@gmail.com
            *   sort the merged output
                https://github.com/craigtrim/owl-finder/issues/3
        """
        self.logger = configure_logging(__name__)

    def _merge(self,
               results: list,
               result_type: QueryResultType) -> dict:

        results = [x for x in results if x is not None and len(x)]

        if result_type == QueryResultType.DICT_OF_STR2LIST:
            d_merge = defaultdict(list)
            for d_result in results:
                for k in d_result:
                    if k not in d_merge:
                        d_merge[k] = []

                    for value in d_result[k]:
                        if value not in d_merge[k]:
                            d_merge[k].append(value)

            return dict(d_merge)

        elif result_type == QueryResultType.DICT_OF_STR2DICT:
            d_merge = defaultdict(list)
            for d_result in results:
                for k in d_result:
                    for value in d_result[k]:
                        d_merge[k].append(value)

            return dict(d_merge)

        else:
            raise NotImplementedError

    def process(self,
                results: list,
                result_type: QueryResultType) -> list:

        d_model = self._merge(
            results=results,
            result_type=result_type)

        # Sort by Alpha
        # Reference https://github.com/craigtrim/owl-finder/issues/3
        d_sorted = {k: sorted(set(d_model[k]), reverse=False) for k in d_model}

        return d_sorted
