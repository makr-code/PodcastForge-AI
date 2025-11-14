#!/bin/bash
# Quality Check Script für PodcastForge-AI
# Führt alle Code-Quality-Checks offline durch

set -e  # Exit on error

echo "=========================================="
echo "🔍 PodcastForge-AI Quality Check"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_TOTAL=0

# Function to run check
run_check() {
    local name=$1
    local command=$2
    
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    echo -e "${YELLOW}[$CHECKS_TOTAL] Running: $name${NC}"
    
    if eval "$command"; then
        echo -e "${GREEN}✓ $name passed${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        echo ""
        return 0
    else
        echo -e "${RED}✗ $name failed${NC}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        echo ""
        return 1
    fi
}

# CD to project root
cd "$(dirname "$0")/.."

echo "Project: $(pwd)"
echo ""

# 1. Black (Code Formatting Check)
run_check "Black (Code Formatting)" \
    "black --check --diff src/ tests/ || true"

# 2. isort (Import Sorting Check)
run_check "isort (Import Sorting)" \
    "isort --check-only --diff src/ tests/ || true"

# 3. Flake8 (Linting)
run_check "Flake8 (Linting)" \
    "flake8 src/ tests/ || true"

# 4. MyPy (Type Checking)
run_check "MyPy (Type Checking)" \
    "mypy src/ --ignore-missing-imports --no-strict-optional || true"

# 5. Bandit (Security Scanning)
run_check "Bandit (Security)" \
    "bandit -r src/ -c pyproject.toml || true"

# 6. Safety (Dependency Security)
run_check "Safety (Dependencies)" \
    "safety check --json || true"

# 7. Interrogate (Docstring Coverage)
run_check "Interrogate (Docstrings)" \
    "interrogate -vv --fail-under=80 src/ || true"

# 8. Pytest (Unit Tests)
run_check "Pytest (Unit Tests)" \
    "pytest tests/ -v --cov=src --cov-report=term-missing || true"

# Summary
echo "=========================================="
echo "📊 Summary"
echo "=========================================="
echo -e "Total Checks: $CHECKS_TOTAL"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Code is ready for commit.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues before committing.${NC}"
    exit 1
fi
