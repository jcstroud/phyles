include PackageInfo.cfg
include Makefile.inc

META = $(PACKAGE).__meta__
BUNDLE = $(PACKAGE)-$(RELEASE)
DOCDEST = $(BUILDDIR)/docs
DOCZIP = $(BUNDLE)-docs.zip
DOCPDF = $(PACKAGE).pdf

VERMODULE = $(PACKAGE)/_version.py

PRODUCTS = LICENSE.txt $(VERMODULE) $(HTMLDIR) $(DOCPDF)

all : prune $(DOCDEST) $(PRODUCTS) sdist

LICENSE.txt : $(INFOFILE)
	$(PYTHON) -c 'exec("import configobj; \
                            p = configobj.ConfigObj(\"PackageInfo.cfg\", \
                                                    list_values=False); \
                            t = open(\"LICENSE.tmplt\").read(); \
                            s = t % p; \
                            open(\"LICENSE.txt\", \"w\").write(s)")'

$(DOCDEST) :
	mkdir -p $(DOCDEST)

$(HTMLDIR) : $(DOCDEST) $(INFOFILE)
	cd $(DOCDIR) ; rm -rf _build/html ; make html
	cp -r $(DOCDIR)/_build/html $(HTMLDIR)

$(DOCZIP) : $(HTMLDIR)
	-rm -f $(DOCZIP)
	cd $(HTMLDIR) ; zip -ry $(CURDIR)/$(DOCZIP) *
	mv $(DOCZIP) $(DOCDEST)

$(DOCPDF) : $(DOCDEST)
	cd $(DOCDIR) ; rm -rf _build/latex ; make latexpdf
	cp $(DOCDIR)/_build/latex/$(PACKAGE).pdf $(PDFDIR)/$(DOCPDF)

pdf : $(DOCPDF)

$(VERMODULE) :
	$(ECHO) '__version__ = "$(RELEASE)"' > $(VERMODULE)

sdist : prune $(VERMODULE)
	-rm dist/$(BUNDLE).tar.gz
	$(PYTHON) setup.py sdist

install : all
	$(PYTHON) setup.py install

build : all
	$(PYTHON) setup.py build

pypi-build-docs : $(DOCZIP)

pypi-upload-docs : $(HTMLDIR)
	python setup.py upload_docs --upload-dir=$(HTMLDIR)

pypi-upload : all pypi-upload-docs
	$(PYTHON) setup.py sdist upload

test : clean
	$(PYTHON) setup.py test
clean :
	$(ECHO) Cleaning up in `pwd`.
	-rm -rf $(PRODUCTS)

prune :
	$(PYTHON) -c 'exec("import phyles; \
                            import logging; \
                            logging.basicConfig(level=logging.INFO); \
                            phyles.prune([\"*~\", \"*.pyc\"], \
                                         doit=True)")'

scrub : clean prune
	-rm -rf dist/ build/ $(PACKAGE).egg-info/
	cd docsrc ; make clean
