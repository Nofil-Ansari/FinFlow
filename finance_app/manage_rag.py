#!/usr/bin/env python
"""
manage_rag.py — CLI management utility for FinanceFlow RAG knowledge pipeline.

Commands:
  python manage_rag.py ingest    → Ingests and chunks documents into chunks.jsonl
  python manage_rag.py stats     → Prints corpus statistics and category counts
  python manage_rag.py search <q> → Simple substring/keyword test query across chunks
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.rag.pipeline import CorpusPipeline


def get_pipeline():
    base_dir = Path(__file__).parent
    raw_dir = base_dir / "data" / "knowledge" / "raw"
    processed_dir = base_dir / "data" / "knowledge" / "processed"
    return CorpusPipeline(raw_dir=str(raw_dir), processed_dir=str(processed_dir))


def cmd_ingest():
    pipeline = get_pipeline()
    print("Running knowledge corpus ingestion pipeline...")
    docs, chunks = pipeline.run()
    print(f"✓ Ingestion complete!")
    print(f"  • Raw Documents Loaded : {len(docs)}")
    print(f"  • Knowledge Chunks Produced: {len(chunks)}")
    print(f"  • Output JSONL: {pipeline.processed_dir / 'chunks.jsonl'}")


def cmd_stats():
    pipeline = get_pipeline()
    chunks = pipeline.load_processed_chunks()
    if not chunks:
        print("No processed chunks found. Please run 'python manage_rag.py ingest' first.")
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
        print("No processed chunks found. Please run 'python manage_rag.py ingest' first.")
        return

    q_lower = query.lower()
    matches = []
    for ch in chunks:
        if q_lower in ch.title.lower() or q_lower in ch.content.lower():
            matches.append(ch)

    print(f"\nSearch results for: '{query}' ({len(matches)} matching chunks)\n" + "─" * 60)
    for i, ch in enumerate(matches[:5], 1):
        print(f"[{i}] {ch.title} ({ch.category}) — ID: {ch.chunk_id}")
        preview = ch.content.strip().replace("\n", " ")[:160]
        print(f"    Excerpt: {preview}...\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_rag.py [ingest | stats | search <query>]")
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
    else:
        print(f"Unknown command '{cmd}'. Available: ingest, stats, search")

