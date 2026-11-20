@echo off
:: ============================================================
:: verify_rag_phase5.bat — FinanceFlow RAG Phase 5 Regression
:: Runs all 5 RAG test suites in sequence.
:: Exit code 0 = all pass, 1 = first failure detected.
:: ============================================================

setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ================================================================
echo   FinanceFlow RAG Full Regression Suite  ^|  Milestone v2.1
echo ================================================================
echo.

set PASS_COUNT=0
set FAIL_FILE=

:: ── Helper: run one suite ────────────────────────────────────────────────────
:: Usage: call :RunSuite "label" "module"

goto :main

:RunSuite
    set SUITE_LABEL=%~1
    set SUITE_MODULE=%~2
    echo [RUN] %SUITE_LABEL% ...
    python -m unittest %SUITE_MODULE% -v 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo [FAIL] %SUITE_LABEL% FAILED  ^^^!
        echo        Run: python -m unittest %SUITE_MODULE% -v
        echo.
        set FAIL_FILE=%SUITE_MODULE%
        exit /b 1
    )
    echo [PASS] %SUITE_LABEL%
    echo.
    set /a PASS_COUNT+=1
    exit /b 0

:main

:: ── Phase 1 — Corpus Ingestion Models ───────────────────────────────────────
call :RunSuite "Phase 1 — Corpus Models & Chunker" "tests.test_rag_pipeline"
if ERRORLEVEL 1 goto :failed

:: ── Phase 2 — Embedding Engine & Vector Store ───────────────────────────────
call :RunSuite "Phase 2 — Embeddings & Vector Store" "tests.test_rag_vector_store"
if ERRORLEVEL 1 goto :failed

:: ── Phase 3 — Semantic Retrieval & Re-ranking ───────────────────────────────
call :RunSuite "Phase 3 — Hybrid Retrieval & Re-ranking" "tests.test_rag_retrieval"
if ERRORLEVEL 1 goto :failed

:: ── Phase 4 — Groq Integration ──────────────────────────────────────────────
call :RunSuite "Phase 4 — Groq RAG Integration" "tests.test_rag_groq_integration"
if ERRORLEVEL 1 goto :failed

:: ── Phase 5 — Benchmark Tests ───────────────────────────────────────────────
call :RunSuite "Phase 5 — RAG Benchmark & Citations" "tests.test_rag_benchmark"
if ERRORLEVEL 1 goto :failed

:: ── All passed ───────────────────────────────────────────────────────────────
echo ================================================================
echo   RESULT: ALL %PASS_COUNT%/5 SUITES PASSED  ✓
echo   Milestone v2.1 — Localized Financial RAG Engine — COMPLETE
echo ================================================================
echo.
exit /b 0

:failed
echo ================================================================
echo   RESULT: REGRESSION FAILED in: %FAIL_FILE%
echo   Suites passed before failure: %PASS_COUNT%/5
echo ================================================================
echo.
exit /b 1

