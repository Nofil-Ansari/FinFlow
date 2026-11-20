"""
Unit tests for RAG Phase 3: Hybrid Semantic Retrieval & Re-ranking Layer.
"""

import os
import shutil
import tempfile
import unittest

from app.services.rag.models import KnowledgeChunk
from app.services.rag.embeddings import LocalTfidfEmbedding
from app.services.rag.vector_store import LocalVectorStore
from app.services.rag.retrieval import (
    QueryProcessor,
    LexicalMatcher,
    ReRanker,
    HybridRetriever,
)


class TestRagRetrieval(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.test_dir, "test_vector_index.json")
        self.embed_svc = LocalTfidfEmbedding(dimension=768)
        self.vector_store = LocalVectorStore(index_path=self.index_path)

        # Sample test corpus
        self.chunks = [
            KnowledgeChunk(
                chunk_id="fbr-tax-01",
                doc_id="fbr-tax",
                title="Salaried Income Tax Rates (Tax Year 2024-2025)",
                content="Under Clause 1A, income tax on salaried individuals earning over 600,000 PKR begins at 5 percent up to 1,200,000 PKR.",
                category="tax_rates",
                tags=["tax", "fbr", "salary", "rates"],
                metadata={"authority": "Federal Board of Revenue (FBR)", "tax_year": "2024-2025"}
            ),
            KnowledgeChunk(
                chunk_id="cdns-behbood-01",
                doc_id="cdns-schemes",
                title="Behbood Savings Certificates (BSC)",
                content="Behbood Savings Certificates offered by CDNS provide an annual profit rate of 15.36 percent for senior citizens and widows.",
                category="national_savings",
                tags=["cdns", "behbood", "savings", "profit"],
                metadata={"authority": "Central Directorate of National Savings (CDNS)"}
            ),
            KnowledgeChunk(
                chunk_id="zakat-cz50-01",
                doc_id="zakat-rules",
                title="Zakat Deduction and Form CZ-50 Exemption",
                content="Zakat of 2.5 percent is deducted on 1st Ramadan from saving accounts. Form CZ-50 must be submitted for exemption.",
                category="zakat",
                tags=["zakat", "cz-50", "nisab", "deduction"],
                metadata={"authority": "Ministry of Poverty Alleviation & Social Safety"}
            ),
            KnowledgeChunk(
                chunk_id="sub-transport-01",
                doc_id="substitutions",
                title="Ride-Hailing & Transport Alternatives",
                content="InDrive offers 25-35 percent lower fares than Careem and Uber by allowing fare negotiation.",
                category="substitutions",
                tags=["transport", "careem", "uber", "indrive"],
                metadata={"authority": "Market Survey"}
            ),
        ]

        # Seed vector store
        embeddings = self.embed_svc.embed_batch([f"{c.title}\n{c.content}" for c in self.chunks])
        self.vector_store.add_chunks(self.chunks, embeddings)

        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_service=self.embed_svc,
            chunks=self.chunks,
            relevance_threshold=0.01  # Low threshold for test fixture verification
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_query_normalization_currency_and_slang(self):
        # 1.5 lakh -> 150000 PKR
        norm = QueryProcessor.normalize_query("What is the tax on 1.5 lakh salary?")
        self.assertIn("150000 PKR", norm)

        # 25k -> 25000 PKR
        norm_k = QueryProcessor.normalize_query("Need 25k bachat plan")
        self.assertIn("25000 PKR", norm_k)
        self.assertIn("savings", norm_k)

        # 2 crore -> 20000000 PKR
        norm_c = QueryProcessor.normalize_query("2 crore investment")
        self.assertIn("20000000 PKR", norm_c)

    def test_detect_category_intent(self):
        cat1 = QueryProcessor.detect_category_intent("FBR income tax slabs for filers")
        self.assertEqual(cat1, "tax_rates")

        cat2 = QueryProcessor.detect_category_intent("Behbood CDNS savings profit")
        self.assertEqual(cat2, "national_savings")

        cat3 = QueryProcessor.detect_category_intent("Form CZ-50 zakat exemption")
        self.assertEqual(cat3, "zakat")

        cat4 = QueryProcessor.detect_category_intent("Cheaper alternative to Careem")
        self.assertEqual(cat4, "substitutions")

    def test_lexical_matcher_exact_term_hit(self):
        matcher = LexicalMatcher(self.chunks)
        results = matcher.search("CZ-50 zakat exemption", top_k=2)
        self.assertGreater(len(results), 0)
        top_chunk, score, matched = results[0]
        self.assertEqual(top_chunk.chunk_id, "zakat-cz50-01")
        self.assertIn("cz-50", [m.lower() for m in matched])

    def test_hybrid_retrieval_and_authority_boost(self):
        results = self.retriever.retrieve("What are the salaried income tax rates for 2024?", top_k=2)
        self.assertGreater(len(results), 0)
        top_result = results[0]
        self.assertEqual(top_result.chunk.chunk_id, "fbr-tax-01")
        self.assertIn("FBR", top_result.citation)
        self.assertGreater(top_result.score, 0.0)

    def test_relevance_gating_on_unrelated_query(self):
        # High-threshold retriever to verify gating
        gated_retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_service=self.embed_svc,
            chunks=self.chunks,
            relevance_threshold=0.85
        )
        # Random non-financial query
        results = gated_retriever.retrieve("How do I make chocolate chip cookies in Paris?", top_k=3)
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()

