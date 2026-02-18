#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Identical to AskOwlAPI but query local JSON representation of OWL instead """


from mutato.core import configure_logging

class AskJsonAPI(object):
    """ Identical to AskOwlAPI but query local JSON representation of OWL instead """

    def __init__(self,
                 d_owl: dict):
        """ Change Log

        Created:
            26-May-2024
            ctrim@maryville.edu
            *   https://github.com/Maryville-University-DLX/transcriptiq/issues/21
        Args:
            d_owl (dict): the server-side JSON representation of the OWL model

        Raises:
            ValueError: OWL Model Not Found
        """
        self.logger = configure_logging(__name__)
        self.d_owl = d_owl

    def ngrams(self, gram_level: int) -> list[str]:
        """ Retrieve n-grams from the OWL model

        Args:
            gram_level (int): the level of n-grams to retrieve

        Returns:
            list[str] | None: a list of n-grams at the specified level or None if not found
        """
        return self.d_owl.get("synonyms", {}).get(gram_level, [])

    def trie(self) -> dict:
        """
        Retrieves the trie from the d_owl dictionary.

        Returns:
            dict | None: The trie dictionary if it exists, otherwise None.
        """
        return self.d_owl.get("trie", {})

    def by_predicate(self, predicate: str) -> list:
        """
        Retrieves the list of items associated with the given predicate.

        Args:
            predicate (str): The predicate to search for.

        Returns:
            list: The list of items associated with the given predicate, or None if the predicate is not found.
        """
        return self.d_owl.get("by_predicate", {}).get(predicate, [])

    def labels(self) -> list:
        """ Retrieve labels from the OWL model

        Returns:
            list: a list of labels or None if not found
        """
        return self.d_owl.get("labels", [])

    # -----------------------------------------------------------------------------
    # Purpose:  Exclude Useless Predicates
    # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
    #           issuecomment-2433585518
    # Updated:  23-Oct-2024
    # -----------------------------------------------------------------------------
    # def comments(self) -> dict[str, list[str]]:
    #     """
    #     Retrieve the comments from the d_owl dictionary.

    #     Returns:
    #         A dictionary containing comments as values, with keys representing different categories.
    #     """
    #     return self.d_owl.get("comments", {})
    # -----------------------------------------------------------------------------

    def types(self) -> list:
        """
        Returns the list of types associated with the JSON object.

        Returns:
            list: The list of types associated with the JSON object.
                  Returns None if "types" key is not present in the JSON object.
        """
        return self.d_owl.get("types", [])

    def predicates(self) -> dict:
        """
        Retrieves the predicates from the d_owl dictionary.

        Returns:
            A dictionary containing the predicates, or None if "predicates" is not present in d_owl.
        """
        return self.d_owl.get("predicates", {})

    def synonyms(self) -> dict:
        """
        Retrieves the synonyms from the d_owl dictionary.

        Returns:
            A dictionary containing the synonyms, or None if no synonyms are found.
        """
        return self.d_owl.get("synonyms", {}).get("fwd", {})

    def synonyms_rev(self) -> dict:
        """
        Retrieves the reverse synonyms from the 'synonyms' dictionary.

        Returns:
            A dictionary containing the reverse synonyms, or an empty dictionary if no reverse synonyms are found.
        """
        return self.d_owl.get("synonyms", {}).get("rev")

    def synonyms_lookup(self) -> dict:
        """
        Retrieves the synonyms from the d_owl dictionary.

        Returns:
            A dictionary containing the synonyms, or None if no synonyms are found.
        """
        return self.d_owl.get("synonyms", {}).get("lookup", {})

    def equivalents(self) -> dict[str, list[str]]:
        return self.d_owl.get("equivalents", {})

    def find_ner(self, input_text: str) -> str | None:
        return self.d_owl.get("ner", {}).get(input_text)

    def spans(self) -> dict:
        """
        Returns the spans dictionary from the d_owl attribute.

        Returns:
            dict | None: The spans dictionary from the d_owl attribute.
        """
        return self.d_owl.get("spans", {})

    def entities(self) -> list[str]:
        return self.d_owl.get('entities', [])

    def children(self, entity: str):
        return self.d_owl.get('children', []).get(entity, [])

    def descendants(self, entity: str):
        # Initialize an empty list to store descendants
        all_descendants = []

        # Get the direct children of the entity
        direct_children = self.children(entity)

        # Iterate through each child
        for child in direct_children:

            # Add the child to the list of descendants
            all_descendants.append(child)

            # Recursively find and add the child's descendants
            all_descendants.extend(self.descendants(child))

        return all_descendants

    def parents(self, entity: str):
        return self.d_owl.get('parents', []).get(entity, [])

    def ancestors(self, entity: str) -> list[str]:

        # Initialize an empty list to store ancestors
        all_ancestors = []

        # Get the direct parents of the entity
        direct_parents = self.parents(entity)

        # Iterate through each parent
        for parent in direct_parents:

            # Add the parent to the list of ancestors
            all_ancestors.append(parent)

            # Recursively find and add the parent's ancestors
            all_ancestors.extend(self.ancestors(parent))

        return all_ancestors
