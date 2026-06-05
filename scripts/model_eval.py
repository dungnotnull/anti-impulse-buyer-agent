"""Model evaluation pipeline for SECOND-KNOWLEDGE-BRAIN auto-update.

When a new HuggingFace model is discovered by the knowledge crawler,
this pipeline benchmarks it against the current best model on the
product classification test set.

If the new model scores >3% higher, it's flagged for manual review.
"""

import json
import logging
import os
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Built-in test set of 30 products with expected categories
TEST_SET: list[dict[str, Any]] = [
    {"name": "Nike Air Max Sneakers", "expected": "fashion"},
    {"name": "iPhone 15 Pro Case", "expected": "electronics"},
    {"name": "Whole Milk 1 Gallon", "expected": "groceries"},
    {"name": "Vitamin D3 2000 IU", "expected": "health"},
    {"name": "The Great Gatsby Hardcover", "expected": "books"},
    {"name": "LED Desk Lamp", "expected": "home_decor"},
    {"name": "Stanley Hammer 16oz", "expected": "tools"},
    {"name": "LEGO Star Wars Set", "expected": "toys"},
    {"name": "Whey Protein Isolate Powder", "expected": "fitness"},
    {"name": "Silver Chain Necklace", "expected": "accessories"},
    {"name": "Organic Bananas 1lb", "expected": "groceries"},
    {"name": "Wireless Bluetooth Earbuds", "expected": "electronics"},
    {"name": "Cotton T-Shirt Pack", "expected": "fashion"},
    {"name": "Dog Food Dry Kibble", "expected": "pet_supplies"},
    {"name": "Diapers Size 4 Mega Pack", "expected": "baby_products"},
    {"name": "Office Chair Ergonomic", "expected": "office_supplies"},
    {"name": "Motor Oil 5W-30", "expected": "auto_parts"},
    {"name": "Dark Chocolate Bar", "expected": "food"},
    {"name": "Yoga Mat Premium", "expected": "fitness"},
    {"name": "Wall Mirror 24x36", "expected": "home_decor"},
    {"name": "USB-C Charging Cable 6ft", "expected": "electronics"},
    {"name": "Winter Jacket Down Fill", "expected": "fashion"},
    {"name": "Rice Cooker 5-Cup", "expected": "groceries"},
    {"name": "Board Game Catan", "expected": "toys"},
    {"name": "Blood Pressure Monitor", "expected": "health"},
    {"name": "Fiction Novel Bestseller", "expected": "books"},
    {"name": "Cordless Drill 20V", "expected": "tools"},
    {"name": "Cat Litter Unscented", "expected": "pet_supplies"},
    {"name": "Baby Stroller Lightweight", "expected": "baby_products"},
    {"name": "Running Shorts Men", "expected": "fashion"},
]


def evaluate_model(model_id: str, model_type: str = "zero-shot") -> dict[str, Any]:
    """Evaluate a HuggingFace model on the product classification test set.

    Args:
        model_id: HuggingFace model ID (e.g. "facebook/bart-large-mnli")
        model_type: "zero-shot" for zero-shot classifier, "embedding" for sentence embedding

    Returns:
        dict with accuracy, per-category breakdown, and confusion info
    """
    correct = 0
    total = len(TEST_SET)
    category_results: dict[str, dict] = {}

    try:
        if model_type == "zero-shot":
            from transformers import pipeline

            classifier = pipeline(
                "zero-shot-classification",
                model=model_id,
            )
            candidate_labels = sorted(set(item["expected"] for item in TEST_SET))

            for item in TEST_SET:
                result = classifier(
                    item["name"],
                    candidate_labels=candidate_labels,
                )
                predicted = result["labels"][0]
                expected = item["expected"]

                is_correct = predicted == expected
                if is_correct:
                    correct += 1

                cat = expected
                if cat not in category_results:
                    category_results[cat] = {"correct": 0, "total": 0}
                category_results[cat]["total"] += 1
                if is_correct:
                    category_results[cat]["correct"] += 1

        elif model_type == "embedding":
            from sentence_transformers import SentenceTransformer
            import numpy as np

            model = SentenceTransformer(model_id)
            candidate_labels = sorted(set(item["expected"] for item in TEST_SET))
            label_embeddings = {
                label: model.encode(label, normalize_embeddings=True)
                for label in candidate_labels
            }

            for item in TEST_SET:
                product_vec = model.encode(item["name"], normalize_embeddings=True)
                scores = {
                    label: float(np.dot(product_vec, label_vec))
                    for label, label_vec in label_embeddings.items()
                }
                predicted = max(scores, key=scores.get)
                expected = item["expected"]

                is_correct = predicted == expected
                if is_correct:
                    correct += 1

                cat = expected
                if cat not in category_results:
                    category_results[cat] = {"correct": 0, "total": 0}
                category_results[cat]["total"] += 1
                if is_correct:
                    category_results[cat]["correct"] += 1

        else:
            return {"error": f"Unknown model type: {model_type}"}

    except Exception as e:
        logger.error("Evaluation failed for %s: %s", model_id, e)
        return {"error": str(e), "model_id": model_id, "model_type": model_type}

    accuracy = correct / total if total > 0 else 0
    per_category = {
        cat: {
            "accuracy": res["correct"] / res["total"] if res["total"] > 0 else 0,
            "correct": res["correct"],
            "total": res["total"],
        }
        for cat, res in sorted(category_results.items())
    }

    return {
        "model_id": model_id,
        "model_type": model_type,
        "accuracy": round(accuracy, 4),
        "correct": correct,
        "total": total,
        "per_category": per_category,
    }


def compare_models(
    current_model_id: str,
    new_model_id: str,
    model_type: str = "zero-shot",
) -> dict[str, Any]:
    """Compare two models and flag if new one is >3% better."""
    logger.info("Evaluating current model: %s", current_model_id)
    current = evaluate_model(current_model_id, model_type)
    logger.info("Current accuracy: %.2f%%", current.get("accuracy", 0) * 100)

    logger.info("Evaluating new model: %s", new_model_id)
    new = evaluate_model(new_model_id, model_type)
    logger.info("New accuracy: %.2f%%", new.get("accuracy", 0) * 100)

    if "error" in current or "error" in new:
        return {
            "can_swap": False,
            "reason": "One or both models failed evaluation",
            "current": current,
            "new": new,
        }

    diff = new["accuracy"] - current["accuracy"]
    can_swap = diff > 0.03

    return {
        "can_swap": can_swap,
        "reason": (
            f"New model {'IS' if can_swap else 'is NOT'} >3% better. "
            f"Difference: {diff*100:.2f}%"
        ),
        "accuracy_gain": round(diff * 100, 2),
        "current": current,
        "new": new,
    }


def run_benchmark():
    """Run a benchmark on the default models and print results."""
    logger.info("Running model benchmark pipeline...")

    # Test current zero-shot model
    result = evaluate_model("facebook/bart-large-mnli", "zero-shot")
    logger.info(
        "BART-Large-MNLI accuracy: %.2f%% (%d/%d)",
        result["accuracy"] * 100,
        result["correct"],
        result["total"],
    )

    # Test current embedding model
    result2 = evaluate_model(
        "sentence-transformers/all-MiniLM-L6-v2", "embedding"
    )
    logger.info(
        "all-MiniLM-L6-v2 accuracy: %.2f%% (%d/%d)",
        result2["accuracy"] * 100,
        result2["correct"],
        result2["total"],
    )

    return {
        "bart_mnli": result,
        "minilm": result2,
    }


if __name__ == "__main__":
    run_benchmark()
