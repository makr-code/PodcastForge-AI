#!/bin/bash
# Auto-Fix Script für PodcastForge-AI
# Behebt automatisch behebbare Code-Quality-Issues

set -e

echo "=========================================="
echo "🔧 PodcastForge-AI Auto-Fix"
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

# 1. Black (Auto-Format)
echo -e "${YELLOW}[1/3] Running Black (Auto-Format)...${NC}"
black src/ tests/
echo -e "${GREEN}✓ Black completed${NC}"
echo ""

# 2. isort (Auto-Sort Imports)
echo -e "${YELLOW}[2/3] Running isort (Auto-Sort Imports)...${NC}"
isort src/ tests/
echo -e "${GREEN}✓ isort completed${NC}"
echo ""

# 3. Remove trailing whitespace
echo -e "${YELLOW}[3/3] Removing trailing whitespace...${NC}"
find src/ tests/ -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} +
echo -e "${GREEN}✓ Whitespace cleanup completed${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}✓ Auto-fix completed!${NC}"
echo "=========================================="
echo ""
echo "Please review changes with: git diff"
echo "Then run: ./scripts/check_quality.sh"
