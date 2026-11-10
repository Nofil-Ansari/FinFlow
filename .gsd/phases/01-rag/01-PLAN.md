---
phase: 1
plan: 01
type: standard
autonomous: true
wave: 1
depends_on: []
---

# Plan 01-01: Knowledge Corpus Curation & Ingestion Pipeline

<objective>
Curate authoritative, localized personal finance knowledge documents for Pakistan (FBR tax slabs 2024-2025, SBP banking regulations, National Savings schemes, Zakat nisab rules, and product substitutions) and build an extensible document loader, semantic chunking engine, and metadata enrichment pipeline.
</objective>

<context>
- `.gsd/ROADMAP.md`
- `.gsd/STATE.md`
- `finance_app/app/services/recommender.py`
- `finance_app/app/services/groq_middleware.py`
</context>

<tasks>

<task type="auto" name="Curate Raw Knowledge Corpus Documents">
<files>
- `finance_app/data/knowledge/raw/01_fbr_income_tax_2024_2025.md`
- `finance_app/data/knowledge/raw/02_national_savings_schemes_rates.md`
- `finance_app/data/knowledge/raw/03_sbp_banking_regulations_monetary.md`
- `finance_app/data/knowledge/raw/04_zakat_nisab_and_declarations.md`
- `finance_app/data/knowledge/raw/05_pakistan_consumer_substitutions.json`
</files>
<action>
Author clean, structured Markdown documents with YAML frontmatter containing accurate rates, official formulas, slab thresholds, and tabular data for Pakistani personal finance. Expand substitutions into structured JSON.
</action>
<verify>
Ensure all 5 raw corpus documents exist and have valid YAML frontmatter and markdown tables.
</verify>
<done>
All 5 raw documents authored with verified data for Tax Year 2024-2025.
</done>
</task>

<task type="auto" name="Build Ingestion, Chunking & Normalization Engine">
<files>
- `finance_app/app/services/rag/__init__.py`
- `finance_app/app/services/rag/models.py`
- `finance_app/app/services/rag/loader.py`
- `finance_app/app/services/rag/chunker.py`
- `finance_app/app/services/rag/pipeline.py`
- `finance_app/manage_rag.py`
</files>
<action>
Implement `KnowledgeChunk` data models, `DocumentLoader` for frontmatter/body extraction, `MarkdownHeaderChunker` preserving table and heading context without truncating tabular data, `CorpusPipeline` for outputting `chunks.jsonl`, and `manage_rag.py` CLI.
</action>
<verify>
Run `python manage_rag.py ingest` to verify `data/knowledge/processed/chunks.jsonl` generates without error.
</verify>
<done>
Pipeline creates chunks with metadata (source, category, tags, token counts, SHA256 hashes).
</done>
</task>

<task type="auto" name="Create Unit Tests & Validation Harness">
<files>
- `finance_app/tests/test_rag_ingestion.py`
</files>
<action>
Write comprehensive unit tests asserting document frontmatter parsing, table integrity preservation across chunk boundaries, metadata propagation, and idempotency of chunk generation.
</action>
<verify>
Run test suite: `python -m unittest tests/test_rag_ingestion.py`
</verify>
<done>
All unit tests pass with 100% success rate.
</done>
</task>

</tasks>

<success_criteria>
- [ ] 5 raw localized Pakistani finance knowledge documents created.
- [ ] RAG ingestion engine (`loader.py`, `chunker.py`, `pipeline.py`) operational.
- [ ] `chunks.jsonl` produced with verified token counts and content hashes.
- [ ] Unit test suite passing cleanly.
</success_criteria>

