.PHONY: help install test clean run demo docker dev lint format docs check security pre-commit

help:
	@echo "PodcastForge-AI Makefile"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Installiere alle Abhängigkeiten"
	@echo "  make install-dev   - Installiere Entwicklungs-Dependencies"
	@echo "  make setup         - Komplettes Setup (inkl. Ollama)"
	@echo "  make dev-setup     - Development environment setup"
	@echo ""
	@echo "Quality Checks (Offline):"
	@echo "  make check         - Alle Quality-Checks ausführen"
	@echo "  make lint          - Linting (flake8, mypy)"
	@echo "  make format        - Auto-format code (black, isort)"
	@echo "  make format-check  - Check formatting ohne Änderungen"
	@echo "  make security      - Security checks (bandit, safety)"
	@echo "  make doccheck      - Docstring coverage"
	@echo "  make test          - Tests mit Coverage"
	@echo ""
	@echo "Pre-Commit:"
	@echo "  make pre-commit    - Install pre-commit hooks"
	@echo "  make pre-commit-run - Run pre-commit on all files"
	@echo ""
	@echo "Ausführen:"
	@echo "  make demo          - Demo-Podcast ausführen"
	@echo "  make docker        - Docker-Container bauen"
	@echo "  make docker-run    - Docker-Container starten"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Build artifacts aufräumen"
	@echo "  make clean-all     - Alle generierten Dateien löschen"
	@echo ""

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

dev-setup:
	@chmod +x scripts/*.sh
	./scripts/setup_dev.sh

setup:
	@echo "🚀 PodcastForge-AI Setup"
	@chmod +x setup.sh
	@./setup.sh

# Quality Checks (Offline)
check:
	@chmod +x scripts/check_quality.sh
	./scripts/check_quality.sh

lint:
	@echo "Running Flake8..."
	flake8 src/ tests/
	@echo "Running MyPy..."
	mypy src/ --ignore-missing-imports --no-strict-optional

format:
	@chmod +x scripts/fix_quality.sh
	./scripts/fix_quality.sh

format-check:
	@echo "Checking Black..."
	black --check --diff src/ tests/
	@echo "Checking isort..."
	isort --check-only --diff src/ tests/

security:
	@echo "Running Bandit..."
	bandit -r src/ -c pyproject.toml
	@echo "Running Safety..."
	safety check --json || true

doccheck:
	interrogate -vv --fail-under=80 src/

# Testing
test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-fast:
	pytest tests/ -v --no-cov

# Pre-Commit
pre-commit:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate

demo:
	python examples/demo.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete

clean-all: clean
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml

# CI workflow (offline)
ci: format-check lint security doccheck test
	@echo "✓ All CI checks passed!"
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

docker:
	docker-compose build

docker-run:
	docker-compose up

docs:
	cd docs && make html
