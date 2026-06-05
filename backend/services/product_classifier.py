"""Product classification and essential-item matching.

Phase 2 will integrate real HuggingFace models:
  - facebook/bart-large-mnli for zero-shot category classification
  - sentence-transformers/all-MiniLM-L6-v2 for semantic essential-item matching

For Phase 0/1, this module provides deterministic stubs so the E2E flow works.
"""


def classify_product_category(product_name: str) -> str:
    """Stub: return a hardcoded category based on keyword matching.

    Phase 2: replace with bart-large-mnli zero-shot classifier.
    """
    name_lower = product_name.lower()

    categories = {
        "fashion": ["shirt", "dress", "jeans", "jacket", "shoe", "sneaker", "hat", "belt", "purse", "bag", "wallet", "watch", "jewelry", "necklace", "ring"],
        "electronics": ["phone", "tablet", "laptop", "charger", "cable", "headphone", "speaker", "mouse", "keyboard", "monitor", "tv", "camera", "drone"],
        "groceries": ["milk", "bread", "egg", "cheese", "vegetable", "fruit", "meat", "chicken", "rice", "pasta", "oil", "butter", "yogurt"],
        "health": ["vitamin", "supplement", "protein", "medicine", "mask", "sanitizer", "bandage", "first aid"],
        "books": ["book", "novel", "textbook", "kindle", "magazine"],
        "home_decor": ["lamp", "cushion", "curtain", "rug", "vase", "frame", "candle", "shelf"],
        "tools": ["hammer", "screwdriver", "drill", "wrench", "pliers", "saw", "tape", "glue"],
        "toys": ["toy", "game", "puzzle", "lego", "doll", "action figure", "board game"],
    }

    for category, keywords in categories.items():
        for kw in keywords:
            if kw in name_lower:
                return category

    return "other"


def compute_essential_similarity(
    product_name: str, essential_items: list[str]
) -> float:
    """Stub: compute cosine-similarity surrogate via keyword overlap.

    Phase 2: replace with all-MiniLM-L6-v2 embeddings + cosine similarity.
    """
    if not essential_items:
        return 0.0

    product_words = set(product_name.lower().split())
    best_overlap = 0.0

    for item in essential_items:
        item_words = set(item.lower().split())
        if not product_words or not item_words:
            continue
        intersection = product_words & item_words
        union = product_words | item_words
        jaccard = len(intersection) / len(union)
        best_overlap = max(best_overlap, jaccard)

    return best_overlap
