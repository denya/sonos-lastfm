# Load environment variables from .env file
ifneq (,$(wildcard .env))
    include .env
    export
endif

.PHONY: check-types check-all install-dev clean setup install run versions version help release build-package update-version publish-package verify-package

# Python version to use
PYTHON_VERSION := 3.14.2

# Source files
PYTHON_FILES := src/sonos_lastfm

# Install development dependencies
install-dev:
	uv pip install mypy ruff types-setuptools hatchling

# Check types with mypy
check-types:
	mypy --strict --python-version=3.14 $(PYTHON_FILES)

# Run ruff type checking and linting
check-ruff:
	ruff check --select=ALL --target-version=py314 $(PYTHON_FILES)

# Run all checks
check-all: check-types check-ruff

# Clean up cache directories and build artifacts
clean:
	rm -rf .mypy_cache .ruff_cache __pycache__ */__pycache__ dist build *.egg-info

# Setup Python environment
setup:
	@echo "Setting up Python environment..."
	uv venv
	@echo "Python environment setup complete. Run 'make install' to install dependencies."

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv pip install -r requirements.txt
	uv pip install -e .
	@echo "Dependencies installed successfully."

# Run the scrobbler
run:
	@echo "Running Sonos Last.fm scrobbler..."
	uv run -m sonos_lastfm

# Show available Python versions
versions:
	@echo "Available Python versions:"
	uv python list

# Show current Python version
version:
	@echo "Current Python version:"
	uv python --version

# Update version in all files
update-version:
	@if [ -z "$(NEW_VERSION)" ]; then \
		echo "Error: NEW_VERSION is not set"; \
		exit 1; \
	fi
	@echo "Updating version to $(NEW_VERSION)"
	@sed -i '' "s/version = \"[0-9.]*\"/version = \"$(NEW_VERSION)\"/" pyproject.toml
	@sed -i '' "s/__version__ = \"[0-9.]*\"/__version__ = \"$(NEW_VERSION)\"/" src/sonos_lastfm/__init__.py

# Build Python package
build-package:
	@echo "Building package..."
	uv pip install hatchling
	uv build --no-sources

# Publish package to PyPI
publish-package:
	@echo "Publishing to PyPI..."
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		echo "Error: PYPI_TOKEN not found in .env file"; \
		exit 1; \
	fi
	uv publish --token $(PYPI_TOKEN)

# Verify package installation
verify-package:
	@echo "Verifying package installation..."
	uv run --with sonos-lastfm --no-project -- python -c "import sonos_lastfm"

# Full release process
release:
	@echo "Starting release process..."
	@echo "Current version: $$(grep -o 'version = "[0-9.]*"' pyproject.toml | cut -d'"' -f2)"
	@read -p "Enter new version: " version; \
	make clean && \
	make update-version NEW_VERSION=$$version && \
	make build-package && \
	make publish-package && \
	make verify-package && \
	echo "Release v$$version completed successfully!"

# Help
help:
	@echo "Available commands:"
	@echo "  make setup          - Set up Python environment with uv"
	@echo "  make install       - Install project dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make check-types   - Run mypy type checker"
	@echo "  make check-ruff    - Run ruff linter"
	@echo "  make check-all     - Run all checks"
	@echo "  make clean         - Clean up generated files"
	@echo "  make run           - Run the scrobbler"
	@echo "  make versions      - Show available Python versions"
	@echo "  make version       - Show current Python version"
	@echo "  make release       - Full release process (clean, version, build, check, commit, tag, publish)"
	@echo "  make verify-package - Verify package installation"
	@echo "  make help          - Show this help message" 
