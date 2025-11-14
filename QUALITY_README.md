# 🔍 Offline Quality Check System

Vollständiges lokales Quality-Check-System ohne GitHub Actions.

## ⚡ Quick Start

```bash
# 1. Development Setup (einmalig)
make dev-setup

# 2. Vor jedem Commit
make format  # Auto-fix formatting
make check   # Alle Checks

# 3. Commit (pre-commit hooks laufen automatisch)
git commit -m "feat: your message"
```

## 🛠️ Verfügbare Tools

### Formatierung & Linting
- **Black** - Code Formatting (PEP 8)
- **isort** - Import Sorting
- **Flake8** - Linting (max-line-length=100)
- **MyPy** - Type Checking

### Security
- **Bandit** - Security Scanner
- **Safety** - Dependency Vulnerability Check

### Testing
- **Pytest** - Unit Tests
- **Coverage** - Code Coverage (Target: 80%+)

### Documentation
- **Interrogate** - Docstring Coverage (Target: 80%+)

## 📋 Makefile Commands

```bash
make help          # Alle verfügbaren Commands
make check         # Alle Quality-Checks
make format        # Auto-fix Code
make test          # Tests mit Coverage
make security      # Security Checks
make ci            # Full CI workflow (offline)
```

## 🔧 Scripts

```bash
./scripts/check_quality.sh  # Alle Checks ausführen
./scripts/fix_quality.sh    # Auto-fix Formatierung
./scripts/setup_dev.sh      # Dev Environment Setup
```

## 📊 Pre-Commit Hooks

Automatisch bei jedem Commit:
- ✅ Black Formatting
- ✅ isort Import Sorting
- ✅ Flake8 Linting
- ✅ MyPy Type Checking
- ✅ Bandit Security
- ✅ YAML/JSON Validation
- ✅ Trailing Whitespace
- ✅ Large Files Check

```bash
# Install
make pre-commit

# Manual run
pre-commit run --all-files
```

## 📚 Dokumentation

Siehe [QUALITY_CHECKS.md](docs/QUALITY_CHECKS.md) für Details.

## ✅ Quality Standards

- **Code Coverage:** 80%+ (Target: 90%)
- **Docstring Coverage:** 80%+ (Target: 95%)
- **Max Line Length:** 100
- **Max Complexity:** 15
- **Security:** 0 high/medium issues

## 🎯 Workflow

```bash
# 1. Auto-fix
make format

# 2. Check
make check

# 3. Tests
make test

# 4. Commit
git commit -m "feat: something"
# -> Pre-commit hooks laufen automatisch
```

## 📁 Config Files

- `pyproject.toml` - Main config
- `.flake8` - Flake8 config
- `.pre-commit-config.yaml` - Pre-commit hooks

---

**Status:** ✅ Production Ready  
**Version:** 1.2.0
