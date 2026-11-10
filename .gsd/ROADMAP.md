# ROADMAP.md

> **Active Milestone**: v2.1 - Localized Financial RAG & Vector Intelligence Engine  
> **Goal**: Build an end-to-end Retrieval-Augmented Generation (RAG) system for FinanceFlow to ground the AI financial advisor in Pakistani market financial rules (FBR tax slabs, SBP regulations, National Savings schemes, Zakat calculations, and verified local product substitutions) using vector embeddings and similarity search.

## Must-Haves (Milestone v2.1)
- [ ] Document Ingestion & Chunking Pipeline for Pakistani financial regulations, tax laws, investment products, and product substitution databases.
- [ ] Embedding generation pipeline with cost-effective, high-accuracy embeddings (e.g., Google text-embedding-004 / open-source HuggingFace sentence-transformers).
- [ ] Vector database integration (e.g., ChromaDB for lightweight local persistence, with pgvector upgrade path for PostgreSQL/Supabase).
- [ ] Hybrid Semantic Retrieval & Context Augmentation integrated into `GroqMiddleware` alongside existing user ledger/financial profile data.
- [ ] RAG evaluation and test suite verifying source citation, retrieval accuracy, and guardrails against hallucinated tax/interest rates.
- [ ] Web UI citation display in `/ai/advisor` chat showing source reference badges and confidence.

## Milestone v2.1 Phases (RAG Architecture)

### Phase 1: Knowledge Corpus Curation & Ingestion Pipeline
**Status**: ⏳ Ready to Plan  
**Objective**: Curate markdown/JSON source documents for Pakistani tax slabs (income/sales tax), SBP policy rates & banking rules, National Savings schemes (rates & terms), Zakat rules, and curated market alternatives. Implement an automated document loader, normalizer, and chunking service.

### Phase 2: Embedding Engine & Vector Store Setup
**Status**: ⏳ Queued  
**Objective**: Set up vector storage (ChromaDB / SQLite-vss / pgvector) and build an embedding service interface supporting local and cloud embedding models with caching to prevent redundant API calls.

### Phase 3: Semantic Retrieval & Re-ranking Layer
**Status**: ⏳ Queued  
**Objective**: Build a query processor that generates query embeddings, performs hybrid search (semantic similarity + keyword/tag filtering by category/merchant), and ranks retrieved chunks with relevance thresholds.

### Phase 4: Groq Advisor RAG Integration & Prompt Synthesis
**Status**: ⏳ Queued  
**Objective**: Connect the retrieval layer into `GroqMiddleware.chat()` and `recommender.py`. Dynamically augment system prompts with top-k retrieved context chunks, enforce citation markers (`[Source: ...]`), and handle fallback when relevance is low.

### Phase 5: UI Citations, Verification & Benchmark Testing
**Status**: ⏳ Queued  
**Objective**: Update the chat frontend (`ai/advisor.html`) to render collapsible citation pills and source snippets. Author automated test cases validating retrieval relevance and hallucination prevention.

---

## Paused Milestones

### ⏸️ Milestone v2.0 - Production Deployment & Continuous Delivery (GCP Cloud Run + Supabase + Redis)
**Status**: ⏸️ PAUSED (Paused on 2026-11-10 to prioritize RAG engine development)  
**Goal**: Automated CD pipeline deploying FinanceFlow to Google Cloud Run with Redis caching & Supabase PostgreSQL.

#### Paused Phases:
- **Phase 1: GCP Environment, Cloud Project Provisioning & API Setup** (Plan 01-01 prepared, paused at authentication checkpoint)
- **Phase 2: Production Containerization & Redis Caching Layer Architecture**
- **Phase 3: Hosted PostgreSQL Database Setup & Migration Automation**
- **Phase 4: Google Cloud Run Service Configuration & Artifact Registry Setup**
- **Phase 5: GitHub Actions Continuous Deployment (CD) Pipeline for Cloud Run**
- **Phase 6: Production Hardening & Technical Debt Resolution (Gap Closure)**

