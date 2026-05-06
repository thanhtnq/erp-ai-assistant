@echo off
REM Globe3 ERP AI Assistant - Test Runner
REM Run all unit tests for the system

echo ========================================
echo Globe3 ERP AI Assistant - Unit Tests
echo ========================================
echo.

REM Activate virtual environment and run tests
call venv\Scripts\activate.bat
python -m unittest discover -s tests -p "test_*.py" -v

echo.
echo ========================================
echo Test run completed
echo ========================================
pause