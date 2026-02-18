from .bp import *
from .dmo import *
from .dto import *
from .svc import *
from mutato.parser.bp import MutatoAPI
from mutato.core import Enforcer, FileIO
from mutato.finder.multiquery.bp import FindOntologyData

def owl_parse(tokens: list,
              ontology_name: str,
              absolute_path: str):

    Enforcer.is_list_of_dicts(tokens)
    Enforcer.is_str(ontology_name)
    FileIO.exists_or_error(absolute_path)

    finder = FindOntologyData(ontologies=[ontology_name],
                              absolute_path=absolute_path)

    api = MutatoAPI(finder)
    svcresult = api.swap_input_tokens(tokens=tokens)

    Enforcer.is_list_of_dicts(svcresult)

    return svcresult
