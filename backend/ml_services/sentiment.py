"""Twitter-RoBERTa sentiment analysis for emotional state detection.

Only loads model if already cached locally.
Returns neutral multiplier (1.0) if model unavailable.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None
_model_available = False

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"


def _model_is_cached() -> bool:
    """Check if the model is already in local HuggingFace cache."""
    home = Path.home()
    candidates = [
        home / ".cache" / "huggingface" / "hub",
        Path(os.environ.get("HF_HOME", "")),
        Path(os.environ.get("XDG_CACHE_HOME", "")) / "huggingface" / "hub",
    ]
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
    global _model, _tokenizer, _model_available
    if _model_available:
        return True

    if not _model_is_cached():
        logger.info(
            "Twitter-RoBERTa not cached locally. Using neutral sentiment. "
            "Run manually to cache: python -c \"from transformers import AutoModel; "
            "AutoModel.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment-latest')\""
        )
        _model_available = False
        return False

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        _model.eval()
        _model_available = True
        logger.info("Twitter-RoBERTa loaded from local cache")
    except Exception as e:
        logger.warning("Twitter-RoBERTa load failed (%s). Using neutral sentiment.", e)
        _model_available = False
    return _model_available


def analyze_sentiment(texts: list[str]) -> float:
    """Analyze sentiment of browsing session texts.

    Returns sentiment_multiplier: 1.0 = neutral, up to 1.3 = negative.
    """
    if not texts or not _load_model():
        return 1.0

    try:
        import torch

        full_text = " ".join(texts)[:512]
        inputs = _tokenizer(full_text, return_tensors="pt", truncation=True)
        outputs = _model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        neg_conf = probs[0, 0].item()
        pos_conf = probs[0, 2].item()

        if neg_conf > 0.5:
            multiplier = 1.0 + (neg_conf * 0.3)
        elif pos_conf > 0.7:
            multiplier = 1.0 - (pos_conf * 0.15)
        else:
            multiplier = 1.0

        multiplier = max(1.0, min(multiplier, 1.3))
        return multiplier
    except Exception as e:
        logger.warning("Sentiment analysis failed (%s). Using neutral.", e)
        return 1.0
