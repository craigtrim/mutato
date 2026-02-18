#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Use Token Hierarchies to Find Matches """


from mutato.parser.dmo import SlidingWindowExtract
from mutato.core import configure_logging, Stopwatch, Enforcer, isEnabledForDebug

class HierarchyMatchFinder(object):
    """ Use Token Hierarchies to Find Matches """

    def __init__(self):
        """
        Created:
            14-Feb-2022
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/188
        """
        self.logger = configure_logging(__name__)

    def _filter(self,
                window: list) -> list:
        results = []

        for candidates in window:

            # print ("candidates: ---> ", [x['normal'] for x in candidates])

            def is_valid(d_token: dict) -> bool:

                # from pprint import pprint
                # print ('\n'*3)
                # pprint (d_token)
                # print ('\n'*3)

                if 'ancestors' in d_token and len(d_token['ancestors']):
                    return True

                if 'descendants' in d_token and len(d_token['descendants']):
                    return True

                if 'swaps' in d_token:

                    if isEnabledForDebug(self.logger):
                        Enforcer.is_str(d_token['swaps']['type'])

                    if d_token['swaps']['type'] == 'hierarchy':
                        return False

                    for child in d_token['swaps']['tokens']:

                        if isEnabledForDebug(self.logger):
                            Enforcer.is_dict(child)

                        if 'ancestors' in child and len(child['ancestors']):
                            return True

                        if 'descendants' in child and len(child['descendants']):
                            return True

                # print ("is not valid ... ", d_token['normal'])
                return False

            has_valid_tokens = len([token for token
                                    in candidates if is_valid(token)])

            if has_valid_tokens:
                results.append(candidates)

        return results

    def _process(self,
                 tokens: list,
                 gram_size: int) -> list:

        window = SlidingWindowExtract(
            tokens=tokens,
            gram_size=gram_size).process()

        return self._filter(window)

    def process(self,
                tokens: list,
                gram_size: int) -> list:
        Enforcer.is_list(tokens)

        sw = Stopwatch()

        swaps = self._process(tokens=tokens,
                              gram_size=gram_size)

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Hierarchy Match Finding Completed in {str(sw)}")

        return swaps
