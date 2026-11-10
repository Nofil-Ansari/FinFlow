---
phase: 2
plan: 01
type: standard
autonomous: true
wave: 1
depends_on: ["01"]
---

# Plan 02-01: Embedding Engine, Dual-Mode Vector Store & Two-Tier Redis Cache

<objective>
Implement a resilient, multi-tiered embedding engine (768-dim Google Gemini + zero-dependency local fallback), a two-tier L1 Redis + L2 Disk embedding cache, and a Dual-Mode Vector Store (Lightweight NumPy/JSON for local dev + pgvector/PostgreSQL schema for Docker/Cloud Run serverless deployment).
</objective>

<context>
- `.gsd/ROADMAP.md`
- `.gsd/STATE.md`
- `finance_app/app/services/rag/models.py`
- `finance_app/app/services/rag/pipeline.py`
- `finance_app/app/config.py`
</context>

<tasks>

<task type="auto" name="Create 768-Dim Embedding Engine with Two-Tier Redis + Disk Cache">
<files>
- `finance_app/app/services/rag/embeddings.py`
</files>
<action>
Implement `BaseEmbeddingService`, `LocalTfidfEmbedding` (768 dimensions with deterministic hash projection), `GeminiEmbeddingService` (supporting `text-embedding-004` via REST/SDK), and `TwoTierCachedEmbeddingService` (checking L1 Redis `rag:chunk:embedding:<sha256>` first, then L2 Disk `cache/embeddings_cache.json`, gracefully falling back to disk if Redis is unreachable).
</action>
<verify>
Verify embedding outputs are 768-dimensional normalized vectors, Redis cache writes/reads work when REDIS_URL is present, and fallback to disk operates without error when Redis is absent.
</verify>
<done>
Pluggable 768-dim embedding engine operational with two-tier Redis+Disk caching.
</done>
</task>

<task type="auto" name="Build Dual-Mode Vector Store (Local NumPy & Cloud pgvector)">
<files>
- `finance_app/app/services/rag/vector_store.py`
- `finance_app/app/models/rag_chunk.py`
</files>
<action>
Implement `VectorStore` interface with two backend adapters:
1. `LocalVectorStore`: In-memory NumPy cosine similarity index serialized to `vector_index.json` (stateless, zero extra dependencies, runs offline).
2. `PgVectorStore`: SQLAlchemy model `RagKnowledgeChunk` with vector support for PostgreSQL / Supabase, enabling stateless Cloud Run multi-instance queries.
Include automated adapter selection based on environment (`DATABASE_URL` containing `postgres` vs `sqlite`).
</action>
<verify>
Verify both adapters index chunks, filter by category/tags, and execute cosine similarity searches returning top-k ranked chunks.
</verify>
<done>
Dual-mode vector store supports local development and Docker/Cloud Run deployment seamlessly.
</done>
</task>

<task type="auto" name="Update CLI & Author Comprehensive Test Suite">
<files>
- `finance_app/manage_rag.py`
- `finance_app/tests/test_rag_vector_store.py`
</files>
<action>
Extend `manage_rag.py` with `embed` (indexes chunks to vector store), `query <text>` (semantic vector search with scores), and `warm-cache` (syncs disk cache to Redis). Author unit tests verifying embedding dimension (768), cosine similarity ordering, cache hit/miss behavior, and graceful Redis failover.
</action>
<verify>
Run unit tests: `python -m unittest tests/test_rag_vector_store.py`
</verify>
<done>
All embedding, caching, and vector store test fixtures pass with 100% success rate.
</done>
</task>

</tasks>

<success_criteria>
- [ ] 768-dimensional embedding engine with local fallback functional.
- [ ] Two-tier L1 Redis + L2 Disk caching working with content-hash keys (`rag:chunk:embedding:<sha256>`).
- [ ] Dual-mode vector store operates in both local file mode and pgvector mode.
- [ ] `manage_rag.py embed` and `manage_rag.py query` commands active.
- [ ] Test suite `tests/test_rag_vector_store.py` passes cleanly.
</success_criteria>
