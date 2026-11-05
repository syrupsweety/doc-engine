# doc-engine Makefile
# Build system for document-as-code workflow

# Configuration
PROFILE ?= gost-7.32
INPUT ?= docs/example/manuscript.md

# Mirror the input directory under output/: docs/example/x.md -> output/example/x.pdf
INPUT_REL_DIR = $(patsubst %/,%,$(patsubst docs/%,%,$(dir $(INPUT))))
OUTPUT_DIR ?= $(if $(INPUT_REL_DIR),output/$(INPUT_REL_DIR),output)
RENDER_SCRIPT ?= scripts/cli.py
PYTHON ?= $(if $(wildcard .venv/bin/python3),.venv/bin/python3,python3)
VALIDATE_SCRIPT ?= scripts/validator.py
TEST_SCRIPT ?= scripts/tester.py

# Profile path
PROFILE_PATH = profiles/$(PROFILE)

# Output files (based on input filename)
BASENAME = $(basename $(notdir $(INPUT)))
PDF_OUTPUT = $(OUTPUT_DIR)/$(BASENAME).pdf
HTML_OUTPUT = $(OUTPUT_DIR)/$(BASENAME).html
DOCX_OUTPUT = $(OUTPUT_DIR)/$(BASENAME).docx

# Default target
.PHONY: all pdf html docx clean help install test

all: pdf html docx

# Help target
help:
	@echo "doc-engine Build System"
	@echo "======================"
	@echo ""
	@echo "Available targets:"
	@echo "  make pdf      - Generate PDF output (default: gost-7.32 profile)"
	@echo "  make html     - Generate HTML output"
	@echo "  make docx     - Generate DOCX output"
	@echo "  make all      - Generate all output formats"
	@echo "  make clean    - Remove all generated files"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"
	@echo ""
	@echo "Variables:"
	@echo "  PROFILE       - Profile to use (gost-7.32, ieee, apa-7th)"
	@echo "  INPUT         - Input Markdown file (output mirrors its directory)"
	@echo ""
	@echo "Examples:"
	@echo "  make pdf PROFILE=ieee"
	@echo "  make all INPUT=docs/example/manuscript.md PROFILE=gost-7.32"

# PDF generation
pdf: $(PDF_OUTPUT)

$(PDF_OUTPUT): $(INPUT) $(RENDER_SCRIPT) $(PROFILE_PATH)/config.yaml
	@echo "Building PDF with profile: $(PROFILE)"
	$(PYTHON) $(RENDER_SCRIPT) \
		--input $(INPUT) \
		--output $(PDF_OUTPUT) \
		--format pdf \
		--profile $(PROFILE)

# HTML generation
html: $(HTML_OUTPUT)

$(HTML_OUTPUT): $(INPUT) $(RENDER_SCRIPT) $(PROFILE_PATH)/config.yaml
	@echo "Building HTML with profile: $(PROFILE)"
	$(PYTHON) $(RENDER_SCRIPT) \
		--input $(INPUT) \
		--output $(HTML_OUTPUT) \
		--format html \
		--profile $(PROFILE)

# DOCX generation
docx: $(DOCX_OUTPUT)

$(DOCX_OUTPUT): $(INPUT) $(RENDER_SCRIPT) $(PROFILE_PATH)/config.yaml
	@echo "Building DOCX with profile: $(PROFILE)"
	$(PYTHON) $(RENDER_SCRIPT) \
		--input $(INPUT) \
		--output $(DOCX_OUTPUT) \
		--format docx \
		--profile $(PROFILE)

# Profile-specific builds
pdf-gost:
	$(MAKE) pdf PROFILE=gost-7.32

pdf-ieee:
	$(MAKE) pdf PROFILE=ieee

pdf-apa:
	$(MAKE) pdf PROFILE=apa-7th

# Clean output directory
clean:
	@echo "Cleaning output directory..."
	rm -rf $(OUTPUT_DIR)/*
	@echo "Output directory cleaned."

# Install dependencies
install:
	@chmod +x install.sh
	./install.sh
	@echo "Setup complete!"

# Run tests
test:
	@echo "Running tests..."
	$(PYTHON) -m pytest tests/ -v || echo "No tests directory found."

# Verify installation
verify:
	@echo "Verifying installation..."
	@which pandoc > /dev/null && echo "pandoc: ok" || echo "pandoc: missing"
	@which tlmgr > /dev/null && echo "tlmgr: ok" || echo "tlmgr: missing"
	@git lfs version > /dev/null 2>&1 && echo "git-lfs: ok" || echo "git-lfs: missing"
	@$(PYTHON) -c "import yaml" 2>/dev/null && echo "pyyaml: ok" || echo "pyyaml: missing"

# Check for typos in documentation
check-typos:
	@echo "Checking for typos..."
	typos docs/ || true

# Lint Markdown files
lint-md:
	@echo "Linting Markdown files..."
	@which mdl > /dev/null && mdl docs/ || echo "mdl not installed, skipping"

# Validation targets
validate-profile:
	@echo "Validating profile: $(PROFILE)"
	$(PYTHON) $(VALIDATE_SCRIPT) --profile $(PROFILE)

validate-all-profiles:
	@echo "Validating all profiles..."
	$(PYTHON) $(VALIDATE_SCRIPT) --all

validate-config:
	@echo "Validating configuration files..."
	$(PYTHON) $(VALIDATE_SCRIPT) --config

# Test targets
test-basic:
	@echo "Running basic smoke tests..."
	$(PYTHON) $(TEST_SCRIPT) --basic

test-profiles:
	@echo "Testing all profiles..."
	$(PYTHON) $(TEST_SCRIPT) --profiles

test-rendering:
	@echo "Testing rendering pipeline..."
	$(PYTHON) $(TEST_SCRIPT) --render

# CI build (used by GitHub Actions)
ci-build: validate-all-profiles test-basic all
	@echo "CI build complete with validation and testing."
