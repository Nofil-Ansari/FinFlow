"""
RAG (Retrieval-Augmented Generation) package for FinanceFlow.
Provides document loading, semantic chunking, embedding generation,
and context synthesis for localized financial advising.
"""

from .models import KnowledgeDocument, KnowledgeChunk
from .loader import DocumentLoader
from .chunker import MarkdownHeaderChunker
from .pipeline import CorpusPipeline

__all__ = [
    "KnowledgeDocument",
    "KnowledgeChunk",
    "DocumentLoader",
    "MarkdownHeaderChunker",
    "CorpusPipeline",
]

