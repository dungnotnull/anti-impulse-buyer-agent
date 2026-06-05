"""all-MiniLM-L6-v2 semantic similarity for essential-items matching.

Only loads model if already cached locally.
Falls back to Jaccard keyword overlap if model unavailable.
"""

import logging
import os
from pathlib import Path

import numpy as np

from backend.services.product_classifier import compute_essential_similarity as _fallback_similarity

logger = logging.getLogger(__name__)

_model = None
_model_available = False
_essentials_cache = {}

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _model_is_cached() -> bool:
    """Check if the sentence-transformers model is in local cache."""
    home = Path.home()
    candidates = [
        home / ".cache" / "huggingface" / "hub",
        Path(os.environ.get("HF_HOME", "")),
        Path(os.environ.get("XDG_CACHE_HOME", "")) / "huggingface" / "hub",
    ]
    # Also check sentence-transformers specific cache
    st_cache = home / ".cache" / "torch" / "sentence_transformers"
    if st_cache.exists():
        candidates.append(st_cache)

    for cache_dir in candidates:
        if not cache_dir.exists():
            continue
        model_slug = MODEL_NAME.replace("/", "--")
        if list(cache_dir.rglob(f"*{model_slug}*")):
            return True
        if list(cache_dir.rglob(f"models--{model_slug}*")):
            return True
    return False


def _load_model():
    global _model, _model_available
    if _model_available:
        return True

    if not _model_is_cached():
        logger.info(
            "all-MiniLM-L6-v2 not cached locally. Using keyword fallback. "
            "Run manually to cache: python -c \"from sentence_transformers import "
            "SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')\""
        )
        _model_available = False
        return False

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
        _model_available = True
        logger.info("all-MiniLM-L6-v2 loaded from local cache")
    except Exception as e:
        logger.warning("all-MiniLM-L6-v2 load failed (%s). Using keyword fallback.", e)
        _model_available = False
    return _model_available


def _encode(text: str) -> np.ndarray:
    if not _model:
        return np.array([])
    return _model.encode(text, normalize_embeddings=True)


def compute_similarity(product_name: str, essential_items: list[str]) -> float:
    """Cosine similarity between product and best-matching essential item."""
    if not essential_items:
        return 0.0

    if not _load_model():
        return _fallback_similarity(product_name, essential_items)

    try:
        product_vec = _encode(product_name)
        best_score = 0.0

        for item in essential_items:
            if item not in _essentials_cache:
                _essentials_cache[item] = _encode(item)
            item_vec = _essentials_cache[item]
            if product_vec.size and item_vec.size:
                cos_sim = float(np.dot(product_vec, item_vec))
                best_score = max(best_score, cos_sim)

        logger.debug("MiniLM similarity: %s vs essentials -> %.4f", product_name, best_score)
        return best_score
    except Exception as e:
        logger.warning("MiniLM inference failed (%s). Using fallback.", e)
        return _fallback_similarity(product_name, essential_items)
