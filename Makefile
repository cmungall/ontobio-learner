OBO = http://purl.obolibrary.org/obo
all:
	echo hi

test: t1 t2
t1:
	python tests/learn_test.py
	pandoc -i target/index.md -o target/index.html
t2:
	python tests/pheno_test.py
	pandoc -i target/from_phenotype/index.md -o target/from_phenotype/index.html

clean:
	rm -rf target/* || echo

PHAF= phenotype_annotations.pombase.phaf
data/$(PHAF).gz:
	wget ftp://ftp.pombase.org/pombe/annotations/Phenotype_annotations/$(PHAF).gz -O $@

data/phenotype_annotation.hpoa:
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastStableBuild/artifact/misc/phenotype_annotation.tab -O $@ && touch $@
data/omim.hpoa: data/phenotype_annotation.hpoa
	grep ^OMIM $< > $@
data/mondo.hpoa: data/mondo.obo
	./bin/mondo2hpoa.pl $< > $@
data/combined.hpoa: data/mondo.hpoa data/omim.hpoa
	cat $^ | ./bin/hpoa-new2old.pl > $@

data/mondo.obo:
	curl -L -s $(OBO)/mondo.obo -o $@
data/hp.obo:
	curl -L -s $(OBO)/hp.obo -o $@
data/mondo.json:
	curl -L -s $(OBO)/mondo.json -o $@
data/hp.json:
	robot convert -I $(OBO)/hp.owl -o $@
data/mondo-basic.json:
	robot convert -I $(OBO)/mondo.obo -o $@
data/mondo-hp.json: data/hp.obo data/mondo.obo
	owltools $^ --merge-support-ontologies -o -f json $@

learn-mondo:
	./bin/ob-learn.py learn  -d target-mondo -r data/mondo-hp.json -i data/combined.hpoa -R MONDO:0000001
