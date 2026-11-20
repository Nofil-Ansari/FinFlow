---
phase: 4
plan: 01
type: standard
autonomous: true
wave: 1
depends_on: ["03"]
---

# Plan 04-01: Groq Advisor RAG Integration & Prompt Synthesis

<objective>
Integrate the Phase 3 Hybrid Retrieval Engine directly into the conversational advisor pipeline (GroqMiddleware and recommender.py). Synthesize token-budget-aware prompts containing verified Pakistani regulatory knowledge, enforce strict source citation markers (`[Source: ...]`), pass citation metadata in chat payloads, and ground the offline fallback responder in real corpus knowledge when no LLM key is configured.
</objective>

<context>
- `.gsd/ROADMAP.md`
- `.gsd/STATE.md`
- `finance_app/app/services/groq_middleware.py`
- `finance_app/app/services/recommender.py`
- `finance_app/app/services/rag/retrieval.py`
- `finance_app/app/services/rag/__init__.py`
</context>

<tasks>

<task type="auto" name="Create Prompt Synthesizer & Retriever Singleton Factory">
<files>
- `finance_app/app/services/rag/prompt_synthesizer.py`
- `finance_app/app/services/rag/__init__.py`
</files>
<action>
1. Implement `PromptSynthesizer` in `prompt_synthesizer.py`:
   - Formats a list of `RetrievalResult` objects into a clean, XML/Markdown-fenced prompt block (`=== VERIFIED PAKISTANI FINANCIAL KNOWLEDGE ===`).
   - Enforces token budgeting (truncates context if it exceeds ~700 estimated tokens, keeping top 2-3 most relevant chunks).
   - Injects explicit anti-hallucination guardrails instructing the LLM:
     "You MUST base any specific tax brackets, SBP policy rates, Zakat rules, or National Savings figures on the verified excerpts below. If not present, state the limitation rather than estimating."
   - Mandates inline source citations using format: `[Source: Title | Authority (Year)]`.
2. Implement `get_rag_retriever()` lazy singleton factory in `prompt_synthesizer.py` to cache the initialized `HybridRetriever` across requests, avoiding reloading chunks and indices on every chat message.
3. Export `PromptSynthesizer` and `get_rag_retriever` from `app/services/rag/__init__.py`.
</action>
<verify>
Unit test verifies `PromptSynthesizer.format_context()` generates formatted XML/Markdown with citation instructions and respects token budgets.
</verify>
<done>
Prompt synthesis layer complete with token bounds, guardrail instructions, and efficient retriever caching.
</done>
</task>

<task type="auto" name="Wire RAG Pipeline into GroqMiddleware & recommender.py">
<files>
- `finance_app/app/services/recommender.py`
- `finance_app/app/services/groq_middleware.py`
</files>
<action>
1. Update `build_groq_context(user_id, retrieved_chunks=None)` in `recommender.py`:
   - Accept optional `retrieved_chunks: List[RetrievalResult]`.
   - When present and non-empty, invoke `PromptSynthesizer.format_context(retrieved_chunks)` and append to the system prompt.
2. Update `GroqMiddleware.chat(user_id, user_message, model_override=None)` in `groq_middleware.py`:
   - Step 1: Run `get_rag_retriever().retrieve(user_message, top_k=3)`.
   - Step 2: Pass retrieved chunks to `build_groq_context(user_id, retrieved_chunks=chunks)`.
   - Step 3: Call Groq API and extract citations list from `retrieved_chunks`.
   - Step 4: Include `citations: [r.to_dict() for r in retrieved_chunks]` in the return dictionary.
3. Update `GroqMiddleware._fallback_response(user_message)`:
   - When offline/no key is set, query `get_rag_retriever().retrieve(user_message, top_k=1)`.
   - If a high-confidence chunk exists (score >= 0.35), dynamically craft the fallback using the chunk's content and citation, rather than relying solely on static hardcoded strings.
</action>
<verify>
Verify `GroqMiddleware.chat()` returns response dict containing `"citations"` list with sources. Verify offline fallback generates grounded advice for tax and savings queries.
</verify>
<done>
Advisor chat is dynamically grounded with verified Pakistani financial data and returns structured citation metadata.
</done>
</task>

<task type="auto" name="Author Comprehensive Integration Test Suite & Verification Script">
<files>
- `finance_app/tests/test_rag_groq_integration.py`
- `finance_app/verify_rag_phase4.bat`
</files>
<action>
1. Create `tests/test_rag_groq_integration.py` testing:
   - `PromptSynthesizer`: Output structure, token budget adherence, and citation instruction inclusion.
   - `build_groq_context()` with and without retrieved chunks.
   - `GroqMiddleware.chat()` mock test verifying prompt contains RAG excerpts and return dict contains `citations`.
   - Offline fallback RAG grounding test (returns verified Pakistani rate excerpts without API key).
2. Create `verify_rag_phase4.bat` batch file for one-click test execution on Windows.
</action>
<verify>
Run `python -m unittest tests/test_rag_groq_integration.py` — all fixtures pass.
</verify>
<done>
All unit and integration tests for Phase 4 pass with 100% success rate.
</done>
</task>

</tasks>

<success_criteria>
- [ ] `PromptSynthesizer` formats retrieved chunks into token-budgeted, guardrailed system prompt sections.
- [ ] `recommender.py` accepts and includes RAG context in `build_groq_context()`.
- [ ] `GroqMiddleware.chat()` retrieves top-k chunks, injects them into the Groq LLM prompt, and returns a `citations` array.
- [ ] Offline fallback responder leverages RAG knowledge chunks for Pakistani financial questions.
- [ ] Unit & integration tests in `tests/test_rag_groq_integration.py` pass.
- [ ] Windows runner `verify_rag_phase4.bat` executes cleanly.
</success_criteria>

