.PHONY: test lint install-local clean help

help:
	@echo "Available targets:"
	@echo "  test            Run pytest with coverage"
	@echo "  lint            Run ruff linter (if installed)"
	@echo "  install-local   Install plugin to local HERMES_HOME"
	@echo "  install-skill   Copy skill to local HERMES_HOME"
	@echo "  clean           Remove build artifacts and cache"
	@echo "  dev-install     Install package in editable mode with dev deps"

test:
	python -m pytest tests/ -v

lint:
	@command -v ruff >/dev/null 2>&1 && ruff check plugin/ tests/ || echo "ruff not installed; run: pip install ruff"

install-local:
	@echo "Installing plugin to ~/.hermes/plugins/example_plugin/"
	mkdir -p ~/.hermes/plugins/example_plugin
	cp -r plugin/* ~/.hermes/plugins/example_plugin/
	@echo "Done. Start Hermes and check /plugins to verify."

install-skill:
	@echo "Installing skill to ~/.hermes/skills/example-skill/"
	mkdir -p ~/.hermes/skills/example-skill
	cp skill/* ~/.hermes/skills/example-skill/
	@echo "Done. Start Hermes and check for /example-skill command."

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ .coverage htmlcov/ build/ dist/ *.egg-info/
	@echo "Cleaned."

dev-install:
	pip install -e ".[dev]"
