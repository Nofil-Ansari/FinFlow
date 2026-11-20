"""
Prompt Synthesizer and RAG Retriever Singleton Factory.
Formats retrieved knowledge chunks into token-budgeted, guardrailed system prompt sections,
and caches the HybridRetriever in memory for low-latency chat inference.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

from app.services.rag.retrieval import HybridRetriever, RetrievalResult
from app.services.rag.pipeline import CorpusPipeline
from app.services.rag.embeddings import GeminiEmbeddingService, TwoTierCachedEmbeddingService
from app.services.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# Global singleton cache for the hybrid retriever
_GLOBAL_RETRIEVER: Optional[HybridRetriever] = None


class PromptSynthesizer:
    """Formats retrieved chunks into token-bounded, guardrailed system prompt context."""

    MAX_CONTEXT_TOKENS: int = 750

    @classmethod
    def format_context(cls, results: List[RetrievalResult]) -> str:
        """Formats a list of RetrievalResult objects into a structured XML/Markdown prompt block."""
        if not results:
            return ""

        context_blocks = []
        cumulative_tokens = 0

        for r in results:
            chunk = r.chunk
            tokens = chunk.token_count or (len(chunk.content.split()) * 4 // 3)
            if cumulative_tokens + tokens > cls.MAX_CONTEXT_TOKENS and context_blocks:
                # Stop if adding this chunk would exceed our token budget
                break

            block = (
                f"---\n"
                f"Source ID: {chunk.chunk_id}\n"
                f"Citation Label: {r.citation}\n"
                f"Authority: {chunk.metadata.get('authority') or chunk.jurisdiction}\n"
                f"Content:\n{chunk.content.strip()}\n"
            )
            context_blocks.append(block)
            cumulative_tokens += tokens

        if not context_blocks:
            return ""

        joined_blocks = "\n".join(context_blocks)
        return (
            "\n=== VERIFIED PAKISTANI FINANCIAL KNOWLEDGE BASE ===\n"
            "CRITICAL INSTRUCTIONS FOR CITATIONS & GROUNDING:\n"
            "1. When answering questions regarding tax slabs, withholding taxes (WHT), SBP policy rates,\n"
            "   National Savings certificate profit rates, Zakat nisab/deductions, or local product alternatives,\n"
            "   you MUST ground your answer in the verified excerpts below.\n"
            "2. Whenever you use information from an excerpt, cite it using its exact Citation Label,\n"
            "   e.g. '[Source: Title | Authority (Year)]'.\n"
            "3. If the user asks a financial regulatory question not covered by these excerpts or their personal\n"
            "   ledger, clearly state that you do not have the verified regulatory rate on file rather than guessing.\n\n"
            f"{joined_blocks}\n"
            "=== END VERIFIED KNOWLEDGE BASE ===\n"
        )


def get_rag_retriever(force_reload: bool = False) -> HybridRetriever:
    """Lazy singleton factory returning an initialized, in-memory HybridRetriever instance."""
    global _GLOBAL_RETRIEVER

    if _GLOBAL_RETRIEVER is not None and not force_reload:
        return _GLOBAL_RETRIEVER

    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "data" / "knowledge" / "raw"
    processed_dir = base_dir / "data" / "knowledge" / "processed"
    cache_dir = processed_dir / "cache"

    pipeline = CorpusPipeline(raw_dir=str(raw_dir), processed_dir=str(processed_dir))
    chunks = pipeline.load_processed_chunks()

    # If processed chunks don't exist yet, run ingestion pipeline
    if not chunks:
        logger.info("Processed RAG chunks not found. Ingesting corpus now...")
        _, chunks = pipeline.run()

    embedding_svc = TwoTierCachedEmbeddingService(
        inner_service=GeminiEmbeddingService(),
        cache_dir=str(cache_dir)
    )
    vector_store = get_vector_store()

    # If vector store is empty, embed chunks
    if vector_store.count() == 0 and chunks:
        logger.info("Vector store index is empty. Embedding and indexing knowledge chunks...")
        texts = [f"{c.title}\n{c.content}" for c in chunks]
        embeddings = embedding_svc.embed_batch(texts)
        vector_store.add_chunks(chunks, embeddings)

    _GLOBAL_RETRIEVER = HybridRetriever(
        vector_store=vector_store,
        embedding_service=embedding_svc,
        chunks=chunks,
        relevance_threshold=0.30
    )
    return _GLOBAL_RETRIEVER

