#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Perform Synonym Swapping with Spanned Matches """


from mutato.core import configure_logging
from mutato.parser.dmo.core import SwapTokenGenerator
from mutato.finder.multiquery.bp import FindOntologyData

class SpanMatchSwapper(object):
    """ Perform Synonym Swapping with Spanned Matches """

    def __init__(self,
                 find_ontology_data: FindOntologyData):
        """ Change Log

        Created:
            20-Oct-2021
            craigtrim@gmail.com
            *   renamed from 'perform-sliding-window'
                GRAFFL-CORE-0077
        Updated:
            1-Feb-2022
            craigtrim@gmail.com
            *   pass 'ontologies' as list param
                https://github.com/grafflr/graffl-core/issues/135#issuecomment-1027464370
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   remove 'ontologies' and integrate 'find-ontology-data'
                https://github.com/grafflr/deepnlu/issues/13

        Args:
            find_ontology_data (FindOntologyData): an instantiation of this object
        """
        self.logger = configure_logging(__name__)
        self._find_ner = find_ontology_data.find_ner
        self._create_swap = SwapTokenGenerator(
            find_ontology_data.ontologies()).process

    def process(self,
                tokens: list,
                matching_rules: list) -> list:

        for matching_rule in matching_rules:

            x = matching_rule['positions'][0]
            y = matching_rule['positions'][-1] + 1

            subset = tokens[x:y]

            canon = matching_rule['canon']

            def normal() -> str:
                # ----------------------------------------------------------
                # Purpose:    The 'canonical' form is the appropriate normal form
                # Reference:  https://github.com/grafflr/graffl-core/issues/20#issuecomment-940678237
                # ----------------------------------------------------------
                return canon

            def ner() -> str:
                # ----------------------------------------------------------
                # Purpose:
                # Reference:  https://github.com/grafflr/graffl-core/issues/35#issuecomment-949986993
                # ----------------------------------------------------------
                return self._find_ner(canon)

            d_swap = self._create_swap(normal=normal(),
                                       canon=canon,
                                       ner=ner(),
                                       tokens=subset,
                                       swap_type='spans')

            normalized = tokens[:x]
            normalized.append(d_swap)
            [normalized.append(x) for x in tokens[y:]]

            return normalized
