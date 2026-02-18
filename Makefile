.PHONY: all get_model install test build freeze

ifeq ($(OS),Windows_NT)
  OS_SHELL            := powershell
  DOWNLOAD_SPACY_MODEL := resources/scripts/download-spacy-model.ps1
else
  OS_SHELL            := bash
  DOWNLOAD_SPACY_MODEL := ./resources/scripts/download-spacy-model.sh
endif

get_model:
	$(OS_SHELL) $(DOWNLOAD_SPACY_MODEL)

install:
	poetry lock
	poetry check
	poetry update
	poetry install

test:
	poetry run pytest --disable-pytest-warnings

build: install test
	poetry build

freeze:
	poetry run pip freeze > requirements.txt
	poetry run python -m pip install --upgrade pip

all: get_model build freeze
