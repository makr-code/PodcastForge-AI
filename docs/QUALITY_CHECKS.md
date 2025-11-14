# Quality Check & Testing Guide

## 🔍 Offline Quality Checks für PodcastForge-AI

Dieses Dokument beschreibt das lokale Quality-Check-System ohne GitHub Actions.

---

## ⚡ Quick Start

```bash
# 1. Development Setup
make dev-setup

# 2. Alle Checks ausführen
make check

# 3. Auto-Fix für Formatierung
make format

# 4. Tests ausführen
make test
```

---

## 🛠️ Verfügbare Tools

### 1. Black (Code Formatting)
Automatische Code-Formatierung nach PEP 8.

```bash
# Check only
black --check src/ tests/

# Auto-fix
black src/ tests/

# Via Make
make format
```

**Konfiguration:** `pyproject.toml` (line-length=100)

### 2. isort (Import Sorting)
Sortiert Imports automatisch.

```bash
# Check only
isort --check-only src/ tests/

# Auto-fix
isort src/ tests/

# Via Make
make format
```

**Konfiguration:** `pyproject.toml` (profile="black")

### 3. Flake8 (Linting)
Python-Linter für Code-Quality.

```bash
# Run linter
flake8 src/ tests/

# Via Make
make lint
```

**Konfiguration:** `.flake8`
- Max line length: 100
- Ignored: E203, W503, E501, E402

### 4. MyPy (Type Checking)
Static Type Checker.

```bash
# Type check
mypy src/ --ignore-missing-imports

# Via Make
make lint
```

**Konfiguration:** `pyproject.toml`
- Python version: 3.8+
- Ignore missing imports: true

### 5. Bandit (Security Scanning)
Security-Linter für Python.

```bash
# Scan for security issues
bandit -r src/ -c pyproject.toml

# Via Make
make security
```

**Konfiguration:** `pyproject.toml`
- Exclude: tests, build, dist
- Skips: B101 (assert_used), B601 (paramiko_calls)

### 6. Safety (Dependency Security)
Check dependencies for known vulnerabilities.

```bash
# Check dependencies
safety check

# JSON output
safety check --json

# Via Make
make security
```

### 7. Interrogate (Docstring Coverage)
Check docstring coverage.

```bash
# Check coverage
interrogate -vv --fail-under=80 src/

# Via Make
make doccheck
```

**Konfiguration:** `pyproject.toml`
- Minimum coverage: 80%
- Ignore: `__init__` modules

### 8. Pytest (Unit Testing)
Test-Framework mit Coverage.

```bash
# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Fast (no coverage)
pytest tests/ -v --no-cov

# Via Make
make test
make test-fast
```

**Konfiguration:** `pyproject.toml`
- Coverage target: src/
- HTML report: htmlcov/

---

## 📋 Pre-Commit Hooks

Automatische Quality-Checks vor jedem Commit.

### Installation

```bash
# Install hooks
make pre-commit

# Oder manuell
pre-commit install
```

### Verwendung

```bash
# Automatisch bei jedem Commit
git commit -m "fix: something"
# -> Pre-commit hooks laufen automatisch

# Manuell auf allen Dateien
pre-commit run --all-files

# Via Make
make pre-commit-run
```

### Konfigurierte Hooks

1. **Black** - Code Formatting
2. **isort** - Import Sorting
3. **Flake8** - Linting
4. **Bandit** - Security
5. **MyPy** - Type Checking
6. **YAML Validation**
7. **Trailing Whitespace**
8. **Large Files Check**
9. **Merge Conflict Check**
10. **Interrogate** - Docstring Coverage
11. **Safety** - Dependency Security

---

## 🚀 Workflow

### Vor dem Commit

```bash
# 1. Auto-fix formatting
make format

# 2. Check code quality
make check

# 3. Run tests
make test

# 4. Wenn alles grün:
git add -A
git commit -m "feat: your message"
```

### CI-Workflow (komplett)

```bash
# Gesamter CI-Workflow offline
make ci

# Entspricht:
# - make format-check
# - make lint
# - make security
# - make doccheck
# - make test
```

### Fix Quality Issues

```bash
# Auto-fix script
./scripts/fix_quality.sh

# Oder via Make
make format
```

---

## 📊 Coverage Reports

### Terminal Output

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### HTML Report

```bash
pytest tests/ --cov=src --cov-report=html
# Open: htmlcov/index.html
```

### XML Report (für CI)

```bash
pytest tests/ --cov=src --cov-report=xml
# Generiert: coverage.xml
```

---

## 🎯 Quality Standards

### Code Coverage
- **Minimum:** 80%
- **Target:** 90%

### Docstring Coverage
- **Minimum:** 80%
- **Target:** 95%

### Linting
- **Max Complexity:** 15
- **Max Line Length:** 100

### Security
- **Bandit:** 0 high/medium issues
- **Safety:** 0 known vulnerabilities

---

## 🐛 Troubleshooting

### MyPy Errors

```bash
# Ignore missing imports
mypy src/ --ignore-missing-imports

# Ignore specific file
mypy src/ --exclude 'src/podcastforge/some_file.py'
```

### Flake8 Errors

```bash
# Check specific file
flake8 src/podcastforge/some_file.py

# Ignore specific rule
# Add to .flake8: extend-ignore = E203,W503,YOUR_RULE
```

### Pre-Commit Issues

```bash
# Clear cache
pre-commit clean

# Reinstall hooks
pre-commit uninstall
pre-commit install

# Update hooks
pre-commit autoupdate
```

### Coverage Too Low

```bash
# Show uncovered lines
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML report for details
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 📝 Cheat Sheet

```bash
# Setup
make dev-setup              # Initial setup
make install-dev            # Install dependencies

# Quality Checks
make check                  # All checks
make lint                   # Flake8 + MyPy
make format                 # Black + isort
make security               # Bandit + Safety
make doccheck               # Docstring coverage
make test                   # Tests + Coverage

# Pre-Commit
make pre-commit             # Install hooks
make pre-commit-run         # Run manually

# Cleanup
make clean                  # Clean cache
make clean-all              # Clean everything

# CI
make ci                     # Full CI workflow
```

---

## 🔧 Configuration Files

- **pyproject.toml** - Main config (Black, isort, MyPy, Pytest, Coverage, Bandit, Interrogate)
- **.flake8** - Flake8 config
- **.pre-commit-config.yaml** - Pre-commit hooks
- **scripts/check_quality.sh** - Main check script
- **scripts/fix_quality.sh** - Auto-fix script
- **scripts/setup_dev.sh** - Dev setup script

---

## 📚 Best Practices

1. **Vor jedem Commit:**
   ```bash
   make format && make check
   ```

2. **Regelmäßig:**
   ```bash
   make security  # Dependency vulnerabilities
   ```

3. **Bei Pull Requests:**
   ```bash
   make ci  # Full CI workflow
   ```

4. **Code Review:**
   ```bash
   make test  # Coverage report
   make doccheck  # Docstring check
   ```

---

## 🎓 Weitere Ressourcen

- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Pre-Commit Documentation](https://pre-commit.com/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Version:** 1.2.0  
**Letzte Aktualisierung:** November 14, 2024
