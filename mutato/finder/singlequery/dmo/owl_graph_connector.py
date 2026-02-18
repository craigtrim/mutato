#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Connect to an RDF Graph (Ontology) """


import os

from rdflib import Graph
from mutato.core import configure_logging, FileIO, isEnabledForDebug

class OwlGraphConnector(object):
    """ Connect to an RDF Graph (Ontology) """

    def __init__(self,
                 prefix: str,
                 namespace: str,
                 ontology_name: str,
                 absolute_path: str):
        """ Change Log

        Created:
            6-Oct-2021
            craigtrim@gmail.com
            *   Create Owl2PY Util Service
        Updated:
            25-May-2022
            craigtrim@gmail.com
            *   refactor into 'ask-owl' repo
                https://github.com/craigtrim/askowl/issues/1

        Args:
            prefix (str): the query prefix
            namespace (str): the ontology namespace
            ontology_name (str): the ontology name (phsyical file name)
            absolute_path (str): the absolute path to the OWL model
        """
        self.logger = configure_logging(__name__)

        self._format = 'ttl'
        self._prefix = prefix
        self._namespace = namespace
        self._ontology_name = ontology_name
        self._absolute_path = absolute_path

        self._graph = self._process()

        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Loading Ontology (namespace: {self._namespace}), (name: {self._ontology_name}), (prefix: {self._prefix}), (format: {self._format}), (absolute path: {self._absolute_path})")

    def _get_versioned_model(self) -> str | None:
        """ Get Versioned Model from Directory

        Notes:
            Ontology Models may be saved as
                /home/path/temp/my_model-0.1.0.owl

            But the only params passed by the consumer are:
                absolute-path:  /home/path/temp
                ontology-name:  my_model.owl

            This function will find any Ontology Model at the given location
                with a matching name, but also with a version

        Returns:
            str | None: the qualified input path to a versioned model, if any
        """
        files = FileIO.load_files(
            directory=self._absolute_path,
            extension='owl')

        if len(files) != 1:
            return None

        basename = os.path.basename(files[0]).split('.')[0].strip()
        if not basename.startswith(self._ontology_name.split('.')[0]):
            self.logger.error(
                "Named Ontology Not Found: (Ontology Name: {self._ontology_name}), (Ontology Files: {files}")
            return None

        input_path = files[0]
        if isEnabledForDebug(self.logger):
            self.logger.debug(
                f"Using Verisoned Ontology Model: (Incoming Ontology Name: {self._ontology_name}), (Versioned Ontology Model: {input_path}")

        return input_path

    def _process(self) -> Graph:
        """ Load the OWL Model from disk as an RDF Graph

        Returns:
            Graph: an instantiated and in-memory RDF Graph
        """
        g = Graph()

        input_path = os.path.normpath(
            os.path.join(
                self._absolute_path,
                self._ontology_name))

        if not FileIO.exists(input_path):
            input_path = self._get_versioned_model()

        FileIO.exists_or_error(input_path)

        g.parse(input_path,
                format=self._format)

        # TODO: Fix this in the future
        # g.bind(self._prefix,
        #       Namespace(self._namespace))

        return g

    def graph(self) -> Graph:
        return self._graph
