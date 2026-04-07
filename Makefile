.PHONY: test lint install-local install-skill clean help dev-install

help:
	@echo "Available targets:"
	@echo "  test            Run pytest with verbose output"
	@echo "  lint            Run ruff linter (if installed)"
	@echo "  install-local   Install plugin to local HERMES_HOME"
	@echo "  install-skill   Copy skill to local HERMES_HOME"
	@echo "  clean           Remove build artifacts and cache"
	@echo "  dev-install     Install package in editable mode with dev deps"

test:
	python -m pytest tests/ -v

lint:
	@command -v ruff >/dev/null 2>&1 && ruff check __init__.py schemas.py tools.py tests/ || echo "ruff not installed; run: pip install ruff"

install-local:
	@echo "Installing native_extract plugin locally..."
	@mkdir -p $(HOME)/.hermes/plugins/native_extract_plugin
	@cp plugin.yaml $(HOME)/.hermes/plugins/native_extract_plugin/
	@cp __init__.py $(HOME)/.hermes/plugins/native_extract_plugin/
	@cp schemas.py $(HOME)/.hermes/plugins/native_extract_plugin/
	@cp tools.py $(HOME)/.hermes/plugins/native_extract_plugin/
	@echo "Done. Restart Hermes to load the plugin."

install-skill:
	@echo "Installing native_extract skill..."
	@mkdir -p $(HOME)/.hermes/skills/native_extract
	@cp skill/SKILL.md $(HOME)/.hermes/skills/native_extract/
	@echo "Done."

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ .coverage htmlcov/ build/ dist/ *.egg-info/
	@echo "Cleaned."

dev-install:
	pip install -e ".[dev]"
