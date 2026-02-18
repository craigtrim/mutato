# !/usr/bin/env python
# -*- coding: UTF-8 -*-


from collections import defaultdict

from mutato.core import configure_logging
from mutato.finder.singlequery import AskOwlAPI

class FindEquivalents(object):

    def __init__(self,
                 owlapis: list[AskOwlAPI]):
        """ Change Log

        Created:
            16-Aug-2023
            craig@bast.ai
            *   https://bast-ai.atlassian.net/browse/COR-139
        """
        self.logger = configure_logging(__name__)
        self._owlapis = owlapis

    def process(self,
                entities: list[str]) -> dict[str, list[str]]:
        """
        Processes a list of entity names to find their equivalent entities.

        Parameters:
            entities (list[str]): A list of entity names.

        Returns:
            Dict[str, list[str]]: 
                A dictionary where:
                    - Each key is a cleaned-up entity name from the input list, and
                    - The associated value is a list of equivalent entity names for the key entity.

        Notes:
            - The method normalizes the input entity names by replacing spaces with underscores, 
              converting to lowercase, and stripping leading/trailing whitespace.
            - The method aggregates data from multiple OWL API instances, which are accessed through self._owlapis.
        """

        if isinstance(entities, str):
            entities = [entities]
        elif not isinstance(entities, list):
            raise ValueError(f"Unexpected Type: {type(entities)}")

        # Normalize entity names
        entities = [
            x.replace('_', ' ').lower().strip()
            for x in entities
        ]

        # print (entities)

        # Initialize the master dictionary with default sets
        d_master = defaultdict(set)

        # Fetch and aggregate equivalent entities from all OWL API instances
        for owlapi in self._owlapis:

            d_equivalents = owlapi.equivalents()
            if not d_equivalents or not len(d_equivalents):
                continue

            for entity in [
                x for x in entities
                if x in d_equivalents
            ]:
                d_master[entity].update(d_equivalents[entity])

        # Convert sets to lists
        return {k: list(v) for k, v in d_master.items()}
