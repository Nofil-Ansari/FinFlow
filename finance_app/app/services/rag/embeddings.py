"""
Embedding service layer with two-tier Redis + Disk caching and pluggable providers.
Supports Google Gemini gemini-embedding-001 (768-dim) and zero-dependency local TF-IDF (768-dim).
"""

import os
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import requests

logger = logging.getLogger(__name__)

# Optional redis client
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class EmbeddingResult(list):
    """List subclass holding embedding vector values and a fallback status indicator."""

    def __init__(self, values: List[float], is_fallback: bool = False):
        super().__init__(values)
        self.is_fallback = is_fallback


class BaseEmbeddingService:
    """Base interface for embedding services."""

    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class LocalTfidfEmbedding(BaseEmbeddingService):
    """Local, zero-external-dependency embedding generator based on TF-IDF word frequency.
    Generates deterministic, normalized 768-dimensional vectors using MD5 hash projection.
    Ensures the RAG system operates seamlessly offline without API keys or external services.
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def _tokenize(self, text: str) -> List[str]:
        cleaned = "".join([c.lower() if c.isalnum() else " " for c in text])
        return [w for w in cleaned.split() if len(w) > 2]

    def embed_text(self, text: str) -> List[float]:
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.dimension

        vec = np.zeros(self.dimension, dtype=np.float32)
        for token in tokens:
            # Deterministic hash trick to map tokens into fixed-dimension space
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h // self.dimension) % 2 == 0 else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


class GeminiEmbeddingService(BaseEmbeddingService):
    """Google Gemini gemini-embedding-001 REST embedding provider producing 768-dim vectors.
    Falls back gracefully to LocalTfidfEmbedding if GEMINI_API_KEY is not configured or on network error.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-embedding-001",
        fallback_service: Optional[BaseEmbeddingService] = None,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.fallback = fallback_service or LocalTfidfEmbedding(dimension=768)
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent"

    def embed_text(self, text: str) -> List[float]:
        if not self.api_key:
            return EmbeddingResult(self.fallback.embed_text(text), is_fallback=True)

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": 768,
        }

        try:
            resp = requests.post(
                self.endpoint, headers=headers, json=payload, timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                values = data.get("embedding", {}).get("values", [])
                if len(values) == 768:
                    return EmbeddingResult(values, is_fallback=False)
            logger.warning(
                f"Gemini API returned status {resp.status_code}. Using local TF-IDF fallback."
            )
            return EmbeddingResult(self.fallback.embed_text(text), is_fallback=True)
        except Exception as e:
            err_msg = str(e)
            if self.api_key:
                err_msg = err_msg.replace(self.api_key, "[REDACTED]")
            err_msg = re.sub(r"key=[^\s&'\"]+", "key=[REDACTED]", err_msg)
            logger.warning(
                f"Gemini API call failed ({type(e).__name__}): {err_msg}. Using local TF-IDF fallback."
            )
            return EmbeddingResult(self.fallback.embed_text(text), is_fallback=True)


class DiskCache:
    """L2 Persistent Disk Cache keyed by content SHA256."""

    def __init__(self, cache_dir: str = "data/knowledge/processed/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "embeddings_cache.json"
        self._cache: Dict[str, List[float]] = self._load()

    def _load(self) -> Dict[str, List[float]]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except Exception as e:
            logger.error(f"Failed to write disk cache: {e}")

    def get(self, key: str) -> Optional[List[float]]:
        return self._cache.get(key)

    def set(self, key: str, value: List[float]):
        self._cache[key] = value
        self.save()

    def get_all(self) -> Dict[str, List[float]]:
        return self._cache


class TwoTierCachedEmbeddingService(BaseEmbeddingService):
    """Two-Tier Caching Embedding Service:
    - Tier 1: In-Memory / Distributed Redis (Key: 'rag:chunk:embedding:<sha256>')
    - Tier 2: Persistent Disk Cache ('data/knowledge/processed/cache/embeddings_cache.json')

    If Redis is down or unconfigured, it gracefully falls back to Tier 2 (Disk).
    If neither has the embedding, it invokes inner_service and populates both tiers.
    """

    def __init__(
        self,
        inner_service: BaseEmbeddingService,
        redis_url: Optional[str] = None,
        cache_dir: str = "data/knowledge/processed/cache",
    ):
        self.inner_service = inner_service
        self.disk_cache = DiskCache(cache_dir=cache_dir)
        self.redis_client = None

        target_redis_url = redis_url or os.environ.get("REDIS_URL")
        if target_redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis.from_url(
                    target_redis_url, decode_responses=True, socket_connect_timeout=2
                )
                self.redis_client.ping()
            except Exception as e:
                logger.warning(
                    f"Redis connection failed ({e}). Running with Tier 2 Disk Cache only."
                )
                self.redis_client = None

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def _redis_key(self, content_hash: str) -> str:
        return f"rag:chunk:embedding:{content_hash}"

    def embed_text(self, text: str) -> List[float]:
        content_hash = self._hash_text(text)
        r_key = self._redis_key(content_hash)

        # Tier 1: Redis Check
        if self.redis_client:
            try:
                cached_str = self.redis_client.get(r_key)
                if cached_str:
                    return EmbeddingResult(json.loads(cached_str), is_fallback=False)
            except Exception as e:
                logger.debug(f"Redis read error: {e}")

        # Tier 2: Disk Cache Check
        cached_disk = self.disk_cache.get(content_hash)
        if cached_disk:
            # Back-populate Redis Tier 1 if available
            if self.redis_client:
                try:
                    self.redis_client.set(r_key, json.dumps(cached_disk))
                except Exception:
                    pass
            return EmbeddingResult(cached_disk, is_fallback=False)

        # Cache Miss: Compute embedding
        res = self.inner_service.embed_text(text)
        is_fallback = getattr(res, "is_fallback", False)

        if not is_fallback:
            # Populate Tier 2 (Disk)
            self.disk_cache.set(content_hash, list(res))

            # Populate Tier 1 (Redis)
            if self.redis_client:
                try:
                    self.redis_client.set(r_key, json.dumps(list(res)))
                except Exception as e:
                    logger.debug(f"Redis write error: {e}")

        return EmbeddingResult(res, is_fallback=is_fallback)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        results: List[List[float]] = []
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        for idx, text in enumerate(texts):
            h = self._hash_text(text)
            r_key = self._redis_key(h)
            found = None

            # L1 Redis
            if self.redis_client:
                try:
                    cached_str = self.redis_client.get(r_key)
                    if cached_str:
                        found = json.loads(cached_str)
                except Exception:
                    pass

            # L2 Disk
            if found is None:
                found = self.disk_cache.get(h)
                if found is not None and self.redis_client:
                    try:
                        self.redis_client.set(r_key, json.dumps(found))
                    except Exception:
                        pass

            if found is not None:
                results.append(EmbeddingResult(found, is_fallback=False))
            else:
                results.append([])
                missing_indices.append(idx)
                missing_texts.append(text)

        if missing_texts:
            new_vectors = self.inner_service.embed_batch(missing_texts)
            for orig_idx, text, vec in zip(missing_indices, missing_texts, new_vectors):
                h = self._hash_text(text)
                r_key = self._redis_key(h)
                is_fb = getattr(vec, "is_fallback", False)
                results[orig_idx] = EmbeddingResult(vec, is_fallback=is_fb)
                if not is_fb:
                    self.disk_cache.set(h, list(vec))
                    if self.redis_client:
                        try:
                            self.redis_client.set(r_key, json.dumps(list(vec)))
                        except Exception:
                            pass

        return results

    def warm_redis_from_disk(self) -> int:
        """Pushes all embeddings currently in Disk Cache into Redis L1."""
        if not self.redis_client:
            return 0
        all_entries = self.disk_cache.get_all()
        count = 0
        for h, vec in all_entries.items():
            try:
                self.redis_client.set(self._redis_key(h), json.dumps(vec))
                count += 1
            except Exception:
                break
        return count
