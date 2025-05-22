#!/bin/bash

# SmartNinja Application Runner
# This script helps run various aspects of the SmartNinja application

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}==============================${NC}"
    echo -e "${BLUE}      SmartNinja Runner      ${NC}"
    echo -e "${BLUE}==============================${NC}"
    echo ""
}

function print_usage() {
    echo -e "Usage: ${GREEN}./run.sh${NC} [command]"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}app${NC}        Run the SmartNinja Streamlit frontend"


    echo -e "  ${GREEN}test${NC}       Run all tests"
    echo -e "  ${GREEN}coverage${NC}   Run tests with coverage report"
    echo -e "  ${GREEN}lint${NC}       Run linting (isort, black, pylint)"
    echo -e "  ${GREEN}security${NC}   Run security checks (bandit, pip-audit)"
    echo -e "  ${GREEN}clean${NC}      Clean temporary files and caches"
    echo -e "  ${GREEN}help${NC}       Show this help message"
    echo ""
}

function run_app() {
    echo -e "${BLUE}Starting SmartNinja Streamlit frontend...${NC}"
    streamlit run app.py
}

function run_tests() {
    echo -e "${BLUE}Cleaning pytest cache...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +

    echo -e "${BLUE}Running tests...${NC}"
    python -m pytest app/tests/ -v -p no:warnings
}

function run_coverage() {
    echo -e "${BLUE}Running tests with coverage...${NC}"
    pytest --cov=app --cov-report=term-missing --cov-report=html
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
}

function run_lint() {
    echo -e "${BLUE}Running linting...${NC}"

    echo -e "${BLUE}Running isort...${NC}"
    isort app/ --profile black

    echo -e "${BLUE}Running black...${NC}"
    black app/

    echo -e "${BLUE}Running pylint...${NC}"
    pylint --rcfile=.pylintrc app/
}

function run_security() {
    echo -e "${BLUE}Running security checks...${NC}"

    echo -e "${BLUE}Running bandit security scan...${NC}"
    bandit -r app/ -c bandit.yaml -f txt

    echo -e "${BLUE}Checking dependencies for vulnerabilities...${NC}"
    pip-audit -r requirements.txt

    echo -e "${GREEN}Security checks complete!${NC}"
}

function clean_temp() {
    echo -e "${BLUE}Cleaning temporary files...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".coverage" -delete
    find . -type d -name "htmlcov" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    echo -e "${GREEN}Cleaning complete!${NC}"
}

# Main script execution
print_header

if [ $# -eq 0 ]; then
    print_usage
    exit 0
fi

case "$1" in
    app)
        run_app
        ;;
    test)
        run_tests
        ;;
    coverage)
        run_coverage
        ;;
    lint)
        run_lint
        ;;
    security)
        run_security
        ;;
    clean)
        clean_temp
        ;;
    help)
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        print_usage
        exit 1
        ;;
esac
