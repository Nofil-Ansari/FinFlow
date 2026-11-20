---
phase: 3
plan: 01
type: standard
autonomous: true
wave: 1
depends_on: ["02"]
---

# Plan 03-01: Semantic Retrieval & Re-ranking Layer

<objective>
Implement a production-grade Hybrid Semantic Retrieval & Re-ranking Engine that accurately selects the most authoritative Pakistani financial knowledge chunks for a user query. The engine includes: query normalization (Pakistani currency/slang), hybrid dense+lexical search, Reciprocal Rank Fusion (RRF), authority-weighted cross-scoring re-ranker, and relevance threshold gating to prevent hallucinated financial data reaching the LLM.
</objective>

<context>
- `.gsd/ROADMAP.md`
- `.gsd/STATE.md`
- `finance_app/app/services/rag/models.py`
- `finance_app/app/services/rag/vector_store.py`
- `finance_app/app/services/rag/embeddings.py`
- `finance_app/app/services/groq_middleware.py`
</context>

<tasks>

<task type="auto" name="Build Hybrid Retrieval Engine (QueryProcessor + LexicalMatcher + HybridRetriever + RRF)">
<files>
- `finance_app/app/services/rag/retrieval.py`
</files>
<action>
Implement the full retrieval pipeline in one module:
1. `QueryProcessor`: normalizes Pakistani currency (1.5 lakh -> 150,000 PKR, 25k -> 25,000), bilingual terms (bachat -> savings, munafa -> profit), detects intent category (tax, banking, investment, zakat, substitution).
2. `LexicalMatcher`: builds an in-memory inverted index from loaded KnowledgeChunks and scores candidate chunks using TF-IDF token overlap (BM25-style) against query terms.
3. `HybridRetriever`: runs both dense vector search (via VectorStoreBase) and lexical search, then merges results with Reciprocal Rank Fusion (RRF constant k=60). Returns top-15 merged candidates.
4. `ReRanker`: applies cross-scoring heuristics — authority boost for FBR/SBP/CDNS sourced chunks, exact number match bonus, term coverage score, negative penalty for category mismatch. Applies relevance threshold gate (default 0.35): chunks scoring below threshold are excluded.
5. `RetrievalResult`: structured dataclass containing the KnowledgeChunk, vector_score, rerank_score, citation string ("[Source: FBR Income Tax Ordinance 2024-25]"), and matched_terms list.
6. `retrieve()`: top-level function wiring all stages together — takes raw query + optional category filter + top_k, returns List[RetrievalResult].
</action>
<verify>
Import module cleanly (no dependency errors). Run test suite: `python -m unittest tests/test_rag_retrieval.py`.
</verify>
<done>
Hybrid retrieval engine operational: query normalization works, RRF fusion merges candidates, re-ranker elevates authoritative chunks, gating returns empty list for irrelevant queries.
</done>
</task>

<task type="auto" name="Update CLI + Tests + Package Exports">
<files>
- `finance_app/manage_rag.py`
- `finance_app/tests/test_rag_retrieval.py`
- `finance_app/app/services/rag/__init__.py`
- `finance_app/verify_rag_phase3.bat`
</files>
<action>
1. `manage_rag.py`: add `retrieve <query>` command that runs the full pipeline and prints ranked results with scores, citation labels, and matched terms.
2. `tests/test_rag_retrieval.py`: author 5 unit test cases:
   - Currency normalization (1.5 lakh -> 150,000, 25k -> 25,000, bachat -> savings)
   - RRF merging (chunk appearing in both dense and lexical lists scores higher than chunk in one list only)
   - Authority boosting (FBR-tagged chunk ranks above general chunk for tax query)
   - Relevance gating (non-financial query "how to bake a cake" returns empty results)
   - Entity retrieval (query "Behbood Certificate" returns CDNS-category chunk in top position)
3. `app/services/rag/__init__.py`: export QueryProcessor, LexicalMatcher, HybridRetriever, ReRanker, RetrievalResult, retrieve.
4. `verify_rag_phase3.bat`: one-click Windows runner for tests + 4 sample retrieval queries.
</action>
<verify>
`python -m unittest tests/test_rag_retrieval.py` — all tests pass. `python manage_rag.py retrieve "income tax salaried 2024"` returns ranked results.
</verify>
<done>
All 5 test fixtures pass. CLI retrieve command outputs ranked chunks with scores >= 0.35 for financial queries and empty list for irrelevant queries.
</done>
</task>

</tasks>

<success_criteria>
- [ ] `retrieval.py` module with QueryProcessor, LexicalMatcher, HybridRetriever, ReRanker, RetrievalResult, retrieve() function.
- [ ] RRF merging correctly elevates chunks ranking high in both dense and lexical channels.
- [ ] Authority re-ranking boosts FBR/SBP/CDNS sourced chunks for regulatory queries.
- [ ] Relevance threshold gating prevents non-financial queries from returning context.
- [ ] `python manage_rag.py retrieve "<query>"` CLI command functional.
- [ ] `tests/test_rag_retrieval.py` — 5 tests all passing.
</success_criteria>

