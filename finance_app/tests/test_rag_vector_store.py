"""
Unit tests for RAG Phase 2: Embedding Engine, Two-Tier Cache & Dual-Mode Vector Store.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from app.services.rag.models import KnowledgeChunk
from app.services.rag.embeddings import (
    LocalTfidfEmbedding,
    DiskCache,
    TwoTierCachedEmbeddingService,
)
from app.services.rag.vector_store import LocalVectorStore


class TestEmbeddingAndVectorStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.test_dir, "cache")
        self.index_path = os.path.join(self.test_dir, "vector_index.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_local_tfidf_dimension_and_normalization(self):
        service = LocalTfidfEmbedding(dimension=768)
        vec = service.embed_text("FBR tax slabs on salaried income in Pakistan")
        self.assertEqual(len(vec), 768)

        # Check normalization (norm should be ~1.0)
        norm = sum(x**2 for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_disk_cache_hit_and_miss(self):
        cache = DiskCache(cache_dir=self.cache_dir)
        key = "test_sha256_hash"
        dummy_vec = [0.1] * 768

        self.assertIsNone(cache.get(key))
        cache.set(key, dummy_vec)

        # Reload cache from disk to verify persistence
        new_cache = DiskCache(cache_dir=self.cache_dir)
        self.assertEqual(new_cache.get(key), dummy_vec)

    def test_two_tier_cache_graceful_failover_without_redis(self):
        # Explicitly pass non-existent/invalid redis URL
        inner = LocalTfidfEmbedding(dimension=768)
        cached_svc = TwoTierCachedEmbeddingService(
            inner_service=inner,
            redis_url="redis://localhost:9999/0",
            cache_dir=self.cache_dir,
        )
        # Should not raise exception and should fall back to disk cache
        vec = cached_svc.embed_text("State Bank of Pakistan policy rate floor")
        self.assertEqual(len(vec), 768)

        # Second call should be a cache hit from disk
        vec2 = cached_svc.embed_text("State Bank of Pakistan policy rate floor")
        self.assertEqual(vec, vec2)

    def test_local_vector_store_indexing_and_search(self):
        store = LocalVectorStore(index_path=self.index_path)
        embed_svc = LocalTfidfEmbedding(dimension=768)

        chunk1 = KnowledgeChunk(
            chunk_id="fbr-01",
            doc_id="fbr",
            title="Salaried Income Tax Rates",
            content="Income tax for salaried individuals earning over 600,000 PKR begins at 5 percent.",
            category="tax_rates",
            tags=["tax", "fbr", "salary"],
        )
        chunk2 = KnowledgeChunk(
            chunk_id="sbp-01",
            doc_id="sbp",
            title="SBP Monetary Policy",
            content="The State Bank of Pakistan monetary policy rate dictates commercial bank lending floors.",
            category="banking",
            tags=["banking", "sbp", "rate"],
        )

        chunks = [chunk1, chunk2]
        embeddings = embed_svc.embed_batch([f"{c.title}\n{c.content}" for c in chunks])
        store.add_chunks(chunks, embeddings)

        self.assertEqual(store.count(), 2)

        # Query relevant to tax
        q_vec = embed_svc.embed_text("salaried individual tax percentage")
        results = store.search(q_vec, top_k=2)

        self.assertGreater(len(results), 0)
        top_chunk, score = results[0]
        self.assertEqual(top_chunk.chunk_id, "fbr-01")
        self.assertGreater(score, 0.0)

    def test_vector_store_category_filtering(self):
        store = LocalVectorStore(index_path=self.index_path)
        embed_svc = LocalTfidfEmbedding(dimension=768)

        chunk1 = KnowledgeChunk(
            chunk_id="fbr-01",
            doc_id="fbr",
            title="Tax Slabs",
            content="FBR income tax details",
            category="tax_rates",
        )
        chunk2 = KnowledgeChunk(
            chunk_id="sbp-01",
            doc_id="sbp",
            title="Banking Guidelines",
            content="State Bank monetary guidelines",
            category="banking",
        )
        store.add_chunks(
            [chunk1, chunk2],
            embed_svc.embed_batch([c.content for c in [chunk1, chunk2]]),
        )

        # Filter strictly by banking
        q_vec = embed_svc.embed_text("tax guidelines")
        filtered_results = store.search(q_vec, top_k=5, category="banking")
        self.assertEqual(len(filtered_results), 1)
        self.assertEqual(filtered_results[0][0].chunk_id, "sbp-01")


if __name__ == "__main__":
    unittest.main()
