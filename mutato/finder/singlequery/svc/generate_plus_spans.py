#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" View Generator: Entity Spans for Long-Range Synonym Swapping """


from collections import defaultdict

from mutato.core import configure_logging, EnvIO

class GeneratePlusSpans(object):
    """ View Generator: Entity Spans for Long-Range Synonym Swapping """

    def __init__(self):
        """ Change Log

        Created:
            25-Nov-2022
            craigtrim@gmail.com
            *   https://github.com/craigtrim/owl-finder/issues/4
        Updated:
            28-Nov-2022
            craigtrim@gmail.com
            *   use hash to ensure uniqueness in spans
                https://github.com/craigtrim/owl-finder/issues/4#issuecomment-1329990189
        Updated:
            1-Aug-2023
            craigtrim@gmail.com
            *   reverse spans for more coverage
                https://bast-ai.atlassian.net/browse/COR-135
            *   update hashing algorithm
                https://bast-ai.atlassian.net/browse/COR-136
        Updated:
            24-Oct-2024
            craigtrim@gmail.com
            *   strip erroneous whitespace
                https://github.com/Maryville-University-DLX/transcriptiq/issues/351#issuecomment-2435992591
        """
        self.logger = configure_logging(__name__)

    def _to_dict(self,
                 canon: str,
                 tokens: list) -> dict[str, any]:

        # -----------------------------------------------------------------------------
        def cleanse(value: str) -> str:
            # Purpose:  Strip erronenous Whitespace
            # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
            #           issuecomment-2435992591
            # Updated:  24-Oct-2024
            # -----------------------------------------------------------------------------
            while '  ' in value:
                value = value.replace('  ', ' ')
            return value.strip()
        # -----------------------------------------------------------------------------

        tokens = sorted(set([
            cleanse(token) for token in tokens
        ]), reverse=False)

        if not len(tokens):
            return None

        # TODO: all these values have to be default only when not otherwise specified
        distance = EnvIO.int_or_default('SPAN_DISTANCE', 4)
        return {
            'content': tokens,
            'distance': distance,
            'forward': True,
            'reverse': True,
            'canon': canon
        }

    @staticmethod
    def _to_hash(key: str,
                 d_result: dict) -> str:
        # ----------------------------------------------------------
        # Purpose:  Ensure Uniqueness
        # Issue:    https://github.com/craigtrim/owl-finder/issues/4
        #           issuecomment-1329990189
        # Updated:  28-Nov-2022
        # ----------------------------------------------------------
        return hash(''.join([
            key,  # COR-136
            ''.join(d_result['content']),
            str(d_result['distance']),
            str(d_result['forward']),
            str(d_result['reverse']),
            d_result['canon'],
        ]))

    @staticmethod
    def sliding_n_grams(input_text: str, n: int) -> list[str]:
        """
        Generate sliding n-grams from the input text.

        Args:
            input_text (str): The input text to generate sliding n-grams from.
            n (int): The size of the n-grams to generate.

        Returns:
            list[str]: A list of sliding n-grams.

        Raises:
            ValueError: If n is less than 2.
        """
        if n < 2:
            raise ValueError("n must be at least 2")

        # Split the text into tokens based on whitespace
        tokens = input_text.split()

        # Create sliding n-grams using a list comprehension
        return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

    def sliding_bigrams(self, input_text: str) -> list[str]:
        return [
            token.replace(' ', '_') for token in
            self.sliding_n_grams(input_text, 2)
        ]

    def process(self,
                d_results: dict) -> dict:

        hashes = set()
        d_spans = defaultdict(list)

        for entity in d_results:

            synonyms: list[str] = d_results[entity]

            # -----------------------------------------------------------------------------
            # Experimental Section --------------------------------------------------------
            # Purpose:  Create Artificial Spans
            # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/352
            # Updated:  24-Oct-2024
            s = set(synonyms)
            for synonym in synonyms:

                bigrams: list[str] = self.sliding_bigrams(synonym)
                bigrams: list[str] = [
                    bigram for bigram in bigrams
                    if bigram in d_results
                ]

                for bigram in bigrams:
                    _bigram = bigram.replace('_', ' ')
                    synonym = synonym.replace(_bigram, f"{bigram} +")
                    if not synonym.endswith('+'):
                        s.add(synonym)

            synonyms: list[str] = [
                synonym for synonym in s
                if '+' in synonym
            ]
            # End Experimental Section ----------------------------------------------------
            # -----------------------------------------------------------------------------

            for synonym in synonyms:

                tokens: list[str] = synonym.split('+')

                d_result: dict[str, any] = self._to_dict(entity, tokens[1:])
                h_result: str = self._to_hash(tokens[0], d_result)

                if h_result not in hashes:
                    d_spans[tokens[0]].append(d_result)
                    hashes.add(h_result)

        return dict(d_spans)
