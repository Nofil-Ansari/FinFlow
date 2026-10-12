# STATE.md - Project Memory

## Active Milestone
**Milestone**: v1.0
**Active Branch**: `LLM_pilot_branch`
**Last Updated**: 2026-10-12

## Current Status
- Application server running and active on `http://127.0.0.1:5000`.
- All 23 unit and integration tests passing (`tests/test_finance_app.py` + `tests/test_ai_advisor.py`).
- Groq LLM connection verified live (latency ~372ms, model `openai/gpt-oss-120b`).
- Codebase mapped and GSD lifecycle documentation initialized.

## Key Decisions
- Chose `openai/gpt-oss-120b` as default Groq flagship model due to 128k context and reasoning performance.
- Store user custom API keys securely in `FinancialProfile` table with masked UI representation (`gsk_••••••••yMWR`).
- Implemented offline Pakistani rule-based advisor fallback whenever API keys are unset.

## Phase 4 Status
- Discussion completed: Selected Option A (ReportLab, Heuristic Leakage Detection, Integrated UI Hub).
- Scoped webhook endpoint for raw tabular ledger statement syncing with Excel, MS Access, and BigQuery.
- Ready for `/plan 4`.
