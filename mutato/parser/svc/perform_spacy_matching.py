#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Leverage spaCy NERs """


from mutato.finder.multiquery.bp import FindOntologyData
from mutato.parser.dmo import SpacyMatchFinder, SpacyMatchSwapper
from mutato.core import configure_logging, Stopwatch, Enforcer, isEnabledForDebug

class PerformSpacyMatching(object):
    """Collapse Contiguous spaCy NERs into a single entity

    Sample Input:
        and/CONJ John/PERSON Doe/PERSON said/DECL

    Sample Match:
        "John Doe" == PERSON PERSON

    Sample Output:
        and john_doe said
    """

    def __init__(self,
                 find_ontology_data: FindOntologyData):
        """ Change Log

        Created:
            22-Oct-2021
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/35
        Updated:
            29-Oct-2021
            craigtrim@gmail.com
            *   Update for Recursive Processing
                https://github.com/grafflr/graffl-core/issues/96
        Updated:
            1-Feb-2022
            craigtrim@gmail.com
            *   pass 'ontology-name' as a param
                https://github.com/grafflr/graffl-core/issues/135#issuecomment-1027468040
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

        Args:
            find_ontology_data (FindOntologyData): an instantiation of this object
        """
        self.logger = configure_logging(__name__)
        self._spacy_match_swapper = SpacyMatchSwapper(
            find_ontology_data).process

    def _process(self,
                 tokens: list) -> list:

        matching_rules = SpacyMatchFinder().process(tokens)
        if not matching_rules or not len(matching_rules):
            return tokens

        tokens = self._spacy_match_swapper(tokens=tokens,
                                           matching_rules=matching_rules)

        return self._process(tokens)  # graffl-core-96-954953141

    def process(self,
                tokens: list) -> list:

        if isEnabledForDebug(self.logger):
            Enforcer.is_list(tokens)

        sw = Stopwatch()

        swaps = self._process(tokens)

        if isEnabledForDebug(self.logger):
            self.logger.debug(f"spaCy Swapping Completed in {str(sw)}")

        return swaps
