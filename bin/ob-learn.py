#!/usr/bin/env python3

"""
Multiple commands for

 - tidying up HPO annot files
 - generating synthetic patient vectors from annotations
 - build tree classifiers for each disease

"""

from ontobio.io import assocparser
from ontobio.io.gpadparser import GpadParser
from ontobio.io.gafparser import GafParser
from ontobio.io import GafWriter
from ontobio.io.assocwriter import GpadWriter
from ontobio import AssociationSetFactory
from ontobio import OntologyFactory
import ontobio_learner as ol

import pandas as pd
import numpy as np
import click
import os
import graphviz
import pydot
import logging
import math

@click.group()
def cli():
    pass



@cli.command()
@click.option("--resource", "-r", help="Ontology id or path")
@click.option("--input", "-i", help="association file")
@click.option("--outdir", "-d", default='./target')
@click.option("--target_assocfile", "-A",
              help='if passed, targets will be obtained from this file')
@click.option("--target_ontology", "-X",
              help='if passed, this will be used as the ontology for classifying targets')
@click.option("--target_root_class", "-R",
              help='if passed, a single assoc file will be used, and this will be split into target and features based on inheritance of this class')
def learn(resource, input, outdir, target_assocfile, target_ontology, target_root_class):
    """
    Learn association rules
    """
    logging.basicConfig(level=logging.INFO)
    
    afa = AssociationSetFactory()
    ofa = OntologyFactory()

    ont = ofa.create(resource)
    aset = afa.create_from_file(file=input, ontology=ont, fmt=None)

    learner = ol.OntologyLearner(assocs=aset)
    isa_ont = ont.subontology(relations=['subClassOf'])

    if target_root_class:
        learner.split_assocs(target_root_class, ontology=isa_ont)

    if target_ontology:
        learner.target_ontology = ofa.create(target_ontology)
    if target_assocfile:
        tont = ont
        if learner.target_ontology is not None:
            tont = learner.target_ontology
        learner.target_assocs = afa.create_from_file(target_assocfile, ontology=tont, fmt=None)
        
    with open(outdir + '/index.md', 'w') as file:
        learner.fit_all(dir=outdir, reportfile=file)
    
    
if __name__ == "__main__":
    cli()
