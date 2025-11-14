#!/bin/bash
# Development Environment Setup für PodcastForge-AI

set -e

echo "=========================================="
echo "🚀 PodcastForge-AI Development Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# CD to project root
cd "$(dirname "$0")/.."

echo "Project: $(pwd)"
echo ""

# 1. Install development dependencies
echo -e "${YELLOW}[1/4] Installing development dependencies...${NC}"
pip install -e ".[dev]" -q
echo -e "${GREEN}✓ Development dependencies installed${NC}"
echo ""

# 2. Install pre-commit hooks
echo -e "${YELLOW}[2/4] Installing pre-commit hooks...${NC}"
pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
echo ""

# 3. Make scripts executable
echo -e "${YELLOW}[3/4] Making scripts executable...${NC}"
chmod +x scripts/*.sh
echo -e "${GREEN}✓ Scripts are executable${NC}"
echo ""

# 4. Run initial quality check
echo -e "${YELLOW}[4/4] Running initial quality check...${NC}"
./scripts/check_quality.sh || echo -e "${YELLOW}⚠ Some checks failed (expected on first run)${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}✓ Development environment ready!${NC}"
echo "=========================================="
echo ""
echo "Available commands:"
echo "  - ./scripts/check_quality.sh  # Run all quality checks"
echo "  - ./scripts/fix_quality.sh    # Auto-fix formatting issues"
echo "  - pre-commit run --all-files  # Run pre-commit hooks manually"
echo "  - pytest tests/ -v            # Run tests"
echo ""
