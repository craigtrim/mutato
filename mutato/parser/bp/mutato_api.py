#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Mutato API """


import spacy
from mutato.parser.svc import (
from spacy.lang.en import English
from lingpatlab import SpacyResult, LingPatLab, Sentence
from mutato.finder.multiquery.bp import FindOntologyData, FindOntologyJSON
from mutato.core import Stopwatch, Enforcer, configure_logging, isEnabledForDebug

    AugmentTokenHierarchy,
    PerformExactMatching,
    PerformHierarchyMatching,
    PerformSpanMatching
)


class MutatoAPI(object):
    """ Mutato API """

    __lingpat_api: LingPatLab = None

    def __init__(self,
                 find_ontology_data: FindOntologyData | FindOntologyJSON,
                 en_spacy_model: English | None = None):
        """ Change Log

        Created:
            6-Oct-2021
            craigtrim@gmail.com
            *   GRAFFL-CORE-0004
        Updated:
            1-Feb-2022
            craigtrim@gmail.com
            *   a finder initialization is a contract
                GRAFFL-CORE-0135
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
        Updated:
            28-Nov-2022
            craigtrim@gmail.com
            *   check if Ontology data actually exists
                https://github.com/craigtrim/owl-finder/issues/5
        Updated:
            26-May-2024
            ctrim@maryville.edu
            *   add 'swap-input-text' and rename 'swap' to 'swap-input-tokens'
                https://github.com/Maryville-University-DLX/transcriptiq/issues/19#issuecomment-2132417516

        Args:
            find_ontology_data (FindOntologyData): an instantiation of this object
        """
        self.logger = configure_logging(__name__)
        if not find_ontology_data.lookup():
            raise ValueError('Empty Ontology')

        self._finder = find_ontology_data

        if en_spacy_model is not None:
            self._en_spacy_model = en_spacy_model
        else:
            self._en_spacy_model = spacy.load('en_core_web_sm')

        self._perform_exact_matching = PerformExactMatching(
            find_ontology_data).process

        self._perform_span_matching = PerformSpanMatching(
            find_ontology_data).process

        self._perform_hierarchal_matching = PerformHierarchyMatching(
            find_ontology_data).process

        self._augment_hierarchy = AugmentTokenHierarchy(
            find_ontology_data).process

        # ----------------------------------------------------------
        # Change Log:
        # 20220214  Disable Environment Check
        # 20220228  GRAFFL-CORE-0205
        # self._perform_spacy_matching = PerformSpacyMatching(
        #     find_ontology_data).process
        # ----------------------------------------------------------

    def swap_input_text(self,
                        input_text: str,
                        ctr: int = 0) -> list | None:
        """
        Perform synonym swapping on the given input text.

        Args:
            input_text (str): The input text to perform synonym swapping on.
            ctr (int, optional): The counter to keep track of the number of recursive calls. Defaults to 0.

        Returns:
            list: The list of tokens after performing synonym swapping.

        """

        if not input_text or not isinstance(input_text, str) or not len(input_text):
            return None

        if not self.__lingpat_api:
            self.__lingpat_api = LingPatLab()

        sentence: Sentence = self.__lingpat_api.parse_input_text(
            input_text=input_text,
            en_spacy_model=self._en_spacy_model
        )

        if sentence and sentence.tokens:
            return self.swap_input_tokens(tokens=sentence.tokens, ctr=ctr)

    def swap_input_tokens(self,
                          tokens: list[dict] | list[SpacyResult],
                          ctr: int = 0) -> list:
        """
        Perform synonym swapping on the given tokens.

        Args:
            tokens (list[dict] | list[SpacyResult]): The list of tokens to perform synonym swapping on.
                Some implementations may use spacy-core and send a list of SpacyResult objects.
                This route will convert these objects to native dictionaries for processing.
            ctr (int, optional): The counter to keep track of the number of recursive calls. Defaults to 0.

        Returns:
            list: The list of tokens after performing synonym swapping.

        """

        sw = Stopwatch()

        if tokens and len(tokens):
            if isinstance(tokens[0], SpacyResult):
                tokens: list[dict] = [
                    token.to_json() for token in tokens
                ]

        if isEnabledForDebug(self.logger):
            Enforcer.is_list_of_dicts(tokens)
            Enforcer.is_int(ctr)

        # ----------------------------------------------------------
        # Document:   Tokens vs Swaps
        # Reference:  GRAFFL-CORE-0074
        # ----------------------------------------------------------
        # swaps = self._augment_hierarchy(tokens)
        swaps = self._perform_exact_matching(tokens)

        # ----------------------------------------------------------
        # Change Log:
        # 20221129  OWL-FINDER-0005  It is possible that spans may not exist
        # ----------------------------------------------------------
        if self._finder.has_spans():
            swaps = self._perform_span_matching(swaps)

        swaps = self._perform_hierarchal_matching(swaps)

        if ctr < 2:
            swaps = self.swap_input_tokens(swaps, ctr + 1)

        # ----------------------------------------------------------
        # Change Log:
        # 20220214  Disable Environment Check
        # 20220228  GRAFFL-CORE-0205
        # if EnvIO.exists_as_true('ENABLE_SPACY_SPANNING'):
        #   swaps = self._perform_spacy_matching(swaps)
        # ----------------------------------------------------------

        if isEnabledForDebug(self.logger):
            self.logger.debug(f"Synonym Swap Completed in {str(sw)}")

        return swaps
