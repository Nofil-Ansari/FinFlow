@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo FinanceFlow RAG Phase 3 - Semantic Retrieval & Re-ranking
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

echo [2/3] Running Unit Tests (test_rag_retrieval.py)...
%PYTHON_EXE% -m unittest tests/test_rag_retrieval.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Retrieval unit tests failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [PASS] All Phase 3 unit tests passed successfully!
echo.

echo [3/3] Testing Hybrid Retrieval Engine across Pakistani Domains:
echo ---------------------------------------------------------
echo Query A: "tax on 1.5 lakh salary"
%PYTHON_EXE% manage_rag.py retrieve "tax on 1.5 lakh salary"
echo.

echo ---------------------------------------------------------
echo Query B: "form cz-50 zakat exemption"
%PYTHON_EXE% manage_rag.py retrieve "form cz-50 zakat exemption"
echo.

echo ---------------------------------------------------------
echo Query C: "cheaper alternative to Careem"
%PYTHON_EXE% manage_rag.py retrieve "cheaper alternative to Careem"
echo.

echo ---------------------------------------------------------
echo Query D: Irrelevant / Gated query: "how to bake cake"
%PYTHON_EXE% manage_rag.py retrieve "how to bake chocolate cake"
echo.

echo =========================================================
echo Phase 3 Verification Complete! Hybrid Retriever is Active.
echo =========================================================
pause

