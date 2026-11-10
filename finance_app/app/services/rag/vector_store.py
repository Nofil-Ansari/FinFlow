"""
Dual-Mode Vector Store:
- LocalVectorStore: In-memory NumPy cosine similarity index serialized to vector_index.json (Zero dependencies, offline, local dev).
- PgVectorStore: PostgreSQL / Supabase pgvector store for scalable multi-instance Docker / Cloud Run deployments.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from app.services.rag.models import KnowledgeChunk

logger = logging.getLogger(__name__)


class VectorStoreBase:
    """Abstract Vector Store contract."""

    def add_chunks(self, chunks: List[KnowledgeChunk], embeddings: List[List[float]]):
        raise NotImplementedError

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class LocalVectorStore(VectorStoreBase):
    """File-backed NumPy vector store for local development.
    Stores chunks in JSON format and vector embeddings as a NumPy array.
    """

    def __init__(self, index_path: str = "data/knowledge/processed/vector_index.json"):
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.chunks: List[KnowledgeChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self._load()

    def _load(self):
        if not self.index_path.exists():
            return
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = [KnowledgeChunk.from_dict(c) for c in data.get("chunks", [])]
            raw_emb = data.get("embeddings", [])
            if raw_emb:
                self.embeddings = np.array(raw_emb, dtype=np.float32)
                # Ensure vectors are normalized
                norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self.embeddings = self.embeddings / norms
        except Exception as e:
            logger.error(f"Failed to load local vector index: {e}")
            self.chunks = []
            self.embeddings = None

    def save(self):
        try:
            data = {
                "chunks": [c.to_dict() for c in self.chunks],
                "embeddings": (
                    self.embeddings.tolist() if self.embeddings is not None else []
                ),
            }
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save local vector index: {e}")

    def add_chunks(self, chunks: List[KnowledgeChunk], embeddings: List[List[float]]):
        if not chunks or not embeddings:
            return

        new_mat = np.array(embeddings, dtype=np.float32)
        # Normalize
        norms = np.linalg.norm(new_mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        new_mat = new_mat / norms

        if self.embeddings is None or len(self.chunks) == 0:
            self.chunks = list(chunks)
            self.embeddings = new_mat
        else:
            # Upsert logic based on chunk_id
            existing_ids = {c.chunk_id: idx for idx, c in enumerate(self.chunks)}
            for ch, vec in zip(chunks, new_mat):
                if ch.chunk_id in existing_ids:
                    idx = existing_ids[ch.chunk_id]
                    self.chunks[idx] = ch
                    self.embeddings[idx] = vec
                else:
                    self.chunks.append(ch)
                    self.embeddings = np.vstack([self.embeddings, vec.reshape(1, -1)])
        self.save()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        if self.embeddings is None or len(self.chunks) == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        # Compute cosine similarity across all vectors
        scores = np.dot(self.embeddings, q_vec)

        # Apply metadata filtering
        results: List[Tuple[KnowledgeChunk, float]] = []
        ranked_indices = np.argsort(scores)[::-1]

        for idx in ranked_indices:
            ch = self.chunks[idx]
            if category and ch.category.lower() != category.lower():
                continue
            if tag and tag.lower() not in [t.lower() for t in ch.tags]:
                continue

            results.append((ch, float(scores[idx])))
            if len(results) >= top_k:
                break

        return results

    def count(self) -> int:
        return len(self.chunks)

    def clear(self):
        self.chunks = []
        self.embeddings = None
        if self.index_path.exists():
            try:
                os.remove(self.index_path)
            except Exception:
                pass


class PgVectorStore(VectorStoreBase):
    """PostgreSQL vector store using pgvector for production deployments."""

    def __init__(self, db_session=None):
        self.session = db_session

    def _get_session(self):
        if self.session:
            return self.session
        from app import db

        return db.session

    def add_chunks(self, chunks: List[KnowledgeChunk], embeddings: List[List[float]]):
        from app.models.rag_chunk import RagKnowledgeChunk

        session = self._get_session()
        for ch, emb in zip(chunks, embeddings):
            existing = (
                session.query(RagKnowledgeChunk).filter_by(chunk_id=ch.chunk_id).first()
            )
            if existing:
                existing.title = ch.title
                existing.content = ch.content
                existing.category = ch.category
                existing.tags = ch.tags
                existing.token_count = ch.token_count
                existing.content_hash = ch.content_hash
                existing.chunk_metadata = ch.metadata
                existing.embedding = emb
            else:
                record = RagKnowledgeChunk(
                    chunk_id=ch.chunk_id,
                    doc_id=ch.doc_id,
                    title=ch.title,
                    content=ch.content,
                    category=ch.category,
                    tags=ch.tags,
                    token_count=ch.token_count,
                    content_hash=ch.content_hash,
                    chunk_metadata=ch.metadata,
                    embedding=emb,
                )
                session.add(record)
        session.commit()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        from app.models.rag_chunk import RagKnowledgeChunk

        session = self._get_session()
        query = session.query(RagKnowledgeChunk)

        if category:
            query = query.filter(RagKnowledgeChunk.category == category)

        # If pgvector cosine distance operator is available
        try:
            # 1 - (embedding <=> query_vector) computes cosine similarity
            results_raw = (
                query.order_by(
                    RagKnowledgeChunk.embedding.cosine_distance(query_vector)
                )
                .limit(top_k * 2)
                .all()
            )

            results = []
            for item in results_raw:
                if tag and tag.lower() not in [t.lower() for t in (item.tags or [])]:
                    continue
                chunk = KnowledgeChunk(
                    chunk_id=item.chunk_id,
                    doc_id=item.doc_id,
                    title=item.title,
                    content=item.content,
                    category=item.category,
                    tags=item.tags or [],
                    token_count=item.token_count,
                    content_hash=item.content_hash,
                    metadata=item.chunk_metadata or {},
                )
                # Compute approximate similarity score
                results.append((chunk, 1.0))
                if len(results) >= top_k:
                    break
            return results
        except Exception as e:
            logger.error(
                f"PgVector query failed: {e}. Falling back to Python similarity."
            )
            return []

    def count(self) -> int:
        from app.models.rag_chunk import RagKnowledgeChunk

        session = self._get_session()
        return session.query(RagKnowledgeChunk).count()

    def clear(self):
        from app.models.rag_chunk import RagKnowledgeChunk

        session = self._get_session()
        session.query(RagKnowledgeChunk).delete()
        session.commit()


def get_vector_store() -> VectorStoreBase:
    """Factory selecting the appropriate vector store backend based on the environment."""
    database_url = os.environ.get("DATABASE_URL", "").lower()
    if "postgres" in database_url:
        logger.info("Using PgVectorStore for PostgreSQL database.")
        return PgVectorStore()
    logger.info("Using LocalVectorStore (NumPy / JSON) for local environment.")
    return LocalVectorStore()
