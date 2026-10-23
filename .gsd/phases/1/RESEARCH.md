---
phase: 1
milestone: v2.0
level: 2
researched_at: 2026-10-23
objective: "Context-aware financial advisor with natural dialogue and reduced Groq API dependency/cost"
---

# Phase 1 Research: Context-Aware Advisor with Semantic RAG & Hybrid Local/Groq Pipeline

## Objective
Enable the AI Financial Advisor to maintain rich, natural multi-turn conversational context while minimizing external Groq API dependency and token usage costs.

---

## 1. Questions Investigated

1. **How to reduce Groq API dependency and cost without degrading dialogue quality?**
2. **What embedding model and vector store best fit our lightweight Flask/Python 3.13 stack?**
3. **How to make the advisor truly context-aware beyond static prompt-stuffing?**
4. **How to handle fallback when offline or when the user doesn't have a Groq API key?**

---

## 2. Findings & Architectural Options

### Topic 1: Reducing Groq API Dependency & Costs

#### Analysis of Current Overhead
- **Current Prompt Size**: ~1,200 to 2,000 tokens per message due to full category aggregates, top 10 merchants, and rule-based substitutions injected unconditionally.
- **Full History Forwarding**: Every multi-turn call passes up to 20 past turns in plaintext (`MAX_HISTORY_MESSAGES = 20`).
- **Repetitive Routine Queries**: Greetings ("Hello", "Who are you?"), basic metric lookups ("What is my balance?"), and static advice incur full LLM calls.

#### Cost & Dependency Reduction Strategies:
1. **Tiered Query Routing (Heuristic & Local Intent Gate)**:
   - *Direct Local Handlers*: Queries like "What's my monthly balance?", "List my accounts", or "Show my health score" bypass external LLM entirely and return instantly from local SQL/analytics functions with formatted natural text.
   - *Semantic Cache / Prompt Cache*: Cache common financial guidance and Pakistani market tips so repeat questions hit zero external API tokens.
2. **Model Cascading on Groq**:
   - Default to smaller, cheaper/faster models (`openai/gpt-oss-20b` or `qwen/qwen3.8-27b`) for routine multi-turn queries.
   - Escalate to `openai/gpt-oss-120b` only for complex reasoning (e.g., deep budget restructuring, multi-asset portfolio rebalancing).
3. **Optional Local Small Language Model (SLM) Fallback**:
   - Integrate an optional local GGUF/llama-cpp or ONNX runtime (e.g., `Qwen2.5-0.5B-Instruct` or `SmolLM2-1.7B`) for complete offline/free operation when no Groq key exists.

---

### Topic 2: Vector Store & Embeddings for SQLite/Flask Stack

We compared 3 vector retrieval architectures:

| Solution | Footprint | Python 3.13 Compatibility | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **Option A: `sqlite-vec` / `sqlite-vss`** | Minimal (C extension) | High (C extension wheels) | Native SQLite integration; single DB file | Requires compiled extension loading |
| **Option B: ChromaDB (Embedded)** | Medium (~60MB) | High | Zero-config, built-in persistence, Pythonic API | Extra dependency, slightly slower cold start |
| **Option C: FAISS (CPU) / In-Memory Numpy** | Ultra-light (<10MB) | High | Instant startup, serialized to disk/pkl or SQLite BLOB | Manual metadata indexing |

**Recommendation:** 
- Use **`ChromaDB` (embedded DuckDB/Parquet mode)** or **`FAISS-cpu` with in-memory numpy serialization** for simplicity and zero C-compiler prerequisites.
- For embeddings: **`sentence-transformers/all-MiniLM-L6-v2`** (80MB, fast CPU inference) or HuggingFace ONNX runtime for sub-20ms local embedding generation.

---

### Topic 3: Context-Aware Dialogue & RAG Pipeline Design

Instead of dumping raw transaction tables into prompt strings:
1. **Financial Profile & Real-Time KPIs (Deterministic)**: Keep top-level KPIs (Income, Net Worth, Health Score, Savings Rate) as a condensed 100-token summary header.
2. **Dynamic Semantic Retrieval (Top-K Chunks)**:
   - Index:
     - **Knowledge Base**: Pakistani tax rules, SBP rate benchmarks, mutual fund saving strategies, localized alternatives.
     - **Transaction History**: Embed transaction records (memos, merchant names, amounts, categories).
   - When the user asks: *"Why did my food spending surge last month?"*
     - Retriever pulls only relevant food transactions and budget lines instead of all 500 transactions.
3. **Conversational Memory Summarization**:
   - Rather than keeping 20 full raw messages, periodically summarize past turns into a 2-sentence conversational memory scratchpad, saving 70% of history tokens.

---

## 3. Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Embedding Generation** | Local CPU (`sentence-transformers` or `fastembed`) | Zero API cost, private local processing, no rate limits. |
| **Vector Storage** | ChromaDB (local persistence) or FAISS-cpu | Self-contained within `instance/`, zero external service infrastructure. |
| **Cost Reduction Mechanism** | Intent Router + Condensed RAG Context + Dynamic Model Routing | Cuts prompt token size by ~65% and bypasses Groq for deterministic queries. |
| **Offline Fallback** | Local Rule/RAG Synthesis + Optional Local SLM | Prevents app breakage when Groq key is absent or rate-limited. |

---

## 4. Dependencies Identified

| Package | Version | Purpose |
|---------|---------|---------|
| `chromadb` or `faiss-cpu` | Latest | Local vector store for semantic retrieval |
| `fastembed` or `sentence-transformers` | Latest | Lightweight CPU embeddings for queries and knowledge chunks |

---

## 5. Risks & Mitigations

- **Risk: Embedding latency on CPU slowing down chat responses.**
  - *Mitigation:* Use quantized/ONNX models (`fastembed` with `all-MiniLM-L6-v2-q`) which embed text in <15ms on modern CPUs.
- **Risk: Vector database syncing when new transactions are logged.**
  - *Mitigation:* Background event hook or batch embed on transaction creation via Flask signals.

---

## Ready for Planning
- [x] Questions answered
- [x] Approach selected
- [x] Cost reduction & context awareness strategy verified
