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

.PHONY: help extract clean dirs

help:
	@echo "eml-extractor"
	@echo ""
	@echo "  make extract   Process all .eml in input/ -> output/<name>/"
	@echo "  make clean     Remove generated files under output/"
	@echo "  make dirs      Create input/ and output/"
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
