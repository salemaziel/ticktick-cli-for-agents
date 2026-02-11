PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: test clean build dist-check release-check publish-testpypi publish-pypi

test:
	$(PYTHON) -m pytest -q

clean:
	rm -rf dist build

build: clean
	$(PYTHON) -m build

dist-check: build
	$(PYTHON) -m twine check dist/*

release-check: test dist-check

publish-testpypi:
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish-pypi:
	$(PYTHON) -m twine upload dist/*
