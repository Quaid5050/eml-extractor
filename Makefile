# eml-extractor — batch .eml → folders (headers, bodies, attachments)
#
#   make extract   process input/*.eml
#   make clean     clear output/
#   make help

SHELL := /bin/bash

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
INPUT_DIR := $(ROOT)/input
OUTPUT_DIR := $(ROOT)/output
PYTHON ?= python3
EXTRACT := $(ROOT)/extract.py
WEB_DIR := $(ROOT)/web
VENV ?= $(ROOT)/.venv

.PHONY: help extract clean dirs web web-install

help:
	@echo "eml-extractor"
	@echo ""
	@echo "  make extract      Process all .eml in input/ -> output/<name>/"
	@echo "  make clean        Remove generated files under output/"
	@echo "  make web-install  Create .venv and install Django (web UI)"
	@echo "  make web          Run web UI at http://127.0.0.1:8765/"
	@echo ""
	@echo "  input/   $(INPUT_DIR)"
	@echo "  output/  $(OUTPUT_DIR)"

dirs:
	@mkdir -p "$(INPUT_DIR)" "$(OUTPUT_DIR)"
	@touch "$(INPUT_DIR)/.gitkeep" "$(OUTPUT_DIR)/.gitkeep"

extract: dirs
	@$(PYTHON) "$(EXTRACT)"

clean: dirs
	@find "$(OUTPUT_DIR)" -mindepth 1 ! -name '.gitkeep' -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned $(OUTPUT_DIR)"

web-install:
	@test -d "$(VENV)" || $(PYTHON) -m venv "$(VENV)"
	@"$(VENV)/bin/pip" install -q -r "$(ROOT)/requirements-web.txt"
	@echo "Web dependencies installed in $(VENV)"

web: web-install
	@mkdir -p "$(WEB_DIR)/media/jobs"
	@cd "$(WEB_DIR)" && "$(VENV)/bin/python" manage.py runserver 8765
