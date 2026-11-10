"""
Unit tests for RAG Knowledge Corpus Curation & Ingestion Pipeline (Phase 1).
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from app.services.rag.models import KnowledgeDocument, KnowledgeChunk, compute_content_hash, estimate_token_count
from app.services.rag.loader import DocumentLoader, parse_markdown_frontmatter
from app.services.rag.chunker import MarkdownHeaderChunker
from app.services.rag.pipeline import CorpusPipeline


class TestRagIngestion(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.test_dir) / "raw"
        self.processed_dir = Path(self.test_dir) / "processed"
        self.raw_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_frontmatter_parser(self):
        sample = """---
title: "Test Tax Slabs"
category: "Taxation"
tags: ["tax", "fbr"]
jurisdiction: "Pakistan"
---

# Title
Sample body content.
"""
        meta, body = parse_markdown_frontmatter(sample)
        self.assertEqual(meta["title"], "Test Tax Slabs")
        self.assertEqual(meta["category"], "Taxation")
        self.assertEqual(meta["tags"], ["tax", "fbr"])
        self.assertIn("Sample body content", body)

    def test_document_loader_and_hashing(self):
        sample_path = self.raw_dir / "01_test.md"
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write("""---
title: "Doc 1"
category: "Banking"
---
# SBP Regulations
Banking rules content.
""")
        doc = DocumentLoader.load_markdown_file(str(sample_path))
        self.assertEqual(doc.title, "Doc 1")
        self.assertEqual(doc.category, "Banking")
        self.assertTrue(len(doc.content_hash) > 10)

    def test_table_preservation_in_chunker(self):
        doc = KnowledgeDocument(
            doc_id="test_tables",
            title="Tax Slabs",
            category="Taxation",
            body="""
## Slabs Table
Here are the official tax slabs:

| Slab | Range | Rate |
|---|---|---|
| 1 | 0-600k | 0% |
| 2 | 600k-1200k | 5% |
| 3 | 1200k-2200k | 15% |

Keep table together!
"""
        )
        chunker = MarkdownHeaderChunker(target_chunk_tokens=100)
        chunks = chunker.chunk_document(doc)
        self.assertGreaterEqual(len(chunks), 1)
        # Verify the entire markdown table is intact inside the chunk
        self.assertIn("| Slab | Range | Rate |", chunks[0].content)
        self.assertIn("| 3 | 1200k-2200k | 15% |", chunks[0].content)

    def test_end_to_end_corpus_pipeline(self):
        # Point to actual production knowledge folder
        base_dir = Path(__file__).resolve().parent.parent
        actual_raw_dir = base_dir / "data" / "knowledge" / "raw"
        
        self.assertTrue(actual_raw_dir.exists(), f"Raw knowledge dir not found at {actual_raw_dir}")

        pipeline = CorpusPipeline(
            raw_dir=str(actual_raw_dir),
            processed_dir=str(self.processed_dir)
        )
        docs, chunks = pipeline.run()

        self.assertGreaterEqual(len(docs), 5, "Expected at least 5 raw documents/substitutions categories")
        self.assertGreater(len(chunks), 15, "Expected at least 15 granular chunks")

        # Verify output files
        jsonl_path = self.processed_dir / "chunks.jsonl"
        manifest_path = self.processed_dir / "manifest.json"
        self.assertTrue(jsonl_path.exists())
        self.assertTrue(manifest_path.exists())

        # Test reload from disk
        reloaded = pipeline.load_processed_chunks()
        self.assertEqual(len(reloaded), len(chunks))

        # Check essential categories present
        cats = {c.category for c in reloaded}
        self.assertIn("Taxation", cats)
        self.assertIn("Investments", cats)
        self.assertIn("Banking", cats)
        self.assertIn("Zakat & Charity", cats)
        self.assertIn("Consumer Substitutions", cats)


if __name__ == "__main__":
    unittest.main()

