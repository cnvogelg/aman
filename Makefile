# Makefile for aman

BUILD_DIR = build
DIST_DIR = dist

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: init format
.PHONY: clean clean_all clean_git clean_py
.PHONY: install sdist bdist upload

help:
	@echo "init        initialize project"
	@echo
	@echo "format      format source code with black"
	@echo
	@echo "clean       clean dist"
	@echo "clean_git   clean non-git files"
	@echo "clean_py    remove compiled .pyc files"
	@echo
	@echo "sdist       build source dist"
	@echo "bdist       build bin dist wheel"
	@echo "upload      upload bdist with twine to pypi"

init:
	$(PIP) install --upgrade setuptools pip
	$(PIP) install --upgrade -r requirements-dev.txt
	$(PIP) install --upgrade --editable .

format:
	black .

# clean
clean:
	rm -rf $(DIST_DIR) $(BUILD_DIR)

clean_git:
	git clean -fxd

clean_py:
	find . -name *.pyc -exec rm {} \;

# install, distrib
sdist:
	$(PYTHON) -m build -s

bdist:
	$(PYTHON) -m build -w

upload: clean bdist
	twine upload dist/*
