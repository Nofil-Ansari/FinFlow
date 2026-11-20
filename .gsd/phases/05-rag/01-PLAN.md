---
phase: 5
plan: 01
type: standard
autonomous: true
wave: 1
depends_on: ["04"]
---

# Plan 05-01: UI Citations, Verification & Benchmark Testing

<objective>
Deliver the final user-facing citation experience and automated benchmark evaluation suite for Milestone v2.1. Update the chat route and web UI (advisor.html) with collapsible, interactive Pakistani source reference badges. Author an automated benchmark test suite measuring retrieval hit rate, numerical rate accuracy, and anti-hallucination gating.
</objective>

<context>
- `.gsd/ROADMAP.md`
- `.gsd/STATE.md`
- `finance_app/app/templates/ai/advisor.html`
- `finance_app/app/ai/routes.py`
- `finance_app/app/services/rag/retrieval.py`
- `finance_app/app/services/groq_middleware.py`
</context>

<tasks>

<task type="auto" name="Implement UI Citation Badges in advisor.html & Pass Citations in Chat Route">
<files>
- `finance_app/app/ai/routes.py`
- `finance_app/app/templates/ai/advisor.html`
</files>
<action>
1. Update `/ai/chat` in `app/ai/routes.py` to include `"citations": result.get("citations", [])` in the JSON response payload.
2. In `advisor.html`:
   - Add CSS for `.citation-badge`, `.citation-drawer`, `.citation-header`, and `.citation-snippet` with smooth CSS transitions.
   - Update client-side `addMessage(role, content, citations)` in `<script>`:
     - For assistant messages with non-empty `citations`, render an interactive citation badge beneath the text bubble:
       e.g., `📚 {N} Verified Source(s) (FBR / SBP / CDNS) ▼`.
     - Clicking the badge toggles a collapsible drawer displaying the document title, issuing authority, confidence percentage, and regulatory text snippet.
</action>
<verify>
Verify `/ai/chat` payload contains `citations` array. Inspect `advisor.html` to ensure `addMessage()` renders expandable source drawers correctly without breaking layout.
</verify>
<done>
Interactive citation UI operational in AI Advisor chat with collapsible regulatory proof drawers.
</done>
</task>

<task type="auto" name="Author RAG Benchmark & Ground Truth Evaluation Suite">
<files>
- `finance_app/tests/test_rag_benchmark.py`
</files>
<action>
Create `tests/test_rag_benchmark.py` evaluating:
1. **Precision & Hit Rate @ 3**: Runs benchmark queries across 4 Pakistani financial domains (FBR tax, SBP banking, CDNS savings, Zakat rules) and asserts expected domain chunk appears in top 3.
2. **Numerical Rate Accuracy**: Compares extracted rates in top chunks against ground truth (FBR 5% base rate, 2.5% zakat, 15.36% Behbood yield).
3. **Anti-Hallucination Gating**: Asserts non-financial prompts ("make pasta", "tell joke") return 0 citations.
4. **Latency Verification**: Asserts hybrid retrieval + re-ranking pipeline completes in < 100ms.
</action>
<verify>
Run `python -m unittest tests/test_rag_benchmark.py` — all benchmarks pass with 100% precision.
</verify>
<done>
Automated benchmark suite validates RAG precision, numerical accuracy, and anti-hallucination gating.
</done>
</task>

<task type="auto" name="Final Milestone Verification & Regression Script">
<files>
- `finance_app/verify_rag_phase5.bat`
</files>
<action>
Create `verify_rag_phase5.bat` running the complete test suite across all 5 phases:
- `test_rag_ingestion.py`
- `test_rag_vector_store.py`
- `test_rag_retrieval.py`
- `test_rag_groq_integration.py`
- `test_rag_benchmark.py`
</action>
<verify>
Execute script locally; confirm all 5 test files pass cleanly.
</verify>
<done>
End-to-end regression verification confirmed for Milestone v2.1.
</done>
</task>

</tasks>

<success_criteria>
- [ ] `/ai/chat` endpoint returns `"citations"` array in JSON response.
- [ ] `advisor.html` renders collapsible source reference badges beneath assistant chat bubbles.
- [ ] `tests/test_rag_benchmark.py` verifies retrieval hit rate, rate accuracy, and anti-hallucination suppression.
- [ ] `verify_rag_phase5.bat` runs full regression across all 5 test files.
</success_criteria>

