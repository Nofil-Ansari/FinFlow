"""
Corpus ingestion pipeline reading raw documents, chunking, and outputting JSONL.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from .models import KnowledgeDocument, KnowledgeChunk
from .loader import DocumentLoader
from .chunker import MarkdownHeaderChunker


class CorpusPipeline:
    """Manages the full lifecycle of loading, validating, chunking, and saving knowledge."""

    def __init__(
        self,
        raw_dir: str = "data/knowledge/raw",
        processed_dir: str = "data/knowledge/processed",
        chunker: MarkdownHeaderChunker = None
    ):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.chunker = chunker or MarkdownHeaderChunker()

    def run(self) -> Tuple[List[KnowledgeDocument], List[KnowledgeChunk]]:
        """Run the end-to-end ingestion pipeline and write chunks.jsonl."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        docs = DocumentLoader.load_directory(str(self.raw_dir))
        all_chunks: List[KnowledgeChunk] = []

        for doc in docs:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)

        # Write output JSONL
        output_file = self.processed_dir / "chunks.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for ch in all_chunks:
                f.write(ch.to_json() + "\n")

        # Write metadata summary
        summary = {
            "total_documents": len(docs),
            "total_chunks": len(all_chunks),
            "categories": {},
            "document_ids": [d.doc_id for d in docs]
        }
        for ch in all_chunks:
            summary["categories"][ch.category] = summary["categories"].get(ch.category, 0) + 1

        with open(self.processed_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return docs, all_chunks

    def load_processed_chunks(self) -> List[KnowledgeChunk]:
        """Load already processed chunks from chunks.jsonl."""
        output_file = self.processed_dir / "chunks.jsonl"
        if not output_file.exists():
            return []

        chunks: List[KnowledgeChunk] = []
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(KnowledgeChunk.from_dict(json.loads(line.strip())))
        return chunks

