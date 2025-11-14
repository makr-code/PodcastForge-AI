.PHONY: help install test clean run demo docker dev lint format docs

help:
	@echo "PodcastForge-AI Makefile"
	@echo ""
	@echo "Verfügbare Befehle:"
	@echo "  make install       - Installiere alle Abhängigkeiten"
	@echo "  make install-dev   - Installiere Entwicklungs-Dependencies"
	@echo "  make setup         - Komplettes Setup (inkl. Ollama)"
	@echo "  make demo          - Führe Demo-Podcast aus"
	@echo "  make test          - Führe Tests aus"
	@echo "  make lint          - Code-Linting"
	@echo "  make format        - Code-Formatierung mit black"
	@echo "  make clean         - Aufräumen"
	@echo "  make docker        - Docker-Container bauen"
	@echo "  make docker-run    - Docker-Container starten"
	@echo "  make docs          - Dokumentation generieren"

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

setup:
	@echo "🚀 PodcastForge-AI Setup"
	@chmod +x setup.sh
	@./setup.sh

demo:
	python examples/demo.py

test:
	pytest tests/ -v --cov=podcastforge

lint:
	flake8 src/podcastforge
	mypy src/podcastforge

format:
	black src/podcastforge tests examples

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

docker:
	docker-compose build

docker-run:
	docker-compose up

docs:
	cd docs && make html
