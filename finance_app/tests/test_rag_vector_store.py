"""
Unit tests for RAG Phase 2: Embedding Engine, Two-Tier Cache & Dual-Mode Vector Store.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch, MagicMock

from app.services.rag.models import KnowledgeChunk
from app.services.rag.embeddings import (
    LocalTfidfEmbedding,
    GeminiEmbeddingService,
    DiskCache,
    TwoTierCachedEmbeddingService,
)
from app.services.rag.vector_store import LocalVectorStore, PgVectorStore


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

    def test_gemini_fallback_indicator_and_cache_bypass(self):
        gemini_svc = GeminiEmbeddingService(api_key="")
        cached_svc = TwoTierCachedEmbeddingService(
            inner_service=gemini_svc,
            cache_dir=self.cache_dir,
        )
        vec = cached_svc.embed_text("sample fallback text")
        self.assertEqual(len(vec), 768)
        self.assertTrue(getattr(vec, "is_fallback", False))

        # Ensure fallback embeddings are NOT written to disk cache
        cache = DiskCache(cache_dir=self.cache_dir)
        h = cached_svc._hash_text("sample fallback text")
        self.assertIsNone(cache.get(h))

    @patch("requests.post")
    def test_gemini_header_key_and_output_dimensionality(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embedding": {"values": [0.05] * 768}}
        mock_post.return_value = mock_resp

        svc = GeminiEmbeddingService(api_key="secret-key-xyz")
        vec = svc.embed_text("test query")

        self.assertEqual(len(vec), 768)
        self.assertFalse(getattr(vec, "is_fallback", True))

        # Check call arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        called_url = args[0]
        # Key must NOT be in URL
        self.assertNotIn("secret-key-xyz", called_url)
        self.assertEqual(
            called_url,
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent",
        )

        # Key must be in header
        self.assertEqual(kwargs["headers"].get("x-goog-api-key"), "secret-key-xyz")

        # Payload must include outputDimensionality: 768
        self.assertEqual(kwargs["json"].get("outputDimensionality"), 768)
        self.assertEqual(kwargs["json"].get("model"), "models/gemini-embedding-001")

    def test_pg_vector_store_search_error_rolls_back_and_raises(self):
        mock_session = MagicMock()
        mock_session.query.side_effect = RuntimeError("Database connection lost")
        store = PgVectorStore(db_session=mock_session)

        with self.assertRaises(RuntimeError):
            store.search([0.1] * 768, top_k=5)

        mock_session.rollback.assert_called_once()

    def test_pg_vector_store_search_scoring_and_tag_filter(self):
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.add_columns.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        mock_item = MagicMock()
        mock_item.chunk_id = "chunk-1"
        mock_item.doc_id = "doc-1"
        mock_item.title = "Test Title"
        mock_item.content = "Test Content"
        mock_item.category = "Taxation"
        mock_item.tags = ["fbr", "tax"]
        mock_item.token_count = 50
        mock_item.content_hash = "hash123"
        mock_item.chunk_metadata = {"authority": "FBR"}

        # Simulate cosine distance = 0.25 -> similarity should be 1 - 0.25 = 0.75
        mock_query.limit.return_value.all.return_value = [(mock_item, 0.25)]

        store = PgVectorStore(db_session=mock_session)
        results = store.search(
            query_vector=[0.1] * 768,
            top_k=3,
            category="taxation",
            tag="tax",
        )

        self.assertEqual(len(results), 1)
        chunk, score = results[0]
        self.assertEqual(chunk.chunk_id, "chunk-1")
        self.assertAlmostEqual(score, 0.75, places=4)
        self.assertEqual(chunk.metadata["authority"], "FBR")


if __name__ == "__main__":
    unittest.main()
