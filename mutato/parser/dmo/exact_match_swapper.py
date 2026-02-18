#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Perform Synonym Swapping with Exact Matches """


from mutato.parser.dmo.core import SwapTokenGenerator
from mutato.finder.multiquery.bp import FindOntologyData
from mutato.core import configure_logging, Enforcer, isEnabledForDebug

class ExactMatchSwapper(object):
    """ Perform Synonym Swapping with Exact Matches """

    def __init__(self,
                 find_ontology_data: FindOntologyData):
        """ Change Log

        Created:
            6-Oct-2021
            craigtrim@gmail.com
            *   GRAFFL-CORE-0004
        Updated:
            20-Oct-2021
            craigtrim@gmail.com
            *   renamed from 'perform-synonym-swapping'
                GRAFFL-CORE-0077
        Updated:
            1-Feb-2022
            craigtrim@gmail.com
            *   pass 'ontologies' as list param
                https://github.com/grafflr/graffl-core/issues/135#issuecomment-1027464370
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   remove all params in place of 'find-ontology-data'
                https://github.com/grafflr/deepnlu/issues/13
        Updated:
            25-Nov-2022
            craigtrim@gmail.com
            *   instead of passing 'lists-of-lists-of-tokens' just pass 'list-of-tokens', in pursuit of
                https://github.com/craigtrim/owl-parser/issues/1
        Updated:
            7-Jul-2024
            ctrim@maryville.edu
            *   fix lookup defect
                https://github.com/Maryville-University-DLX/transcriptiq/issues/113

        Args:
            find_ontology_data (FindOntologyData): an instantiation of this object
        """
        self.logger = configure_logging(__name__)
        self._find_ner = find_ontology_data.find_ner
        self._find_canon = find_ontology_data.find_canon
        self._find_variants = find_ontology_data.find_variants
        self._create_swap = SwapTokenGenerator(
            find_ontology_data.ontologies()).process

    def process(self,
                tokens: list) -> list:

        normal = [x['normal'] for x in tokens]

        # ----------------------------------------------------------
        # Purpose:  Do NOT use underscores to concatenate tokens
        # Issue:    https://github.com/grafflr/graffl-core/issues/35
        #           issuecomment-949988463
        #
        # input_text = '_'.join(normal).strip().lower()
        input_text: str = ' '.join(normal).strip().lower()
        # ----------------------------------------------------------

        canon = self._find_canon(input_text)

        # -----------------------------------------------------------------------------
        # Purpose:  Replace Underscores to Find Canonical Form
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/113
        #           issuecomment-2218406437
        # Updated:  7-Jul-2024
        if not canon or not len(canon):
            if '_' in input_text or "'" in input_text:
                canon = self._find_canon(
                    input_text
                    .replace('_', ' ')
                    .replace("'", '')
                )
        # -----------------------------------------------------------------------------

        if isEnabledForDebug(self.logger):
            Enforcer.is_optional_str(canon)

        if not canon:
            self.logger.error(
                f"Canonical Form Not Found: (input-tokens={input_text})")
            raise ValueError

        def normal() -> str:
            # ----------------------------------------------------------
            # Purpose:    The 'canonical' form is the appropriate normal form
            # Reference:  https://github.com/grafflr/graffl-core/issues/20#issuecomment-940678237
            # ----------------------------------------------------------
            return canon

        def ner() -> str:
            # ----------------------------------------------------------
            # Purpose:    Construct the NER tag
            # Reference:  https://github.com/grafflr/graffl-core/issues/35#issuecomment-949988463
            # ----------------------------------------------------------
            # return self._find_ner(canon)
            # ----------------------------------------------------------
            return None

        return self._create_swap(canon=canon,
                                 normal=normal(),
                                 ner=ner(),
                                 tokens=tokens,
                                 swap_type='exact')
