#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" View Generator: Perform Synonym Transformation """


from collections import defaultdict

from mutato.core import configure_logging, TextUtils

class GenerateViewSynonyms(object):
    """ View Generator: Perform Synonym Transformation """

    __punkt = [
        '!',
        '?',
        '.',
    ]

    def __init__(self):
        """ Change Log
        Created:
            7-Oct-2021
            craigtrim@gmail.com
            *   Create Owl2PY Util Service
        Updated:
            2-Feb-2022
            craigtrim@gmail.com
            *   augment forms by removing punctuation
                Defect in Synonym Swapping when Punctuation is Present
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   ported to ask-owl
                https://github.com/craigtrim/askowl/issues/6
        Updated:
            2-Jun-2022
            craigtrim@gmail.com
            *   tokenize spaces in synonyms
                https://github.com/craigtrim/askowl/issues/7
        Updated:
            25-Nov-2022
            craigtrim@gmail.com
            *   remove '+' from spanned synonyms
                https://github.com/craigtrim/owl-finder/issues/4#issuecomment-1327975311
        Updated:
            18-Aug-2023
            craig@bast.ai
            *   augment representation of spans as exact matches
                https://bast-ai.atlassian.net/browse/COR-140?focusedCommentId=10685
        Updated:
            24-Oct-2024
            craigtrim@gmail.com
            *   clean spacing
                https://github.com/Maryville-University-DLX/transcriptiq/issues/351#issuecomment-2435707522
        """
        self.logger = configure_logging(__name__)

    @staticmethod
    def _reverse(d: dict) -> dict:
        d_rev = defaultdict(list)
        for k in d:
            for v in d[k]:
                d_rev[v].append(k)

        return dict(d_rev)

    @staticmethod
    def _cleanse(value: str) -> str:
        # -----------------------------------------------------------------------------
        # Purpose:  Clean Spacing for Accurate Downstream Trie and N-Gramming
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
        #           issuecomment-2435707522
        # Updated:  24-Oct-2024
        # -----------------------------------------------------------------------------
        while '  ' in value:
            value = value.replace('  ', ' ').strip()
        # -----------------------------------------------------------------------------
        return value

    def process(self,
                d_results: dict,
                reverse: bool = False) -> dict:
        d = {}

        for k in d_results:

            s = set()
            for value in d_results[k]:

                # Represent Spanned Synonyms into String-Based Synonyms
                if '+' in value:  # https://github.com/craigtrim/owl-finder/issues/4#issuecomment-1327975311
                    value = value.replace('+', ' ')

                s.add(value.lower())

                # Represent exact matches as well
                if '_' in value:  # https://bast-ai.atlassian.net/browse/COR-140?focusedCommentId=10685
                    s.add(value.replace('_', ' ').lower())

                # Reference: Defect in Synonym Swapping when Punctuation is Present
                # https://github.com/craigtrim/askowl/issues/11
                for punkt in self.__punkt:
                    if value.endswith(punkt):
                        s.add(value[:len(value) - len(punkt)])

                # Reference: Tokenization of Space Required
                # https://github.com/craigtrim/askowl/issues/7
                # TODO: likely need better testing around period vs ellipses vs multiple periods here
                if '.' in value and '...' not in value:
                    _value = value.replace('.', ' . ')
                    _value = TextUtils.update_spacing(_value)
                    s.add(_value)

            d[k.lower()] = sorted(set([
                self._cleanse(token) for token in sorted(s, key=len)
            ]), key=len)

        if reverse:
            return self._reverse(d)

        return d
