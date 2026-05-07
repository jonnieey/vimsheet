# Makefile for Sphinx documentation
#

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile clean build-html linkcheck coverage doctest epub latexpdf serve

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf $(BUILDDIR)
	rm -rf $(SOURCEDIR)/_autosummary
	rm -rf $(SOURCEDIR)/locale

build-html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" -W --keep-going $(O)

linkcheck:
	@$(SPHINXBUILD) -M linkcheck "$(SOURCEDIR)" "$(BUILDDIR)" -b linkcheck $(SPHINXOPTS) $(O)

coverage:
	@$(SPHINXBUILD) -M coverage "$(SOURCEDIR)" "$(BUILDDIR)" -b coverage $(SPHINXOPTS) $(O)
	@echo "Coverage report written to $(BUILDDIR)/coverage/"

doctest:
	@$(SPHINXBUILD) -M doctest "$(SOURCEDIR)" "$(BUILDDIR)" -b doctest $(SPHINXOPTS) $(O)

epub:
	@$(SPHINXBUILD) -M epub "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

latexpdf:
	@$(SPHINXBUILD) -M latex "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "Running LaTeX to build PDF..."
	cd $(BUILDDIR)/latex && make all-pdf 2>/dev/null || echo "PDF build requires LaTeX to be installed"

serve:
	@echo "Starting documentation server at http://localhost:8000"
	@python3 -m http.server 8000 --directory $(BUILDDIR)/html

check: linkcheck doctest coverage

all: clean html epub latexpdf linkcheck doctest coverage
	@echo "All builds completed."

github:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)/github-pages" $(SPHINXOPTS) $(O)
	@echo "GitHub Pages build complete in $(BUILDDIR)/github-pages/"

offline:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)/offline" -A offline=True $(SPHINXOPTS) $(O)
	@$(SPHINXBUILD) -M epub "$(SOURCEDIR)" "$(BUILDDIR)/offline" $(SPHINXOPTS) $(O)
	@echo "Offline build complete in $(BUILDDIR)/offline/"
