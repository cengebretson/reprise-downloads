PYTHON ?= python3
.PHONY: help test
help:
	@printf '%s\n' 'test    Run offline release-integrity tests' 'See docs/RELEASING.md for draft releases; packages are GitHub assets, not Git files.'
test:
	$(PYTHON) -B -m unittest discover -s tests
