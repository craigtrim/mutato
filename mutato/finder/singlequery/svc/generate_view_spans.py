#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" View Generator: Entity Spans for Long-Range Synonym Swapping """


from collections import defaultdict

from mutato.core import configure_logging, EnvIO

# ----------------------------------------------------------
# Purpose:    List of Stopwords
# Reference:  https://github.com/craigtrim/askowl/issues/10
# Source:     https://gist.github.com/sebleier/554280#gistcomment-2596130
# Notes:      this list will likely be refined as needed over time
#             the 'stopwords' represented here are likely too coarse-grained
# ----------------------------------------------------------
stopwords = [
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before',
    'between', 'both', 'but', 'by', 'can', 'did', 'do', 'does', 'doing', 'don', 'down', 'during', 'each', 'few', 'for', 'from', 'further',
    'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself',
    'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out',
    'over', 'own', 's', 'same', 'she', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
    'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while',
    'who', 'whom', 'why', 'will', 'with', 'you', 'your', 'yours', 'yourself', 'yourselves'
]


class GenerateViewSpans(object):
    """ View Generator: Entity Spans for Long-Range Synonym Swapping """

    def __init__(self):
        """ Change Log

        Created:
            25-Oct-2021
            craigtrim@gmail.com
            *   Automate Long Distance Matching in Multi Gram Entities
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   ported to ask-owl
                https://github.com/craigtrim/askowl/issues/5
        Updated:
            24-Nov-2022
            craigtrim@gmail.com
            *   deal with CSV lists in rdfs:seeAlso relationship
                https://github.com/craigtrim/owl-finder/issues/2#issuecomment-1326808994
        Updated:
            28-Nov-2022
            craigtrim@gmail.com
            *   use hash to ensure uniqueness in spans
                https://github.com/craigtrim/owl-finder/issues/4#issuecomment-1329990189
        Updated:
            24-Oct-2024
            craigtrim@gmail.com
            *   strip erroneous whitespace
                https://github.com/Maryville-University-DLX/transcriptiq/issues/351#issuecomment-2435992591
        """
        self.logger = configure_logging(__name__)

    @classmethod
    def _normalize(self,
                   d_results: dict) -> dict:
        """Normalize the Result of the OWL Query

        Sample Input
            'nurse_practitioner':   {   'Np':                       None,
                                        'Nps':                      None,
                                        'Nursing Practitioner':     None },
            'nursing':              {   'Nursing':                  None },
            'nursing_diploma':      {   'Nursing Diploma':          None },
            'nursing_education':    {   'Nursing Education':        None },

        Sample Output:
            {   'nurse_practitioner': [ 'Nursing Practitioner' ],
                'nursing_diploma    : []'
                'nursing_education' : []}

        Args:
            d_results (dict): [description]

        Returns:
            list: Terms to Span Over
        """
        d = {}

        def is_valid(term: str) -> bool:
            return ' ' in term or '_' in term

        keys = [k for k in d_results if is_valid(k)]

        for key in keys:

            def values() -> list[str]:
                """ Deal with CSV List

                Reference:
                    https://github.com/craigtrim/owl-finder/issues/2#issuecomment-1326808994

                Returns:
                    list[str]: a list of synonyms for this entity
                """
                s = set()
                for item in d_results[key]:
                    if ',' in item:
                        [s.add(y) for y in [
                            x.strip() for x in item.split(',')]
                         ]
                    else:
                        s.add(item)

                return sorted(s)

            values = [v for v in values() if is_valid(v)]
            values = [v.lower().replace(' ', '_') for v in values]
            values = [v for v in values if v != key]
            d[key] = values

        return d

    # -----------------------------------------------------------------------------
    @staticmethod
    def _cleanse(value: str) -> str:
        # Purpose:  Strip erronenous Whitespace
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
        #           issuecomment-2435992591
        # Updated:  24-Oct-2024
        # -----------------------------------------------------------------------------
        while '  ' in value:
            value = value.replace('  ', ' ')
        return value.strip()
    # -----------------------------------------------------------------------------

    def _to_dict(self,
                 canon: str,
                 tokens: list) -> dict:

        def content() -> set:
            _tokens: list[str] = [
                self._cleanse(token) for token in tokens[1:]
            ]

            _tokens: list[str] = [
                token for token in _tokens
                if token.lower() not in stopwords
            ]

            # t = [x for x in tokens[1:] if x.lower() not in stopwords]
            return sorted(set(_tokens), reverse=False)

        tokens2 = content()
        if not len(tokens2):
            return None

        # TODO: all these values have to be default only when not otherwise specified
        distance = EnvIO.int_or_default('SPAN_DISTANCE', 4)
        return {
            'content': content(),
            'distance': distance,
            'forward': True,
            'reverse': True,
            'canon': canon
        }

    def process(self,
                d_results: dict) -> dict:

        d = defaultdict(list)

        hashes = set()
        d_results = self._normalize(d_results)

        def update(canon: str,
                   term: str) -> None:
            tokens = term.split('_')
            trigger = tokens[0]

            d_result = self._to_dict(canon, tokens)

            if d_result:

                # 20221128; Ensure Uniqueness
                # https://github.com/craigtrim/owl-finder/issues/4#issuecomment-1329990189
                hash_d_result = hash(''.join([
                    str(x) for x in d_result.values()
                ]))

                if hash_d_result not in hashes:
                    d[trigger].append(d_result)
                    hashes.add(hash_d_result)

        for k in d_results:
            update(canon=k, term=k)
            for v in d_results[k]:
                update(canon=k, term=v)

        return dict(d)
