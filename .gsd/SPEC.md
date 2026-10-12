# SPEC.md - Project Specification

> **Status**: `FINALIZED`

## Vision
An intelligent personal finance and wealth management platform specifically localized for the Pakistani economy, combining core ledger tracking (accounts, transactions, budgets, goals) with an AI Financial Advisor powered by Groq LLMs, predictive spending models, and localized spending substitution intelligence.

## Goals
1. Provide comprehensive personal finance management (multi-account balances, income/expense tracking, budget limits, savings goals).
2. Deliver a real-time AI Financial Advisor powered by high-speed Groq models with user-configurable API keys.
3. Offer localized Pakistani financial intelligence (PKR currency standards, local merchant auto-categorization, domestic investment options like National Savings Certificates, and affordable product substitutions).
4. Run predictive spending analytics to alert users before they exceed monthly budgets.

## Non-Goals (Out of Scope)
- Direct automated Open Banking synchronization with Pakistani commercial banks (manual & CSV import supported instead).
- Live stock trading execution on the Pakistan Stock Exchange (PSX tracking only).
- Multi-tenant enterprise accounting.

## Users
- Pakistani individuals, freelancers, and families seeking structured budgeting, localized savings recommendations, and AI-driven expense guidance.

## Constraints
- Python 3.13+ runtime with Flask modular architecture.
- Fully offline capable fallback when Groq API keys are not provided.
- Response latency under 500ms for live AI chat completions.

## Success Criteria
- [x] All 23 core unit and integration tests passing (`Ran 23 tests ... OK`).
- [x] Live Groq API integration working end-to-end with latency under 400ms.
- [x] Pakistani localized alternative suggestions rendered in advisor dashboard.
- [x] Zero regressions on branch `LLM_pilot_branch`.
