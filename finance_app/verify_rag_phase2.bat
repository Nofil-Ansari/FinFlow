@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo FinanceFlow RAG Phase 2 - Embedding & Vector Store
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python Virtual Environment...
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)
echo Using: %PYTHON_EXE%
echo.

echo [2/4] Running Unit Tests (test_rag_vector_store.py)...
%PYTHON_EXE% -m unittest tests/test_rag_vector_store.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Unit tests failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [PASS] Unit tests passed!
echo.

echo [3/4] Ingesting Knowledge Corpus Chunks...
%PYTHON_EXE% manage_rag.py ingest
echo.

echo [4/4] Generating Embeddings and Building Vector Index...
%PYTHON_EXE% manage_rag.py embed
echo.

echo ---------------------------------------------------
echo Testing Semantic Vector Search:
echo ---------------------------------------------------
%PYTHON_EXE% manage_rag.py query "tax slab salaried income 2024"
echo.

echo ===================================================
echo Verification Complete! Vector Store is operational.
echo ===================================================
pause

