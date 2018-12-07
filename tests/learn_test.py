from ontobio.io import assocparser
from ontobio.io.gpadparser import GpadParser
from ontobio.io.gafparser import GafParser
from ontobio.io import GafWriter
from ontobio.io.assocwriter import GpadWriter
from ontobio.assoc_factory import AssociationSetFactory
from ontobio.ontol_factory import OntologyFactory
import ontobio_learner as ol

import tempfile
import logging
import pytest
import io
import json

GAF = "tests/resources/truncated-pombase.gaf"
ONT = "tests/resources/go-truncated-pombase.json"
CC = "GO:0005575"
BP = "GO:0008150"

def test_learn():
    afa = AssociationSetFactory()
    ont = OntologyFactory().create(ONT)

    aset = afa.create_from_file(file=GAF, ontology=ont)
    learner = ol.OntologyLearner(assocs=aset)
    print('L={}'.format(learner))
    subont = ont.subontology(relations=['subClassOf'])
    learner.split_assocs(CC, ontology=subont)
    print('L.assocs={}'.format(learner.assocs))
    print('L.tassocs={}'.format(learner.target_assocs))
    with open('target/index.md', 'w') as file:
        learner.fit_all(reportfile=file)
    print('L.targets={}'.format(learner.targets))

if __name__ == "__main__":
    test_learn()
    
