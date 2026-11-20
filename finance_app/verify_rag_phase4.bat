@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo FinanceFlow RAG Phase 4 - Groq Advisor Integration & Grounding
echo =========================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python Virtual Environment...
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)
echo Using: %PYTHON_EXE%
echo.

echo [2/3] Running Phase 4 Unit & Integration Tests...
%PYTHON_EXE% -m unittest tests/test_rag_groq_integration.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Integration tests failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [PASS] All Phase 4 integration tests passed!
echo.

echo [3/3] Running Full RAG Test Suite Regression Check...
%PYTHON_EXE% -m unittest discover tests "test_rag_*.py"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Regression tests failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo =========================================================
echo Phase 4 Verification Complete! Groq Advisor RAG is active.
echo =========================================================
pause

