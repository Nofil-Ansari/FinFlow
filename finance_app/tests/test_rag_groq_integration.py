"""
Unit and integration tests for RAG Phase 4: Groq Advisor Integration & Prompt Synthesis.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from app.services.rag.models import KnowledgeChunk
from app.services.rag.retrieval import RetrievalResult
from app.services.rag.prompt_synthesizer import PromptSynthesizer, get_rag_retriever
from app.services.recommender import build_groq_context


class TestRagGroqIntegration(unittest.TestCase):

    def setUp(self):
        self.sample_chunk = KnowledgeChunk(
            chunk_id="fbr-tax-slabs-2024-02",
            doc_id="fbr-income-tax-2024-2025",
            title="Salaried Individuals Income Tax Slabs (2024-2025)",
            content="Income between PKR 1,200,000 and 2,400,000: Tax is PKR 30,000 plus 15% of the amount exceeding PKR 1,200,000.",
            category="tax_rates",
            tags=["tax", "salary", "fbr"],
            token_count=35,
            metadata={"authority": "Federal Board of Revenue (FBR)", "tax_year": "2024-2025"}
        )
        self.sample_result = RetrievalResult(
            chunk=self.sample_chunk,
            score=0.85,
            vector_score=0.82,
            lexical_score=0.88,
            citation="[Source: Salaried Individuals Income Tax Slabs | FBR (2024-2025)]",
            matched_terms=["tax", "salary"]
        )

    def test_prompt_synthesizer_formatting(self):
        context_str = PromptSynthesizer.format_context([self.sample_result])
        self.assertIn("=== VERIFIED PAKISTANI FINANCIAL KNOWLEDGE BASE ===", context_str)
        self.assertIn("Source ID: fbr-tax-slabs-2024-02", context_str)
        self.assertIn("Citation Label: [Source: Salaried Individuals Income Tax Slabs | FBR (2024-2025)]", context_str)
        self.assertIn("Federal Board of Revenue (FBR)", context_str)
        self.assertIn("15% of the amount exceeding PKR 1,200,000", context_str)
        self.assertIn("CRITICAL INSTRUCTIONS FOR CITATIONS & GROUNDING", context_str)

    def test_prompt_synthesizer_token_budget_truncation(self):
        # Create multiple large dummy chunks that exceed MAX_CONTEXT_TOKENS (750)
        large_chunks = []
        for i in range(10):
            ch = KnowledgeChunk(
                chunk_id=f"chunk-{i}",
                doc_id="doc",
                title=f"Chunk {i}",
                content="Large test financial content " * 30,
                category="tax",
                token_count=150
            )
            res = RetrievalResult(
                chunk=ch,
                score=0.9 - (i * 0.05),
                vector_score=0.8,
                lexical_score=0.8,
                citation=f"[Source: Chunk {i}]"
            )
            large_chunks.append(res)

        formatted = PromptSynthesizer.format_context(large_chunks)
        # Should contain first few chunks, but stop before chunk-9 to prevent prompt overflow
        self.assertIn("Source ID: chunk-0", formatted)
        self.assertNotIn("Source ID: chunk-9", formatted)

    @patch("app.services.recommender._get_user_df")
    @patch("app.models.financial_profile.FinancialProfile.query")
    def test_build_groq_context_with_rag(self, mock_profile_query, mock_df):
        import pandas as pd
        mock_df.return_value = pd.DataFrame()
        mock_profile_query.filter_by.return_value.first.return_value = None

        # Build context with RAG chunks
        context = build_groq_context(user_id=1, retrieved_chunks=[self.sample_result])
        self.assertIn("=== VERIFIED PAKISTANI FINANCIAL KNOWLEDGE BASE ===", context)
        self.assertIn("fbr-tax-slabs-2024-02", context)

        # Build context without RAG chunks
        context_no_rag = build_groq_context(user_id=1, retrieved_chunks=None)
        self.assertNotIn("=== VERIFIED PAKISTANI FINANCIAL KNOWLEDGE BASE ===", context_no_rag)

    @patch("app.services.groq_middleware.AiChatMessage")
    @patch("app.services.groq_middleware.db.session")
    def test_fallback_response_grounded_in_rag(self, mock_db, mock_chat_msg):
        from app.services.groq_middleware import GroqMiddleware
        
        fallback = GroqMiddleware._fallback_response(
            "What is the tax on 150,000 monthly salary?",
            retrieved_chunks=[self.sample_result]
        )
        self.assertIn("Verified Regulatory Insights", fallback)
        self.assertIn("[Source: Salaried Individuals Income Tax Slabs | FBR (2024-2025)]", fallback)
        self.assertIn("15% of the amount exceeding", fallback)


if __name__ == "__main__":
    unittest.main()

