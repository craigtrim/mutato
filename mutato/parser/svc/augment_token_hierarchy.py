#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Augment Tokens with Descendant and Ancestory Hierarchy for Inference Purposes """


from mutato.finder.multiquery.bp import FindOntologyData
from mutato.core import configure_logging, Stopwatch, Enforcer, isEnabledForDebug

class AugmentTokenHierarchy(object):
    """ Augment Tokens with Descendant and Ancestory Hierarchy for Inference Purposes """

    def __init__(self,
                 find_ontology_data: FindOntologyData):
        """ Change Log

        Created:
            14-Feb-2022
            craigtrim@gmail.com
            *   https://github.com/grafflr/graffl-core/issues/188
        Updated:
            26-May-2022
            craigtrim@gmail.com
            *   remove 'ontology_name' as a param in pursuit of
                https://github.com/grafflr/deepnlu/issues/7
        Updated:
            27-May-2022
            craigtrim@gmail.com
            *   remove 'ontologies' and integrate 'find-ontology-data'
                https://github.com/grafflr/deepnlu/issues/13

        Args:
            find_ontology_data (FindOntologyData): an instantiation of this object
        """
        self.logger = configure_logging(__name__)
        self._find_ancestors = find_ontology_data.ancestors
        self._find_descendants = find_ontology_data.descendants

    def _process(self, tokens: list) -> list:

        d_normals = {
            token['normal']: []
            for token in tokens
            if token['normal'].isalpha()
        }

        for normal in d_normals:
            d_normals[normal].append(self._find_ancestors(normal))
            d_normals[normal].append(self._find_descendants(normal))

        for token in tokens:
            if token['normal'] not in d_normals:
                continue

            values = d_normals[token['normal']]
            token['ancestors'] = values[0]  # ancestor position
            token['descendants'] = values[1]  # descendant position

        return tokens

    def process(self,
                tokens: list) -> list:

        if isEnabledForDebug(self.logger):
            Enforcer.is_list(tokens)

        sw = Stopwatch()

        tokens = self._process(tokens)

        if isEnabledForDebug(self.logger):
            self.logger.debug(f"Hierarchy Augmentation Completed in {str(sw)}")

        return tokens
