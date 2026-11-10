"""
RAG (Retrieval-Augmented Generation) package for FinanceFlow.
Provides document loading, semantic chunking, embedding generation,
two-tier caching, dual-mode vector storage, and context synthesis.
"""

from .models import KnowledgeDocument, KnowledgeChunk
from .loader import DocumentLoader
from .chunker import MarkdownHeaderChunker
from .pipeline import CorpusPipeline
from .embeddings import (
    BaseEmbeddingService,
    LocalTfidfEmbedding,
    GeminiEmbeddingService,
    DiskCache,
    TwoTierCachedEmbeddingService,
)
from .vector_store import (
    VectorStoreBase,
    LocalVectorStore,
    PgVectorStore,
    get_vector_store,
)

__all__ = [
    "KnowledgeDocument",
    "KnowledgeChunk",
    "DocumentLoader",
    "MarkdownHeaderChunker",
    "CorpusPipeline",
    "BaseEmbeddingService",
    "LocalTfidfEmbedding",
    "GeminiEmbeddingService",
    "DiskCache",
    "TwoTierCachedEmbeddingService",
    "VectorStoreBase",
    "LocalVectorStore",
    "PgVectorStore",
    "get_vector_store",
]
