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
