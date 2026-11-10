"""
Data models for the RAG ingestion pipeline.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import hashlib
import json


def compute_content_hash(text: str) -> str:
    """Compute SHA256 hex digest of normalized string content."""
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def estimate_token_count(text: str) -> int:
    """Approximate token count without mandatory C-bindings.
    Standard heuristic for English & technical financial text:
    ~1 word = 1.33 tokens, or len(text)/4.
    """
    if not text:
        return 0
    words = len(text.split())
    char_estimate = len(text) // 4
    return max(int(words * 1.33), char_estimate, 1)


@dataclass
class KnowledgeDocument:
    """Represents a raw document loaded from the corpus."""
    doc_id: str
    title: str
    category: str
    body: str
    source_url: Optional[str] = None
    jurisdiction: str = "Pakistan"
    authority: Optional[str] = None
    effective_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash and self.body:
            self.content_hash = compute_content_hash(self.body)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeChunk:
    """Represents a chunk derived from a KnowledgeDocument ready for embedding & retrieval."""
    chunk_id: str
    doc_id: str
    title: str
    content: str
    category: str
    tags: List[str] = field(default_factory=list)
    jurisdiction: str = "Pakistan"
    effective_date: Optional[str] = None
    token_count: int = 0
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.content_hash and self.content:
            self.content_hash = compute_content_hash(self.content)
        if not self.token_count and self.content:
            self.token_count = estimate_token_count(self.content)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeChunk":
        return cls(**data)

