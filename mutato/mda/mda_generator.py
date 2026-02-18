#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" MDA Generation Code """


from mutato.core import configure_logging
from mutato.finder.singlequery import AskOwlAPI
from mutato.finder.multiquery.dmo import ViewGeneratorLookup

class MDAGenerator(object):
    """ MDA Generation Code """

    def __init__(self,
                 ontology_name: str,
                 absolute_path: str,
                 namespace: str):
        """ Change Log:

        Created:
            26-May-2024
            ctrim@maryville.edu
            *   Load Graph into Memory
                https://github.com/Maryville-University-DLX/transcriptiq/issues/21
        Updated:
            26-May-2024
            ctrim@maryville.edu
            *   Exclude Predicates that add no value to NLP stage
                https://github.com/Maryville-University-DLX/transcriptiq/issues/351#issuecomment-2433585518
        """
        self.logger = configure_logging(__name__)

        self.api = AskOwlAPI(
            ontology_name=ontology_name,
            absolute_path=absolute_path,
            namespace=namespace
        )

        self.d_ontologies = {
            ontology_name: self.api
        }

    # ----------------------------------------------------------------------------------------------------
    # Purpose:  Hard-Code NER lookup label
    # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21#issuecomment-2133809956
    # Updated:  27-May-2024
    # ----------------------------------------------------------------------------------------------------
    # def find_ner(self, input_text: str) -> str | None:
    #     query_ner_label = QueryNerLabel(self.d_ontologies).process
    #     query_ner_depth = QueryNerDepth(self.d_ontologies).process
    #     query_ner_taxo = QueryNerTaxo(self.d_ontologies).process
    #     svc = FindNER(
    #         d_ner_depth=query_ner_depth(),
    #         d_ner_taxo=query_ner_taxo(),
    #         d_graffl_ner={},
    #         d_spacy_ner={})
    #     return svc.find_ner(input_text)
    # ----------------------------------------------------------------------------------------------------

    def generate(self) -> dict:

        d_predicates: dict[str, list[str]] = self.api.predicates()

        d_by_predicate: dict[str, list[str]] = {}
        for prefix in d_predicates:

            predicates: list[str] = [
                f"{prefix}:{predicate}" for predicate in d_predicates[prefix]
            ]

            predicates = [
                predicate for predicate in predicates
                # -----------------------------------------------------------------------------
                # Purpose:  Exclude Useless Predicates
                # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
                #           issuecomment-2433585518
                # Updated:  23-Oct-2024
                # -----------------------------------------------------------------------------
                if predicate not in [
                    'nil',
                    'rdfs:comment'
                ]
                # -----------------------------------------------------------------------------
            ]

            for predicate in predicates:
                d_by_predicate[predicate] = self.api.by_predicate(predicate)

        d_synonyms_fwd = self.api.synonyms()

        d_ner = {}
        for entity in self.api.labels():
            # ----------------------------------------------------------------------------
            # Purpose:  Hard-Code NER lookup label
            # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21
            #           issuecomment-2133809956
            # Updated:  27-May-2024
            # ----------------------------------------------------------------------------
            d_ner[entity] = "NER"  # self.find_ner(entity)

        # ----------------------------------------------------------------------------
        # Purpose:  Static Generation of View Lookup
        # Trace:    mutato/finder/multiquery/bp/find_ontology_data::lookup()
        # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/21
        #           issuecomment-2132603238
        # Updated:  26-May-2024
        # ----------------------------------------------------------------------------
        d_lookup = ViewGeneratorLookup().process(d_synonyms_fwd)
        
        # # -----------------------------------------------------------------------------
        # # Purpose:  keys must be strings
        # # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/513
        # # Updated:  26-May-2024
        # # -----------------------------------------------------------------------------
        # for key in d_lookup:
        #     assert isinstance(key, str)
        # # -----------------------------------------------------------------------------

        entities: list[str] = sorted(self.api.entities(), reverse=True)

        d_children: dict[str, list[str]] = {}
        for entity in entities:
            children: list[str] | None = self.api.children(entity)
            if children and len(children):
                d_children[entity] = children

        d_parents: dict[str, list[str]] = {}
        for entity in entities:
            parents: list[str] | None = self.api.parents(entity)
            if parents and len(parents):
                d_parents[entity] = parents

        return {
            "children": d_children,
            "parents": d_parents,
            "trie": self.api.trie(),
            "ngrams": self._ngrams(),
            "spans": self.api.spans(),
            "labels": self.api.keyed_labels(),
            # -----------------------------------------------------------------------------
            # Purpose:  Exclude Useless Predicates
            # Issue:    https://github.com/Maryville-University-DLX/transcriptiq/issues/351
            #           issuecomment-2433585518
            # Updated:  23-Oct-2024
            # -----------------------------------------------------------------------------
            # "comments": self.api.comments(),
            # -----------------------------------------------------------------------------
            "equivalents": self.api.equivalents(),
            "predicates": predicates,
            "by_predicate": d_by_predicate,
            "ner": d_ner,
            "synonyms": {
                "lookup": d_lookup,
                "fwd": self.api.synonyms(),
                "rev": self.api.synonyms_rev(),
            },
        }

    def _ngrams(self) -> dict[int, list[str]]:

        d_gram_levels: dict[int, list[str]] = {}

        for gram_level in range(1, 10):

            d_gram_levels[gram_level] = self.api.ngrams(gram_level=gram_level)

        return d_gram_levels
