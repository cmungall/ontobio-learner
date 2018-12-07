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
TGAF = "tests/resources/truncated-pombase-phenotypes.gaf"
ONT = "tests/resources/go-truncated-pombase.json"
TONT = "tests/resources/fypo-truncated-pombase.json"
CC = "GO:0005575"
BP = "GO:0008150"

def test_learn():
    ont = OntologyFactory().create(ONT)
    tont = OntologyFactory().create(TONT)
    afa = AssociationSetFactory()
    aset = afa.create_from_file(file=GAF, ontology=ont)
    taset = afa.create_from_file(file=TGAF, ontology=tont)
    
    learner = ol.OntologyLearner(assocs=aset,
                                 target_assocs=taset,
                                 score_threshold=0.6)
    print('L={}'.format(learner))
    print('L.assocs={}'.format(learner.assocs))
    print('L.tassocs={}'.format(learner.target_assocs))
    with open('target/pheno_index.md', 'w') as file:
        learner.fit_all(reportfile=file)
    print('L.targets={}'.format(learner.targets))

if __name__ == "__main__":
    test_learn()
    
