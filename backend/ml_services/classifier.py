"""BART-MNLI zero-shot product classifier with graceful fallback.

Only loads model if already cached locally.
Never attempts long downloads — falls back to keyword classifier immediately.
"""

import logging
import os
from pathlib import Path

from backend.services.product_classifier import classify_product_category as _fallback_classify

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None
_model_available = False

CANDIDATE_LABELS = [
    "fashion", "electronics", "groceries", "health", "books",
    "home_decor", "tools", "toys", "fitness", "accessories",
    "food", "pet_supplies", "baby_products", "auto_parts", "office_supplies",
]

MODEL_NAME = "facebook/bart-large-mnli"


def _model_is_cached() -> bool:
    """Check if the HuggingFace model is already in local cache."""
    # Check common HuggingFace cache locations
    home = Path.home()
    candidates = [
        home / ".cache" / "huggingface" / "hub",
        Path(os.environ.get("HF_HOME", "")),
        Path(os.environ.get("XDG_CACHE_HOME", "")) / "huggingface" / "hub",
    ]
    for cache_dir in candidates:
        if not cache_dir.exists():
            continue
        # Look for the model's snapshot folder
        model_slug = MODEL_NAME.replace("/", "--")
        if list(cache_dir.rglob(f"*{model_slug}*")):
            return True
        # Check for models--{slug} pattern
        if list(cache_dir.rglob(f"models--{model_slug}*")):
            return True
    return False


def _load_model():
    """Lazy-load BART-MNLI only if already cached locally."""
    global _model, _tokenizer, _model_available
    if _model_available:
        return True

    if not _model_is_cached():
        logger.info(
            "BART-MNLI not cached locally. Using keyword fallback. "
            "Run manually once to cache: python -c \"from transformers import AutoModel; "
            "AutoModel.from_pretrained('facebook/bart-large-mnli')\""
        )
        _model_available = False
        return False

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        _model.eval()
        _model_available = True
        logger.info("BART-MNLI loaded from local cache")
    except Exception as e:
        logger.warning("BART-MNLI load failed (%s). Using keyword fallback.", e)
        _model_available = False
    return _model_available


def classify_product(product_name: str) -> str:
    """Classify product into a category using BART-MNLI zero-shot."""
    if not _load_model():
        return _fallback_classify(product_name)

    try:
        hypothesis_template = "This product is for {}."
        scores = []
        for label in CANDIDATE_LABELS:
            hypothesis = hypothesis_template.format(label)
            inputs = _tokenizer(
                product_name, hypothesis, return_tensors="pt", truncation=True
            )
            outputs = _model(**inputs)
            entailment_logits = outputs.logits[:, 0].item()
            scores.append(entailment_logits)

        best_idx = scores.index(max(scores))
        best_label = CANDIDATE_LABELS[best_idx]
        logger.debug("BART-MNLI: %s -> %s (%.3f)", product_name, best_label, max(scores))
        return best_label
    except Exception as e:
        logger.warning("BART-MNLI inference failed (%s). Using fallback.", e)
        return _fallback_classify(product_name)
