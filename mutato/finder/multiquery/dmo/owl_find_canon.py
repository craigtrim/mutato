# !/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Find Canon for OWL """


from mutato.finder.multiquery.dto import cleanse_canon
from mutato.core import configure_logging, Enforcer, isEnabledForDebug

class OwlFindCanon(object):
    """ Find Canon for OWL """

    def __init__(self,
                 d_synonyms_fwd: dict,
                 d_synonyms_rev: dict):
        """ Change Log

        Created:
            30-Nov-204
            ctrim@maryville.edu
            *   in pursuit of
                https://github.com/Maryville-University-DLX/transcriptiq/issues/419

        Args:
            ontologies (list): one-or-more Ontology models to use in processing
        """
        self.logger = configure_logging(__name__)
        self._d_synonyms_fwd = d_synonyms_fwd
        self._d_synonyms_rev = d_synonyms_rev

        self._has_synonyms_fwd = d_synonyms_fwd and len(d_synonyms_fwd)
        self._has_synonyms_rev = d_synonyms_rev and len(d_synonyms_rev)

    def process(self, input_text: str) -> str | None:

        # ---------------------------------------------------
        # Purpose:      Do not cleanse input text immediately
        # Reference:    https://github.com/craigtrim/owl-finder/issues/8
        # input_text = cleanse_canon(input_text)
        # ---------------------------------------------------
        if not input_text or not len(input_text):
            return None

        def find() -> str | None:

            # is canon
            if self._has_synonyms_fwd and input_text in self._d_synonyms_fwd:
                return input_text

            # is variant
            if self._has_synonyms_rev:
                if input_text in self._d_synonyms_rev:
                    return self._d_synonyms_rev[input_text]
                if '_' in input_text:
                    temp = input_text.replace('_', ' ')
                    if temp in self._d_synonyms_rev:
                        return self._d_synonyms_rev[temp]

        result = find()
        if not result or not len(result):
            # ---------------------------------------------------
            # Purpose:      Only cleanse text if input was not found
            # Reference:    https://github.com/craigtrim/owl-finder/issues/8
            # ---------------------------------------------------
            if ' ' in input_text or "'" in input_text:
                return self.process(cleanse_canon(input_text))

            # Only now we are certain no canonical form exists
            return None

        def get_result() -> str:
            if type(result) == list:
                if len(result) > 1:
                    self.logger.warning(
                        f"Multi Typed Result (total={len(result)}), (input={input_text}), (types={result})")
                return result[0]
            return result

        result = get_result()
        if isEnabledForDebug(self.logger):
            Enforcer.is_str(result)

        return result
