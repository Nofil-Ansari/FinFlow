# STATE.md - Project Memory

## Active Milestone
**Milestone**: v2.1 - Localized Financial RAG & Vector Intelligence Engine  
**Active Branch**: main  
**Last Updated**: 2026-11-10  

## Current Position
- **Milestone**: v2.1
- **Phase**: Phase 1: Knowledge Corpus Curation & Ingestion Pipeline
- **Status**: Plan 01-01 created and awaiting user review/approval
- **Active Plan**: `.gsd/phases/01-rag/01-PLAN.md`

## Key Requirements & Architecture Decisions (RAG System)
- **Knowledge Domain**: Pakistani macroeconomic & personal finance data (FBR income tax slabs, SBP policy rates, National Savings rates/products, Zakat rules, and localized product/service substitutions).
- **Vector Storage**: Lightweight embedded vector store for local dev (ChromaDB / SQLite-vss) with seamless compatibility with pgvector for production.
- **Embedding Provider**: Pluggable embedding service (supporting Gemini `text-embedding-004` / open-source local embeddings via `sentence-transformers` / HuggingFace).
- **Retrieval Strategy**: Hybrid retrieval (top-k semantic cosine similarity + category/keyword metadata filtering) with relevance threshold gating.
- **Prompt Synthesis**: Augmented prompt injection into [`GroqMiddleware`](file:///D:/Projects/Project/finance_app/app/services/groq_middleware.py) combining user transactional context, financial profile, and retrieved knowledge chunks with explicit citations.

## Next Steps
1. Create Phase 1 Plan (`.gsd/phases/01-rag/01-PLAN.md` or `.gsd/phases/rag-01/01-PLAN.md`): Knowledge corpus curation, data models, chunking strategy, and document loader.

---

## Paused Milestones
- **Milestone v2.0 - Production Deployment & Continuous Delivery (GCP Cloud Run + Supabase + Redis)**:
  - **Status**: ⏸️ PAUSED on 2026-11-10
  - **Paused At**: Phase 1 (Plan 01-01 scripts created, awaiting user GCP credentials/project selection)
  - **Artifacts Preserved**: `scripts/gcp_setup.ps1`, `scripts/gcp_setup.sh`, `.env.gcp.example`, `.gsd/phases/01/01-PLAN.md`
