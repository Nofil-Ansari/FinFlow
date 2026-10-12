# DECISIONS.md - Architecture Decision Records (ADRs)

## ADR-001: Architecture Model for AI Advisor
- **Date**: 2026-10-12
- **Status**: Accepted
- **Context**: Needed an AI advisor capable of real-time conversational reasoning over user transactions without high cloud costs or slow response times.
- **Decision**: Integrate Groq API via a custom middleware layer (GroqMiddleware) supporting openai/gpt-oss-120b with localized Pakistani system prompt injection and an automatic offline rule-based fallback.

## ADR-002: Dynamic Per-User API Key Storage
- **Date**: 2026-10-12
- **Status**: Accepted
- **Context**: Users should have the freedom to supply their own free Groq API keys directly from the UI without modifying server environment variables.
- **Decision**: Extended FinancialProfile schema with groq_api_key and preferred_model columns, backed by modal configuration and validation endpoints (/ai/api-key/*).

## Phase 4 Decisions — Advanced Analytics, Reporting & Real-Time Data Sync

**Date:** 2026-10-12

### Scope
- **Live Ledger WebSocket Streaming**: WebSocket service (/ws/ledger) emitting real-time ledger statement updates (transactions, accounts, categories, timestamps) for downstream live integration with MS Excel (Office JS/Power Query), Google Sheets, and scalable ingestion into Google BigQuery / data warehouses.
- **Monthly Financial Intelligence Exports**: Dual-format downloads (PDF via ReportLab + Excel via OpenPyXL) featuring executive AI health summary, overspending alerts, and itemized tabular ledgers.
- **Subscription Leakage Detection**: Heuristic merchant & cadence detection (28–32 day recurrence) catching silent price creep and unused subscriptions.

### Approach
- **Reporting Engine (Option A / Preference 1)**: ReportLab for PDF generation directly in memory buffers. OpenPyXL for structured spreadsheets. Zero binary/GTK dependencies on Windows.
- **Subscription Leakage (Option A)**: Automated heuristic scanner on raw transaction descriptions and cadence without requiring manual user tagging.
- **Real-Time Sync Protocol**: WebSocket event broadcasting on transaction commit events with token-based client auth.
- **UI Integration (Option A)**: Upgrades /reports/ with visual heatmaps, live sync status badge, and direct linkage to /ai/advisor.

### Constraints
- WebSocket connection must enforce session/token authentication per user.
- Export engines must stream bytes efficiently without writing temporary files to disk.
