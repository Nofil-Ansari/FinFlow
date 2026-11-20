"""
Hybrid Semantic Retrieval & Re-ranking Layer for FinanceFlow RAG.
Includes:
- QueryProcessor: Normalizes Pakistani financial slang, currency figures (lakh, crore, k), and intent.
- LexicalMatcher: BM25/token-overlap scoring for exact keyword and entity hits.
- HybridRetriever: Merges dense vector results and lexical results via Reciprocal Rank Fusion (RRF).
- ReRanker: Cross-scores candidates with authority boosts and relevance threshold gating.
- RetrievalResult: Formatted output with citation labels.
"""

import re
import math
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set

from app.services.rag.models import KnowledgeChunk
from app.services.rag.embeddings import BaseEmbeddingService
from app.services.rag.vector_store import VectorStoreBase

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Represents a retrieved, scored, and re-ranked knowledge chunk with citation details."""
    chunk: KnowledgeChunk
    score: float
    vector_score: float
    lexical_score: float
    citation: str
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "title": self.chunk.title,
            "category": self.chunk.category,
            "score": round(self.score, 4),
            "vector_score": round(self.vector_score, 4),
            "lexical_score": round(self.lexical_score, 4),
            "citation": self.citation,
            "matched_terms": self.matched_terms,
            "content": self.chunk.content,
        }


class QueryProcessor:
    """Normalizes Pakistani financial terminology, currency units, and detects category intent."""

    CURRENCY_REPLACEMENTS = [
        (re.compile(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|lakhs)\b", re.IGNORECASE), lambda m: f"{int(float(m.group(1)) * 100000)} PKR"),
        (re.compile(r"(\d+(?:\.\d+)?)\s*(?:crore|crores)\b", re.IGNORECASE), lambda m: f"{int(float(m.group(1)) * 10000000)} PKR"),
        (re.compile(r"(\d+(?:\.\d+)?)\s*(?:k)\b", re.IGNORECASE), lambda m: f"{int(float(m.group(1)) * 1000)} PKR"),
    ]

    SLANG_SYNONYMS = {
        "bachat": "savings",
        "munafa": "profit interest return",
        "sood": "interest riba",
        "kamai": "income salary",
        "kharch": "expense spending",
        "kharcha": "expense spending",
        "filer": "active taxpayer filer",
        "non-filer": "inactive non-filer late filer",
        "zakat": "zakat deduction nisab",
        "behbood": "behbood savings certificate cdns",
        "ric": "regular income certificate cdns",
        "ssc": "special savings certificate cdns",
        "dsc": "defense savings certificate cdns",
    }

    CATEGORY_INTENT_KEYWORDS = {
        "tax_rates": ["tax", "fbr", "salary", "income tax", "slab", "withholding", "wht", "filer", "non-filer"],
        "banking": ["sbp", "state bank", "policy rate", "interest", "raast", "asaan", "dpc", "deposit protection"],
        "national_savings": ["national savings", "cdns", "behbood", "regular income", "special savings", "defense savings", "bahbood"],
        "zakat": ["zakat", "nisab", "cz-50", "cz50", "exemption", "deduction", "ramadan"],
        "substitutions": ["alternative", "substitute", "cheaper", "careem", "uber", "indrive", "bykea", "netflix", "spotify", "panadol"],
    }

    @classmethod
    def normalize_query(cls, query: str) -> str:
        """Converts currency shorthand and maps local Pakistani financial terms."""
        text = query.strip()
        for pattern, repl in cls.CURRENCY_REPLACEMENTS:
            text = pattern.sub(repl, text)

        words = text.split()
        normalized_words = []
        for w in words:
            clean_w = re.sub(r"[^\w\-]", "", w.lower())
            if clean_w in cls.SLANG_SYNONYMS:
                normalized_words.append(cls.SLANG_SYNONYMS[clean_w])
            else:
                normalized_words.append(w)

        return " ".join(normalized_words)

    @classmethod
    def detect_category_intent(cls, query: str) -> Optional[str]:
        """Detects high-confidence category intent from query keywords."""
        q_lower = query.lower()
        scores = {}
        for cat, keywords in cls.CATEGORY_INTENT_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in q_lower)
            if count > 0:
                scores[cat] = count

        if scores:
            best_cat = max(scores, key=scores.get)
            if scores[best_cat] >= 2 or (scores[best_cat] == 1 and len(scores) == 1):
                return best_cat
        return None


class LexicalMatcher:
    """In-memory inverted index scoring chunks with token overlap (BM25-style TF-IDF)."""

    def __init__(self, chunks: Optional[List[KnowledgeChunk]] = None):
        self.chunks: List[KnowledgeChunk] = []
        self.doc_freq: Dict[str, int] = {}
        self.chunk_tokens: List[List[str]] = []
        self.total_docs: int = 0
        if chunks:
            self.index_chunks(chunks)

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) > 1]

    def index_chunks(self, chunks: List[KnowledgeChunk]):
        self.chunks = list(chunks)
        self.total_docs = len(self.chunks)
        self.doc_freq = {}
        self.chunk_tokens = []

        for ch in self.chunks:
            full_text = f"{ch.title} {ch.content} {' '.join(ch.tags)}"
            tokens = self._tokenize(full_text)
            self.chunk_tokens.append(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

    def search(self, query: str, top_k: int = 15) -> List[Tuple[KnowledgeChunk, float, List[str]]]:
        if not self.chunks or self.total_docs == 0:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        q_token_set = set(q_tokens)
        scores: List[Tuple[int, float, List[str]]] = []

        for idx, tokens in enumerate(self.chunk_tokens):
            if not tokens:
                continue

            matched = [t for t in q_tokens if t in tokens]
            if not matched:
                continue

            # BM25-style IDF and TF weighting
            score = 0.0
            token_count = len(tokens)
            for t in set(matched):
                tf = tokens.count(t) / token_count
                df = self.doc_freq.get(t, 1)
                idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
                score += tf * idf

            # Exact phrase or title boost
            title_lower = self.chunks[idx].title.lower()
            if any(t in title_lower for t in q_tokens):
                score *= 1.5

            scores.append((idx, score, list(set(matched))))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score, matched in scores[:top_k]:
            results.append((self.chunks[idx], score, matched))

        return results


class ReRanker:
    """Applies cross-scoring heuristics:
    - Authority boost for official regulatory bodies (FBR, SBP, CDNS)
    - Query term coverage
    - Relevance threshold gating (drops irrelevant queries)
    """

    AUTHORITY_BOOSTS = {
        "Federal Board of Revenue (FBR)": 1.25,
        "State Bank of Pakistan (SBP)": 1.25,
        "Central Directorate of National Savings (CDNS)": 1.25,
        "Ministry of Poverty Alleviation & Social Safety": 1.20,
    }

    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold

    def _build_citation(self, chunk: KnowledgeChunk) -> str:
        authority = chunk.metadata.get("authority") or chunk.jurisdiction or "Pakistan Market"
        eff_date = chunk.effective_date or chunk.metadata.get("tax_year") or "2024-2025"
        return f"[Source: {chunk.title} | {authority} ({eff_date})]"

    def rerank(
        self,
        candidates: List[Tuple[KnowledgeChunk, float, float, List[str]]],
        query: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """candidates are (chunk, rrf_score, vector_score, matched_terms)."""
        if not candidates:
            return []

        q_lower = query.lower()
        reranked: List[RetrievalResult] = []

        for chunk, rrf_score, vec_score, matched in candidates:
            score = rrf_score

            # 1. Authority Boost
            authority = chunk.metadata.get("authority", "")
            for auth_name, boost in self.AUTHORITY_BOOSTS.items():
                if auth_name.lower() in authority.lower() or auth_name.lower() in chunk.content.lower():
                    score *= boost
                    break

            # 2. Exact Title Match Bonus
            title_words = set(chunk.title.lower().split())
            query_words = set(q_lower.split())
            overlap = len(title_words.intersection(query_words))
            if overlap > 0:
                score *= (1.0 + (overlap * 0.15))

            # 3. Dynamic Relevance Gating Check
            # Combined signal: score normalized against minimum semantic bar
            if score < self.threshold and vec_score < 0.25:
                continue

            citation = self._build_citation(chunk)
            reranked.append(RetrievalResult(
                chunk=chunk,
                score=score,
                vector_score=vec_score,
                lexical_score=rrf_score,
                citation=citation,
                matched_terms=matched
            ))

        reranked.sort(key=lambda r: r.score, reverse=True)
        return reranked[:top_k]


class HybridRetriever:
    """Orchestrates multi-channel retrieval:
    1. Query normalization
    2. Dense vector search
    3. Lexical inverted search
    4. Reciprocal Rank Fusion (RRF)
    5. Re-ranking and gating
    """

    def __init__(
        self,
        vector_store: VectorStoreBase,
        embedding_service: BaseEmbeddingService,
        chunks: Optional[List[KnowledgeChunk]] = None,
        rrf_k: int = 60,
        relevance_threshold: float = 0.35,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.lexical_matcher = LexicalMatcher(chunks)
        self.reranker = ReRanker(threshold=relevance_threshold)
        self.rrf_k = rrf_k

    def update_corpus(self, chunks: List[KnowledgeChunk]):
        self.lexical_matcher.index_chunks(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Executes full hybrid retrieval pipeline."""
        normalized_q = QueryProcessor.normalize_query(query)
        detected_category = category or QueryProcessor.detect_category_intent(normalized_q)

        # Stage 1A: Dense Vector Retrieval (Top 15)
        query_vec = self.embedding_service.embed_text(normalized_q)
        dense_results = self.vector_store.search(
            query_vector=query_vec,
            top_k=15,
            category=detected_category
        )

        # Stage 1B: Lexical Retrieval (Top 15)
        lexical_results = self.lexical_matcher.search(normalized_q, top_k=15)
        if detected_category:
            lexical_results = [r for r in lexical_results if r[0].category == detected_category]

        # Stage 2: Reciprocal Rank Fusion (RRF)
        # RRF_Score = 1 / (k + rank_dense) + 1 / (k + rank_lexical)
        chunk_map: Dict[str, KnowledgeChunk] = {}
        dense_ranks: Dict[str, Tuple[int, float]] = {}
        lexical_ranks: Dict[str, Tuple[int, List[str]]] = {}

        for rank, (chunk, vec_score) in enumerate(dense_results, 1):
            chunk_map[chunk.chunk_id] = chunk
            dense_ranks[chunk.chunk_id] = (rank, vec_score)

        for rank, (chunk, lex_score, matched) in enumerate(lexical_results, 1):
            chunk_map[chunk.chunk_id] = chunk
            lexical_ranks[chunk.chunk_id] = (rank, matched)

        candidates: List[Tuple[KnowledgeChunk, float, float, List[str]]] = []
        for chunk_id, chunk in chunk_map.items():
            rrf_score = 0.0
            vec_score = 0.0
            matched_terms = []

            if chunk_id in dense_ranks:
                d_rank, v_score = dense_ranks[chunk_id]
                rrf_score += 1.0 / (self.rrf_k + d_rank)
                vec_score = v_score

            if chunk_id in lexical_ranks:
                l_rank, matched = lexical_ranks[chunk_id]
                rrf_score += 1.0 / (self.rrf_k + l_rank)
                matched_terms = matched

            candidates.append((chunk, rrf_score, vec_score, matched_terms))

        # Stage 3: Re-ranking and Gating
        return self.reranker.rerank(candidates, query=normalized_q, top_k=top_k)

