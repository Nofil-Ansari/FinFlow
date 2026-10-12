# DECISIONS.md - Architecture Decision Records (ADRs)

## ADR-001: Architecture Model for AI Advisor
- **Date**: 2026-10-12
- **Status**: Accepted
- **Context**: Needed an AI advisor capable of real-time conversational reasoning over user transactions without high cloud costs or slow response times.
- **Decision**: Integrate Groq API via a custom middleware layer (`GroqMiddleware`) supporting `openai/gpt-oss-120b` with localized Pakistani system prompt injection and an automatic offline rule-based fallback.

## ADR-002: Dynamic Per-User API Key Storage
- **Date**: 2026-10-12
- **Status**: Accepted
- **Context**: Users should have the freedom to supply their own free Groq API keys directly from the UI without modifying server environment variables.
- **Decision**: Extended `FinancialProfile` schema with `groq_api_key` and `preferred_model` columns, backed by modal configuration and validation endpoints (`/ai/api-key/*`).

## Phase 4 Decisions — Advanced Analytics, Reporting & Data Sync

**Date:** 2026-10-12

### Scope
- **Raw Ledger Webhook & BI Sync Endpoint**: Dedicated secure data feed endpoint (`/api/v1/ledger/statement` / webhook) providing tabular transactions (accounts, categories, dates, amounts, tags) formatted for direct consumption by Excel Power Query, MS Access, and cloud warehouses like BigQuery.
- **Monthly Financial Intelligence Exports**: PDF and Excel (.xlsx) downloads combining executive AI health summaries with structured ledgers.
- **Subscription Leakage Detection**: Automated pattern recognition flagging 28–32 day recurring debits and creeping expenses.

### Approach
- **Reporting Engine**: Option A (ReportLab for PDF, OpenPyXL for Excel) — zero native OS binary issues on Windows, ultra-fast streaming in-memory downloads.
- **Leakage Algorithm**: Option A (Heuristic Merchant & Interval Matching) — scans raw transaction history for cadence regularity without requiring manual user tagging.
- **UI Topology**: Option A (Integrated Hub) — upgrades `/reports/` with visual heatmaps, export actions, and deep linkage to `/ai/advisor`.

### Constraints
- Webhook endpoints require API key token authentication for secure external connectivity.
