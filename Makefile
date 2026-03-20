# ===========================================================================
# LOGGUARD - CROSS-PLATFORM MAKEFILE
# ===========================================================================

# OS detection
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    SHELL := pwsh.exe
    .SHELLFLAGS := -NoProfile -Command
    PYTHON := python
    RM := Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    MKDIR := New-Item -ItemType Directory -Force -Path
    SEP := \\
    NULLDEV := $$null
else
    DETECTED_OS := $(shell uname -s)
    PYTHON := python3
    RM := rm -rf
    MKDIR := mkdir -p
    SEP := /
    NULLDEV := /dev/null
endif

# ANSI colors (work in modern PowerShell and Unix terminals)
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
BLUE   := \033[0;34m
NC     := \033[0m

# Directories
SRC_DIR      := logguard
TEST_DIR     := tests
EXAMPLES_DIR := examples
ARTIFACTS_DIR := build
COVERAGE_DIR := $(ARTIFACTS_DIR)$(SEP)coverage
DOCS_DIR     := $(ARTIFACTS_DIR)$(SEP)docs

.DEFAULT_GOAL := help

# ===========================================================================
# TESTING
# ===========================================================================

.PHONY: test test-fast test-cov
test:
	@printf "$(YELLOW)Running tests with coverage...$(NC)\n"
	@$(PYTHON) -m pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html:$(COVERAGE_DIR)
	@printf "$(GREEN)Tests completed$(NC)\n"
	@printf "$(BLUE)Coverage report: $(COVERAGE_DIR)$(SEP)index.html$(NC)\n\n"

test-fast:
	@printf "$(YELLOW)Running fast tests (no coverage)...$(NC)\n"
	@$(PYTHON) -m pytest $(TEST_DIR) -v
	@printf "$(GREEN)Tests completed$(NC)\n\n"

test-cov:
	@printf "$(YELLOW)Running tests + HTML coverage report...$(NC)\n"
	@$(PYTHON) -m pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html:$(COVERAGE_DIR) --cov-report=term
	@printf "$(GREEN)Coverage report generated$(NC)\n"
	@printf "$(BLUE)Open: $(COVERAGE_DIR)$(SEP)index.html$(NC)\n\n"

# ===========================================================================
# CODE QUALITY
# ===========================================================================

.PHONY: lint lint-fix format format-check typecheck quality pre-commit
lint:
	@printf "$(YELLOW)Running Ruff linter...$(NC)\n"
	@$(PYTHON) -m ruff check $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)
	@printf "$(GREEN)Linting completed$(NC)\n\n"

lint-fix:
	@printf "$(YELLOW)Running Ruff linter with auto-fix...$(NC)\n"
	@$(PYTHON) -m ruff check --fix $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)
	@printf "$(GREEN)Linting and auto-fix completed$(NC)\n\n"

format:
	@printf "$(YELLOW)Formatting code with Ruff...$(NC)\n"
	@$(PYTHON) -m ruff format $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)
	@$(PYTHON) -m ruff check --fix $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)
	@printf "$(GREEN)Code formatted$(NC)\n\n"

format-check:
	@printf "$(YELLOW)Checking code formatting...$(NC)\n"
	@$(PYTHON) -m ruff format --check $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)
	@printf "$(GREEN)Formatting check passed$(NC)\n\n"

typecheck:
	@printf "$(YELLOW)Running mypy type checker...$(NC)\n"
	@$(PYTHON) -m mypy $(SRC_DIR)
	@printf "$(GREEN)Type checking completed$(NC)\n\n"

quality: lint format-check typecheck
	@printf "$(GREEN)All quality checks passed$(NC)\n\n"

pre-commit:
	@printf "$(YELLOW)Running pre-commit hooks on all files...$(NC)\n"
	@pre-commit run --all-files
	@printf "$(GREEN)Pre-commit checks completed$(NC)\n\n"

# ===========================================================================
# CLEANUP
# ===========================================================================

.PHONY: clean clean-pycache clean-coverage clean-docs

clean: clean-pycache clean-coverage clean-docs
	@printf "$(YELLOW)Removing all artifacts...$(NC)\n"
ifeq ($(DETECTED_OS),Windows)
	@if (Test-Path $(ARTIFACTS_DIR)) { $(RM) $(ARTIFACTS_DIR) }
	@if (Test-Path .pytest_cache) { $(RM) .pytest_cache }
	@if (Test-Path .mypy_cache) { $(RM) .mypy_cache }
	@if (Test-Path .ruff_cache) { $(RM) .ruff_cache }
	@if (Test-Path dist) { $(RM) dist }
	@if (Test-Path build) { $(RM) build }
	@if (Test-Path app.log) { $(RM) app.log }
	@if (Test-Path *.egg-info) { $(RM) *.egg-info }
else
	@$(RM) $(ARTIFACTS_DIR) .pytest_cache .mypy_cache .ruff_cache dist build app.log *.egg-info
endif
	@printf "$(GREEN)Cleaned all artifacts$(NC)\n\n"

clean-pycache:
	@printf "$(YELLOW)Removing Python cache files...$(NC)\n"
ifeq ($(DETECTED_OS),Windows)
	@Get-ChildItem -Path . -Include __pycache__,*.pyc,*.pyo -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
else
	@find . -type d -name __pycache__ -exec $(RM) {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
endif
	@printf "$(GREEN)Python cache cleaned$(NC)\n\n"

clean-coverage:
	@printf "$(YELLOW)Removing coverage reports...$(NC)\n"
ifeq ($(DETECTED_OS),Windows)
	@if (Test-Path $(COVERAGE_DIR)) { $(RM) $(COVERAGE_DIR) }
	@if (Test-Path .coverage) { $(RM) .coverage }
	@if (Test-Path htmlcov) { $(RM) htmlcov }
else
	@$(RM) $(COVERAGE_DIR) .coverage htmlcov
endif
	@printf "$(GREEN)Coverage reports cleaned$(NC)\n\n"

clean-docs:
	@printf "$(YELLOW)Removing documentation build...$(NC)\n"
ifeq ($(DETECTED_OS),Windows)
	@if (Test-Path $(DOCS_DIR)) { $(RM) $(DOCS_DIR) }
else
	@$(RM) $(DOCS_DIR)
endif
	@printf "$(GREEN)Documentation cleaned$(NC)\n\n"

# ===========================================================================
# DOCUMENTATION
# ===========================================================================

.PHONY: docs docs-serve
docs:
	@printf "$(YELLOW)Building documentation with pdoc...$(NC)\n"
	@$(MKDIR) $(DOCS_DIR)
	@$(PYTHON) -m pdoc $(SRC_DIR) -o $(DOCS_DIR)
	@printf "$(GREEN)Documentation generated in $(DOCS_DIR)$(NC)\n\n"

docs-serve:
	@printf "$(YELLOW)Serving documentation on http://localhost:8080...$(NC)\n"
	@printf "$(YELLOW)   Press Ctrl+C to stop$(NC)\n\n"
	@$(PYTHON) -m pdoc $(SRC_DIR) --port 8080

# ===========================================================================
# INSTALL & PACKAGING
# ===========================================================================

.PHONY: install install-dev build
install:
	@printf "$(YELLOW)Installing package in editable mode...$(NC)\n"
	@$(PYTHON) -m pip install -e .
	@printf "$(GREEN)Installation complete$(NC)\n\n"

install-dev:
	@printf "$(YELLOW)Installing with development dependencies...$(NC)\n"
	@$(PYTHON) -m pip install -e ".[dev]"
	@printf "$(GREEN)Dev installation complete$(NC)\n\n"

build: clean
	@printf "$(YELLOW)Building sdist and wheel...$(NC)\n"
	@$(PYTHON) -m build
	@printf "$(GREEN)Build complete$(NC)\n\n"

# ===========================================================================
# PUBLISH
# ===========================================================================

.PHONY: publish-test publish
publish-test: build
	@printf "$(YELLOW)Uploading to TestPyPI...$(NC)\n"
	@$(PYTHON) -m twine upload --repository testpypi dist/*
	@printf "$(GREEN)Upload to TestPyPI complete$(NC)\n\n"

publish: build
	@printf "$(YELLOW)Uploading to PyPI...$(NC)\n"
	@$(PYTHON) -m twine upload dist/*
	@printf "$(GREEN)Upload to PyPI complete$(NC)\n\n"

# ===========================================================================
# HELP
# ===========================================================================

.PHONY: help
help:
	@printf "$(BLUE)Logguard Development Makefile$(NC)\n"
	@printf "====================================\n\n"
	@printf "Available commands:\n"
	@printf "  $(YELLOW)make help$(NC)               Show this help\n\n"
	@printf "Testing:\n"
	@printf "  $(YELLOW)make test$(NC)               Run tests with coverage\n"
	@printf "  $(YELLOW)make test-fast$(NC)          Run tests without coverage\n"
	@printf "  $(YELLOW)make test-cov$(NC)           Tests + HTML coverage report\n\n"
	@printf "Code Quality:\n"
	@printf "  $(YELLOW)make lint$(NC)               Run Ruff linter\n"
	@printf "  $(YELLOW)make lint-fix$(NC)           Run Ruff with auto-fix\n"
	@printf "  $(YELLOW)make format$(NC)             Format code with Ruff\n"
	@printf "  $(YELLOW)make format-check$(NC)       Check formatting without changes\n"
	@printf "  $(YELLOW)make typecheck$(NC)          Run mypy type checker\n"
	@printf "  $(YELLOW)make quality$(NC)            lint + format-check + typecheck\n"
	@printf "  $(YELLOW)make pre-commit$(NC)         Run pre-commit hooks\n\n"
	@printf "Cleanup:\n"
	@printf "  $(YELLOW)make clean$(NC)              Remove all build artifacts\n"
	@printf "  $(YELLOW)make clean-pycache$(NC)      Remove Python cache files\n"
	@printf "  $(YELLOW)make clean-coverage$(NC)     Remove coverage reports\n"
	@printf "  $(YELLOW)make clean-docs$(NC)         Remove documentation build\n\n"
	@printf "Documentation:\n"
	@printf "  $(YELLOW)make docs$(NC)               Build documentation with pdoc\n"
	@printf "  $(YELLOW)make docs-serve$(NC)         Serve live docs (localhost:8080)\n\n"
	@printf "Installation & Packaging:\n"
	@printf "  $(YELLOW)make install$(NC)            Install in editable mode\n"
	@printf "  $(YELLOW)make install-dev$(NC)        Install with dev dependencies\n"
	@printf "  $(YELLOW)make build$(NC)              Build sdist + wheel\n"
	@printf "  $(YELLOW)make publish-test$(NC)       Upload to TestPyPI\n"
	@printf "  $(YELLOW)make publish$(NC)            Upload to PyPI\n\n"
	@printf "Detected OS: $(DETECTED_OS)\n\n"
