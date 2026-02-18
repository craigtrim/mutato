#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from mutato.core import configure_logging, Stopwatch, isEnabledForDebug

class SpanContentCheck(object):
    """ 
    Find Candidate Span Matches

    This class finds matching rules for a given list of tokens. 

    It's the Phase 1 in
    GRAFFL-CORE-0077#issuecomment-947342784.
    """

    def __init__(self,
                 d_rules: dict[str, list[dict]],
                 rule_keys: set[str]):
        """ Change Log

        Created:
            20-Oct-2021
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/70
        Updated:
            25-Oct-2021
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/75
        Updated:
            24-Oct-2024
            craigtrim@gmail.com
            *   strip erronenous whitespace
                https://github.com/Maryville-University-DLX/transcriptiq/issues/351#issuecomment-2435992591

        Args:
            d_rules (dict): A dictionary mapping tokens to their corresponding rules.
            rule_keys (set): A set of rule keys.
        """
        self.logger = configure_logging(__name__)
        self._d_rules = d_rules
        self.rule_keys = rule_keys

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

    def _process(self,
                 tokens: list[dict]) -> list[dict]:
        """
        Process a list of tokens to find matching rules.

        Args:
            tokens (list): A list of tokens to process.

        Returns:
            A list of matching rules.
        """

        # Create a set of normal form tokens.
        token_keys = {token['normal'] for token in tokens}

        # Find common tokens between token_keys and rule_keys.
        common_tokens = token_keys.intersection(self.rule_keys)

        # If no common tokens, return an empty list.
        if not common_tokens:
            return []

        matching_rules = []

        # Iterate over the common tokens.
        for token in common_tokens:
            for rule in self._d_rules[token]:

                # If the rule content is a subset of the token keys, add the rule to the matching rules.
                if set(rule['content']).issubset(token_keys):

                    # Create a unique set of rule contents and sort them.
                    rule['content'] = sorted(set([
                        self._cleanse(token)
                        for token in [token] + rule['content']
                    ]), key=len)

                    # Add the rule to the matching rules.
                    matching_rules.append(rule)

        return matching_rules

    def process(self,
                tokens: list[dict]) -> list[dict]:
        """
        Process a list of tokens to find matching rules and log the results.

        Args:
            tokens (list): A list of tokens to process.

        Returns:
            A list of matching rules.
        """

        sw = Stopwatch()

        # Find matching rules for the given tokens.find
        matching_rules = self._process(tokens)

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Span Content Check Completed for {len(matching_rules)} rules in {str(sw)}")

        return matching_rules
