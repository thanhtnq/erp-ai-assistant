#!/bin/bash
# Globe3 ERP AI Assistant - Test Runner
# Run all unit tests for the system

echo "========================================"
echo "Globe3 ERP AI Assistant - Unit Tests"
echo "========================================"
echo ""

# Activate virtual environment and run tests
source venv/bin/activate
python -m unittest discover -s tests -p "test_*.py" -v

echo ""
echo "========================================"
echo "Test run completed"
echo "========================================"