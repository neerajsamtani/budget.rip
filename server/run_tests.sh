#!/bin/bash
# Test runner script for budget.rip server
# Uses virtual environment to avoid dependency conflicts

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/test_env"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Budget.rip Server Test Runner${NC}"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install/update dependencies if needed
if [ ! -f "$VENV_DIR/.deps_installed" ] || [ requirements.txt -nt "$VENV_DIR/.deps_installed" ]; then
    echo -e "${YELLOW}Installing/updating dependencies...${NC}"
    pip install --upgrade pip setuptools wheel -q
    pip install -r requirements.txt -q
    touch "$VENV_DIR/.deps_installed"
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
echo ""

if [ "$1" = "phase3" ]; then
    # Run only Phase 3 migration tests
    python -m pytest tests/test_phase3_migration.py -v
elif [ "$1" = "quick" ]; then
    # Run quick tests (excluding slow integration tests)
    python -m pytest tests/ -v -m "not slow"
elif [ -n "$1" ]; then
    # Run specific test file or pattern
    python -m pytest "$@"
else
    # Run all tests
    python -m pytest tests/ -v
fi

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

echo ""

exit $TEST_EXIT_CODE
