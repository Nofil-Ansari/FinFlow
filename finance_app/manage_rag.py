#!/usr/bin/env python
"""
manage_rag.py — CLI management utility for FinanceFlow RAG knowledge pipeline.

Commands:
  python manage_rag.py ingest        → Ingests and chunks documents into chunks.jsonl
  python manage_rag.py stats         → Prints corpus statistics and category counts
  python manage_rag.py search <q>    → Substring/keyword test query across chunks
  python manage_rag.py embed         → Generates 768-dim embeddings with 2-tier cache and builds vector index
  python manage_rag.py query <q>     → Semantic vector search returning top-k ranked chunks
  python manage_rag.py warm-cache    → Syncs disk cache embeddings into Redis L1
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.rag.pipeline import CorpusPipeline
from app.services.rag.embeddings import (
    GeminiEmbeddingService,
    LocalTfidfEmbedding,
    TwoTierCachedEmbeddingService,
)
from app.services.rag.vector_store import get_vector_store


def get_pipeline():
    base_dir = Path(__file__).parent
    raw_dir = base_dir / "data" / "knowledge" / "raw"
    processed_dir = base_dir / "data" / "knowledge" / "processed"
    return CorpusPipeline(raw_dir=str(raw_dir), processed_dir=str(processed_dir))


def get_embedding_service():
    """Builds two-tier cached embedding service using Gemini with Local TF-IDF fallback."""
    base_dir = Path(__file__).parent
    cache_dir = base_dir / "data" / "knowledge" / "processed" / "cache"
    gemini_svc = GeminiEmbeddingService()
    return TwoTierCachedEmbeddingService(
        inner_service=gemini_svc, cache_dir=str(cache_dir)
    )


def cmd_ingest():
    pipeline = get_pipeline()
    print("Running knowledge corpus ingestion pipeline...")
    docs, chunks = pipeline.run()
    print("✓ Ingestion complete!")
    print(f"  • Raw Documents Loaded     : {len(docs)}")
    print(f"  • Knowledge Chunks Produced: {len(chunks)}")
    print(f"  • Output JSONL: {pipeline.processed_dir / 'chunks.jsonl'}")


def cmd_stats():
    pipeline = get_pipeline()
    chunks = pipeline.load_processed_chunks()
    if not chunks:
        print(
            "No processed chunks found. Please run 'python manage_rag.py ingest' first."
        )
        return

    print("=== FinanceFlow RAG Knowledge Corpus Stats ===")
    print(f"Total Chunks: {len(chunks)}")

    categories = {}
    total_tokens = 0
    for ch in chunks:
        categories[ch.category] = categories.get(ch.category, 0) + 1
        total_tokens += ch.token_count

    print(f"Total Estimated Tokens: ~{total_tokens:,}")
    print(f"Average Tokens / Chunk: ~{int(total_tokens / len(chunks))}")
    print("\nChunks by Category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat:<25}: {count} chunks")


def cmd_search(query: str):
    pipeline = get_pipeline()
    chunks = pipeline.load_processed_chunks()
    if not chunks:
        print(
            "No processed chunks found. Please run 'python manage_rag.py ingest' first."
        )
        return

    q_lower = query.lower()
    matches = []
    for ch in chunks:
        if q_lower in ch.title.lower() or q_lower in ch.content.lower():
            matches.append(ch)

    print(
        f"\nKeyword search results for: '{query}' ({len(matches)} matching chunks)\n"
        + "─" * 60
    )
    for i, ch in enumerate(matches[:5], 1):
        print(f"[{i}] {ch.title} ({ch.category}) — ID: {ch.chunk_id}")
        preview = ch.content.strip().replace("\n", " ")[:160]
        print(f"    Excerpt: {preview}...\n")


def cmd_embed():
    pipeline = get_pipeline()
    chunks = pipeline.load_processed_chunks()
    if not chunks:
        print("No processed chunks found. Ingesting first...")
        _, chunks = pipeline.run()

    print(f"Embedding {len(chunks)} knowledge chunks...")
    embedding_svc = get_embedding_service()
    vector_store = get_vector_store()

    texts = [f"{c.title}\n{c.content}" for c in chunks]
    embeddings = embedding_svc.embed_batch(texts)

    print(
        f"Indexing {len(embeddings)} vectors into vector store ({vector_store.__class__.__name__})..."
    )
    vector_store.add_chunks(chunks, embeddings)
    print("✓ Vector store indexing complete!")
    print(f"  • Total indexed items: {vector_store.count()}")


def cmd_query(query: str, top_k: int = 5):
    embedding_svc = get_embedding_service()
    vector_store = get_vector_store()

    if vector_store.count() == 0:
        print("Vector store is empty. Please run 'python manage_rag.py embed' first.")
        return

    print(f"Generating query embedding for: '{query}'...")
    query_vec = embedding_svc.embed_text(query)

    print(f"Searching top {top_k} nearest neighbors...\n" + "─" * 60)
    results = vector_store.search(query_vec, top_k=top_k)

    if not results:
        print("No results found.")
        return

    for i, (chunk, score) in enumerate(results, 1):
        print(f"[{i}] Score: {score:.4f} | {chunk.title} ({chunk.category})")
        print(f"    Chunk ID: {chunk.chunk_id} | Authority: {chunk.jurisdiction}")
        preview = chunk.content.strip().replace("\n", " ")[:200]
        print(f"    Snippet: {preview}...\n")


def cmd_warm_cache():
    embedding_svc = get_embedding_service()
    if not embedding_svc.redis_client:
        print(
            "Redis is not configured or not running. Set REDIS_URL to use Redis warming."
        )
        return

    count = embedding_svc.warm_redis_from_disk()
    print(f"✓ Redis cache warming complete! Pushed {count} embeddings to Redis L1.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python manage_rag.py [ingest | stats | search <q> | embed | query <q> | warm-cache]"
        )
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "ingest":
        cmd_ingest()
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Please provide a search term, e.g. python manage_rag.py search tax")
            sys.exit(1)
        cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "embed":
        cmd_embed()
    elif cmd == "query":
        if len(sys.argv) < 3:
            print(
                "Please provide a query, e.g. python manage_rag.py query 'salary tax rates 2024'"
            )
            sys.exit(1)
        cmd_query(" ".join(sys.argv[2:]))
    elif cmd == "warm-cache":
        cmd_warm_cache()
    else:
        print(
            f"Unknown command '{cmd}'. Available: ingest, stats, search, embed, query, warm-cache"
        )
