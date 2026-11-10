"""
RagKnowledgeChunk model for PostgreSQL / pgvector persistent vector indexing.
Conditionally guarded so environments without pgvector or PostgreSQL run cleanly without errors.
"""

from typing import Dict, Any
from app import db

try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None


class RagKnowledgeChunk(db.Model):
    """SQLAlchemy model for storing chunk embeddings in PostgreSQL (pgvector).
    Optimized for multi-instance Cloud Run serverless deployments.
    """

    __tablename__ = "rag_knowledge_chunks"

    id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    doc_id = db.Column(db.String(128), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)
    tags = db.Column(db.JSON, nullable=True)
    token_count = db.Column(db.Integer, default=0)
    content_hash = db.Column(db.String(64), nullable=False, index=True)
    chunk_metadata = db.Column(db.JSON, nullable=True)

    if PGVECTOR_AVAILABLE:
        embedding = db.Column(Vector(768))
    else:
        # Fallback column type if pgvector is not installed locally
        embedding = db.Column(db.JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags or [],
            "token_count": self.token_count,
            "content_hash": self.content_hash,
            "metadata": self.chunk_metadata or {},
        }
