"""
RAG (Retrieval-Augmented Generation) package for FinanceFlow.
Provides document loading, semantic chunking, embedding generation,
two-tier caching, dual-mode vector storage, hybrid retrieval, prompt synthesis, and context grounding.
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
from .retrieval import (
    QueryProcessor,
    LexicalMatcher,
    ReRanker,
    HybridRetriever,
    RetrievalResult,
)
from .prompt_synthesizer import (
    PromptSynthesizer,
    get_rag_retriever,
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
    "QueryProcessor",
    "LexicalMatcher",
    "ReRanker",
    "HybridRetriever",
    "RetrievalResult",
    "PromptSynthesizer",
    "get_rag_retriever",
]
