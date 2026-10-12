# ROADMAP.md

> **Current Phase**: Phase 3 Complete (Ready for Phase 4)
> **Milestone**: v1.0 — LLM-Powered Pakistani Financial Advisor

## Must-Haves (from SPEC)
- [x] Full personal finance ledger (Accounts, Transactions, Budgets, Savings, Recurring).
- [x] AI Financial Advisor with localized scoring (0-100) and overspending detection.
- [x] Groq LLM middleware with dynamic API key modal and model switcher.
- [ ] Exportable monthly financial intelligence reports (PDF/Excel).
- [ ] Advanced multi-month predictive budgeting visualization.

## Phases

### Phase 1: Core Financial Management System
**Status**: ✅ Completed
**Objective**: Build foundation ledger, SQLite schema, authentication, transaction CRUD, and responsive dashboard.

### Phase 2: AI Financial Advisor & Pakistani Localization
**Status**: ✅ Completed
**Objective**: Develop financial health scoring, heuristic overspending detection, product substitutions, and rule-based fallback advice.

### Phase 3: Groq LLM Middleware & Live Key Management
**Status**: ✅ Completed
**Objective**: Build `GroqMiddleware`, database migration for user API keys, modal UI on `/ai/advisor`, model selector (`openai/gpt-oss-120b`, `qwen/qwen3.8-27b`), and test connection endpoints.

### Phase 4: Advanced Analytics & Financial Reporting
**Status**: ⏳ Ready for Planning
**Objective**: Implement automated monthly PDF/Excel export reports, category heatmaps, and recurring subscription leakage detection.
