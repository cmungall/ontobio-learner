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

GAF = "tests/resources/truncated-pombase-phenotypes.gaf"
TGAF = "tests/resources/truncated-pombase.gaf"
ONT = "tests/resources/fypo-truncated-pombase.json"
TONT = "tests/resources/go-truncated-pombase.json"

def test_learn_from_phenotype():
    """
    Learn GO from Phenotypes

    (note: some phenotypes in FYPO have graph paths to GO classes,
    so GO will be used to predict GO, which may seem circular, but
    in fact the phenotype is different information)
    """
    ont = OntologyFactory().create(ONT)
    tont = OntologyFactory().create(TONT)
    afa = AssociationSetFactory()
    aset = afa.create_from_file(file=GAF, ontology=ont)
    taset = afa.create_from_file(file=TGAF, ontology=tont)
    
    learner = ol.OntologyLearner(assocs=aset,
                                 target_assocs=taset,
                                 score_threshold=0.9)
    print('L={}'.format(learner))
    print('L.assocs={}'.format(learner.assocs))
    print('L.tassocs={}'.format(learner.target_assocs))
    dir = 'target/from_phenotype'
    with open(dir + '/index.md', 'w') as file:
        learner.fit_all(dir=dir,
                        reportfile=file)
    print('L.targets={}'.format(learner.targets))

if __name__ == "__main__":
    test_learn_from_phenotype()
    
