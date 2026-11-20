"""
RAG Phase 5 — Benchmark Tests for Retrieval Quality & Anti-Hallucination.

Verifies:
  - Hit-rate@3 for each knowledge domain (tax, savings, zakat, substitutions)
  - Numerical accuracy: official rate figures must be present in top chunks
  - Anti-hallucination gating: off-topic queries return 0 results at high threshold
  - Retrieval latency: full pipeline must complete in < 500 ms
"""

import os
import shutil
import tempfile
import time
import unittest

from app.services.rag.models import KnowledgeChunk
from app.services.rag.embeddings import LocalTfidfEmbedding
from app.services.rag.vector_store import LocalVectorStore
from app.services.rag.retrieval import HybridRetriever


# ── Shared seeded corpus (mirrors the 4 real knowledge domains) ───────────────

SEED_CHUNKS = [
    # --- Tax Rates ---
    KnowledgeChunk(
        chunk_id="fbr-tax-01",
        doc_id="fbr-income-tax-2024-2025",
        title="Salaried Income Tax Rates (Tax Year 2024-2025)",
        content=(
            "Under Clause 1A, income tax on salaried individuals earning over 600,000 PKR "
            "begins at 5 percent up to 1,200,000 PKR. The FBR tax year 2024-2025 slabs "
            "also apply withholding tax (WHT) rules for filers and non-filers."
        ),
        category="tax_rates",
        tags=["tax", "fbr", "salary", "rates", "slab", "income tax"],
        metadata={"authority": "Federal Board of Revenue (FBR)", "tax_year": "2024-2025"},
    ),
    KnowledgeChunk(
        chunk_id="fbr-tax-02",
        doc_id="fbr-income-tax-2024-2025",
        title="FBR Non-Filer Withholding Tax Rates",
        content=(
            "Non-filers face a 2x withholding tax rate on cash withdrawals, property "
            "transactions, and vehicle purchases. FBR mandates registration on the Active "
            "Taxpayer List (ATL) to qualify for reduced WHT rates."
        ),
        category="tax_rates",
        tags=["tax", "fbr", "non-filer", "withholding", "atl"],
        metadata={"authority": "Federal Board of Revenue (FBR)", "tax_year": "2024-2025"},
    ),
    # --- National Savings ---
    KnowledgeChunk(
        chunk_id="cdns-behbood-01",
        doc_id="national-savings-schemes-rates",
        title="Behbood Savings Certificates (BSC)",
        content=(
            "Behbood Savings Certificates offered by CDNS provide an annual profit rate "
            "of 15.36 percent for senior citizens and widows. The minimum investment is "
            "PKR 500 and investment is available through National Savings Centres."
        ),
        category="national_savings",
        tags=["cdns", "behbood", "savings", "profit", "senior citizens"],
        metadata={"authority": "Central Directorate of National Savings (CDNS)"},
    ),
    KnowledgeChunk(
        chunk_id="cdns-ric-01",
        doc_id="national-savings-schemes-rates",
        title="Regular Income Certificate (RIC)",
        content=(
            "The Regular Income Certificate (RIC) from CDNS pays monthly profit at an "
            "annualized rate. It is Shariah-compliant and available to Pakistani nationals. "
            "Minimum investment is PKR 50,000."
        ),
        category="national_savings",
        tags=["cdns", "ric", "regular income", "savings", "monthly profit"],
        metadata={"authority": "Central Directorate of National Savings (CDNS)"},
    ),
    # --- Zakat ---
    KnowledgeChunk(
        chunk_id="zakat-cz50-01",
        doc_id="zakat-nisab-and-declarations",
        title="Zakat Deduction and Form CZ-50 Exemption",
        content=(
            "Zakat of 2.5 percent is deducted on 1st Ramadan from saving accounts exceeding "
            "the Nisab threshold. Form CZ-50 must be submitted to your bank before Ramadan "
            "to claim Shariah-based exemption from automatic deduction."
        ),
        category="zakat",
        tags=["zakat", "cz-50", "nisab", "deduction", "ramadan", "exemption"],
        metadata={"authority": "Ministry of Poverty Alleviation & Social Safety"},
    ),
    KnowledgeChunk(
        chunk_id="zakat-nisab-01",
        doc_id="zakat-nisab-and-declarations",
        title="Nisab Threshold for Zakat (2024-2025)",
        content=(
            "The Nisab for Zakat is equivalent to 7.5 tola of gold or 52.5 tola of silver. "
            "If your savings account balance exceeds this threshold on 1st Ramadan, Zakat "
            "at the rate of 2.5 percent will be deducted automatically by the bank."
        ),
        category="zakat",
        tags=["zakat", "nisab", "gold", "silver", "threshold"],
        metadata={"authority": "Ministry of Poverty Alleviation & Social Safety"},
    ),
    # --- Substitutions ---
    KnowledgeChunk(
        chunk_id="sub-transport-01",
        doc_id="pakistan-consumer-substitutions",
        title="Ride-Hailing & Transport Alternatives",
        content=(
            "InDrive offers 25-35 percent lower fares than Careem and Uber by allowing "
            "fare negotiation between riders and drivers. Bykea provides motorbike rides "
            "at significantly lower cost for short urban distances."
        ),
        category="substitutions",
        tags=["transport", "careem", "uber", "indrive", "bykea", "cheaper", "alternative"],
        metadata={"authority": "Market Survey"},
    ),
    KnowledgeChunk(
        chunk_id="sub-streaming-01",
        doc_id="pakistan-consumer-substitutions",
        title="Streaming & Entertainment Alternatives",
        content=(
            "Pakistani users can substitute Netflix (~PKR 1550/month) with Urduflix "
            "(PKR 300/month) or watch free content on Urdu1 and ARY Digital apps. "
            "Spotify can be replaced with YouTube Music free tier."
        ),
        category="substitutions",
        tags=["streaming", "netflix", "spotify", "urduflix", "cheaper", "alternative"],
        metadata={"authority": "Market Survey"},
    ),
]


class TestRagBenchmark(unittest.TestCase):
    """
    Benchmark test suite for the FinanceFlow hybrid retrieval engine.
    Uses a seeded in-memory corpus — no dependency on the real knowledge files.
    """

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.index_path = os.path.join(cls.test_dir, "benchmark_index.json")

        cls.embed_svc = LocalTfidfEmbedding(dimension=768)
        cls.vector_store = LocalVectorStore(index_path=cls.index_path)

        embeddings = cls.embed_svc.embed_batch(
            [f"{c.title}\n{c.content}" for c in SEED_CHUNKS]
        )
        cls.vector_store.add_chunks(SEED_CHUNKS, embeddings)

        # Standard retriever — low threshold so test fixture works deterministically
        cls.retriever = HybridRetriever(
            vector_store=cls.vector_store,
            embedding_service=cls.embed_svc,
            chunks=SEED_CHUNKS,
            relevance_threshold=0.01,
        )

        # High-threshold retriever for anti-hallucination tests
        cls.strict_retriever = HybridRetriever(
            vector_store=cls.vector_store,
            embedding_service=cls.embed_svc,
            chunks=SEED_CHUNKS,
            relevance_threshold=0.85,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    # ── Hit-Rate@3 Tests ──────────────────────────────────────────────────────

    def test_hit_rate_at_3_tax(self):
        """Query for salaried tax rates must return an FBR tax chunk in top-3."""
        results = self.retriever.retrieve("salaried income tax rate", top_k=3)
        self.assertGreaterEqual(len(results), 1, "Expected at least 1 result for tax query")

        hit = any(
            r.chunk.category == "tax_rates" and "fbr" in r.chunk.doc_id
            for r in results
        )
        self.assertTrue(hit, "Top-3 results must include an FBR tax_rates chunk")

    def test_hit_rate_at_3_savings(self):
        """Query for Behbood certificate must return a national_savings chunk in top-3."""
        results = self.retriever.retrieve("behbood certificate profit rate", top_k=3)
        self.assertGreaterEqual(len(results), 1, "Expected at least 1 result for savings query")

        hit = any(r.chunk.category == "national_savings" for r in results)
        self.assertTrue(hit, "Top-3 results must include a national_savings chunk")

    def test_hit_rate_at_3_zakat(self):
        """Query for Zakat CZ-50 form must return a zakat chunk in top-3."""
        results = self.retriever.retrieve("zakat deduction form cz-50", top_k=3)
        self.assertGreaterEqual(len(results), 1, "Expected at least 1 result for zakat query")

        hit = any(r.chunk.category == "zakat" for r in results)
        self.assertTrue(hit, "Top-3 results must include a zakat chunk")

    def test_hit_rate_at_3_substitutions(self):
        """Query for cheaper Careem alternative must return a substitutions chunk in top-3."""
        results = self.retriever.retrieve("cheaper alternative to careem", top_k=3)
        self.assertGreaterEqual(len(results), 1, "Expected at least 1 result for substitutions query")

        hit = any(r.chunk.category == "substitutions" for r in results)
        self.assertTrue(hit, "Top-3 results must include a substitutions chunk")

    # ── Numerical Accuracy Tests ──────────────────────────────────────────────

    def test_numerical_accuracy_zakat_rate(self):
        """Top chunk content for zakat query must contain the official 2.5% rate."""
        results = self.retriever.retrieve("zakat deduction form cz-50", top_k=3)
        self.assertGreaterEqual(len(results), 1, "No results returned for zakat query")

        zakat_results = [r for r in results if r.chunk.category == "zakat"]
        self.assertGreater(len(zakat_results), 0, "No zakat category results found")

        top_content = zakat_results[0].chunk.content
        self.assertIn(
            "2.5", top_content,
            f"Official Zakat rate '2.5' not found in top chunk content: {top_content[:200]}"
        )

    def test_numerical_accuracy_behbood_rate(self):
        """Top Behbood chunk must contain the official 15.36% annual yield."""
        results = self.retriever.retrieve("behbood certificate profit rate", top_k=3)
        self.assertGreaterEqual(len(results), 1, "No results returned for Behbood query")

        savings_results = [r for r in results if r.chunk.category == "national_savings"]
        self.assertGreater(len(savings_results), 0, "No national_savings results found")

        top_content = savings_results[0].chunk.content
        self.assertIn(
            "15.36", top_content,
            f"Official Behbood yield '15.36' not found in top chunk: {top_content[:200]}"
        )

    # ── Anti-Hallucination Gating Test ────────────────────────────────────────

    def test_anti_hallucination_gating(self):
        """
        Off-topic query at threshold=0.85 must return 0 results.
        This validates that the ReRanker gates irrelevant queries from poisoning responses.
        """
        results = self.strict_retriever.retrieve(
            "how to bake chocolate cake in Paris", top_k=3
        )
        self.assertEqual(
            len(results), 0,
            f"Expected 0 results for off-topic query at threshold=0.85, got {len(results)}"
        )

    # ── Latency Test ──────────────────────────────────────────────────────────

    def test_retrieval_latency(self):
        """Full hybrid retrieval pipeline must complete in under 500 ms."""
        query = "What are the income tax slabs for salaried employees in Pakistan 2024-2025?"

        start = time.monotonic()
        results = self.retriever.retrieve(query, top_k=5)
        elapsed_ms = (time.monotonic() - start) * 1000

        self.assertLess(
            elapsed_ms, 500,
            f"Retrieval took {elapsed_ms:.1f} ms — exceeded 500 ms budget"
        )
        # Also sanity-check that we actually got results (not short-circuited early)
        self.assertGreater(len(results), 0, "Latency test returned no results — pipeline may have errored")


if __name__ == "__main__":
    unittest.main(verbosity=2)

