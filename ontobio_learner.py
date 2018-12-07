from typing import Optional, Set, List, Union, Dict, Any, Tuple
from dataclasses import dataclass, field
from sklearn import tree
from sklearn import preprocessing
from sklearn.externals.six import StringIO  
from ontobio import Ontology
from ontobio.assocmodel import AssociationSet

import pickle
import re

import pandas as pd
import numpy as np
import click
import os
import graphviz
import pydot
import sys

import subprocess
import logging

TargetClass = str
FeatureClass = str

@dataclass
class OntologyLearner(object):

    target_ontology: Ontology = None
    assocs : AssociationSet = None
    target_assocs : AssociationSet = None
    features : List[FeatureClass] = None
    targets : List[TargetClass] = None
    min_samples_leaf : int = 2
    min_samples_split : int = 2
    min_impurity_decrease : float = 0.01
    max_depth : int = 5
    score_threshold : float = 0.6
    
    def training_df(self) -> pd.DataFrame:
        """
        Generates a training set, returned as DataFrame.
        Columns are:
        - id: subject id (e.g. gene)
        - targets: list of classes the subject belongs to
        - one column per inferred term (e.g. closure)

        If target_assocs is set, then this is used to generate the target classes
        (e.g. to predict function from phenotype, the target assoc model would be GO annotations,
        and the core assoc model would be phenotype annotations)

        If this is not set, then target_ontology should be set, and in this ontology
        the subjects must be nodes in the graph
        """
        items = []
        distinct_features = set()
        distinct_targets = set()
        logging.info("Getting training dataset, from {} subjects".format(len(self.assocs.subjects)))
        for s in self.assocs.subjects:
            item = {'id': s}
            if self.target_assocs is not None:
                targets = self.target_assocs.inferred_types(s)
            else:
                if self.target_ontology is not None:
                    targets = self.target_ontology.ancestors(s)
                else:
                    raise Exception('must set EITHER target_assocs OR target_ontology')
            if targets is not None:
                features = self.assocs.inferred_types(s)
                distinct_targets.update(targets)
                items.append(item)
                for f in features:
                    item[f] = 1
                    distinct_features.add(f)
                item['targets'] = targets
        self.features = list(distinct_features)
        self.targets = list(distinct_targets)
        logging.info("Distinct features = {}".format(len(self.features)))
        logging.info("Distinct targets = {}".format(len(self.targets)))

        tdf = pd.DataFrame(items, columns=['id', 'targets'] + self.features)
        return tdf.fillna(0)

    def fit_target_class(self, target: str, train : pd.DataFrame) -> Optional[Tuple[tree.DecisionTreeClassifier, float]]:
        """
        Given a data frame of training instances, fit a classifier for a given target.

        As any item can belong to multiple targets, the pos v neg set is split according
        to whether the target is found in the list of targets.

        E.g. if patient1 has targets [EOPD, PD, neurodegenerative disease]
        and patient2 has targets [EOAlz, Alz, neurodenerative disease]
        Then when training for ND disease, these will both belong to target class,
        but when training for PD, patient1 is positive and patient2 is negative
        """
        tlabel = self.assocs.ontology.label(target)
        logging.info('Fitting: {} {}'.format(target, tlabel))
        id = train['id']
        y = train['targets']
        x = train.drop(['targets', 'id'], axis=1)
        y2 = y.apply(lambda ts : target in ts).values
        num_pos = y2[y2].size
        if num_pos < 3:
            logging.info('Skipping: {} {} as only {} positive examples'.format(target, tlabel, num_pos))
            return None
            
        self.feature_names = x.columns.values.tolist()
        clf = tree.DecisionTreeClassifier(max_depth=self.max_depth,
                                          min_samples_leaf=self.min_samples_leaf,
                                          min_samples_split=self.min_samples_split,
                                          min_impurity_decrease=self.min_impurity_decrease)
        clf = clf.fit(x, y2)
        score = clf.score(x, y2)
        if score < self.score_threshold:
            logging.info('Skipping: {} {} as score {} < {}'.format(target, tlabel, score, self.score_threshold))
            return None
        tr = clf.tree_
        if tr.node_count <= 1:
            logging.info('Skipping: {} {} as tree is singleton node'.format(target, tlabel))
            return None
        logging.info('Target: {} {} Score: {}'.format(target, self.assocs.ontology.label(target), score))
        return (clf,score)

    def _safe_name(self, n):
        return re.sub('[^0-9a-zA-Z]+', '_', str(n))
    
    def fit_all(self, train : pd.DataFrame = None, dir="./target", reportfile=sys.stdout, target : TargetClass = None):
        ont = self.assocs.ontology
        logging.info("Fitting all; features ontology={}".format(ont))
        
        if train is None:
            train = self.training_df()
        # find all distinct targets
        targets = set()
        for ts in train.targets:
            targets.update(ts)

        feature_names = [ont.label(f) for f in self.features]
        feature_names = [self._safe_name(n) for n in feature_names]
        for t in targets:
            if target is not None and target != t:
                continue
            clf_score = self.fit_target_class(t, train)
            if clf_score is None:
                continue
            clf,score = clf_score
            t_name = ont.label(t)
            if t_name is None and self.target_ontology is not None:
                t_name = self.target_ontology.label(t)
            if t_name is None and self.target_assocs is not None:
                t_name = self.target_assocs.ontology.label(t)
            if t_name is None:
                t_name = t.replace(":","_")
                
            tr = clf.tree_
            reportfile.write('\n## {} ({})\n\n'.format(t_name, t))
            reportfile.write(' * Score = {}\n'.format(score))
            reportfile.write(' * Nodes = {}\n'.format(tr.node_count))

            filename = self._safe_name(t_name)
            base = "{}/{}".format(dir, filename)
            dotpath = base + ".dot"
            pngpath = base+".png"
            with open(base + ".pickle", 'wb') as handle:
                pickle.dump(clf, handle, protocol=pickle.HIGHEST_PROTOCOL)
            tree.export_graphviz(clf,
                                 feature_names=feature_names,
                                 filled=True, rounded=True,  
                                 special_characters=True,                     
                                 out_file= dotpath)   
            cmd = ['dot','-T','png',dotpath,'-o',pngpath]
            cp = subprocess.run(cmd, check=True)
            logging.debug(cp)
            reportfile.write('\n![img]({}.png)\n'.format(filename))

    def split_assocs(self, root_target : TargetClass, ontology : Ontology = None):
        logging.info('Splitting assocs on: {} // {}'.format(root_target, ontology))
        aset = self.assocs
        if ontology is None:
            ontology = aset.ontology
        fmap = {}
        tmap = {}
        for subj in aset.subjects:
            targets = set()
            features = set()
            for c in aset.annotations(subj):
                if root_target in ontology.ancestors(c, reflexive=True):
                    targets.add(c)
                else:
                    features.add(c)
            fmap[subj] = features
            tmap[subj] = targets
        self.assocs = AssociationSet(ontology=ontology, association_map=fmap)
        self.target_assocs = AssociationSet(ontology=ontology, association_map=tmap)
        logging.info('Split; f={} t={}'.format(self.assocs, self.target_assocs))
            
            
    
