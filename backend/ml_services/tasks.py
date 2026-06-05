"""Async ML inference via Celery/Redis — fully lazy initialization.

Every function tries Celery first with a short timeout, then falls back
to synchronous execution if Celery/Redis is unavailable.
"""

import logging
import socket

logger = logging.getLogger(__name__)


def _redis_available(host="localhost", port=6379, timeout=1.0) -> bool:
    """Quick check if Redis is reachable before attempting Celery."""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def classify_product_async(product_name: str) -> str:
    """Run classification. Tries Celery first, then sync fallback."""
    from backend.ml_services.classifier import classify_product

    if _redis_available():
        try:
            from celery import Celery

            app = Celery("aib_tasks", broker="redis://localhost:6379/0")
            app.conf.update(task_serializer="json", accept_content=["json"])
            task = app.send_task("classify_product", args=[product_name])
            return task.get(timeout=10)
        except Exception as e:
            logger.debug("Async classify unavailable (%s). Running sync.", e)
    return classify_product(product_name)


def compute_similarity_async(
    product_name: str, essential_items: list[str]
) -> float:
    """Run similarity. Tries Celery first, then sync fallback."""
    if not essential_items:
        return 0.0

    if _redis_available():
        try:
            from celery import Celery

            app = Celery("aib_tasks", broker="redis://localhost:6379/0")
            task = app.send_task(
                "compute_similarity", args=[product_name, essential_items]
            )
            return task.get(timeout=10)
        except Exception as e:
            logger.debug("Async similarity unavailable (%s). Running sync.", e)

    from backend.ml_services.embeddings import compute_similarity
    return compute_similarity(product_name, essential_items)


def analyze_sentiment_async(texts: list[str]) -> float:
    """Run sentiment. Tries Celery first, then sync fallback."""
    if not texts:
        return 1.0

    if _redis_available():
        try:
            from celery import Celery

            app = Celery("aib_tasks", broker="redis://localhost:6379/0")
            task = app.send_task("analyze_sentiment", args=[texts])
            return task.get(timeout=10)
        except Exception as e:
            logger.debug("Async sentiment unavailable (%s). Running sync.", e)

    from backend.ml_services.sentiment import analyze_sentiment
    return analyze_sentiment(texts)


def get_browsing_session_texts(page_title: str | None = None) -> list[str]:
    """Collect recent page titles as a proxy for mood/context."""
    texts = []
    if page_title:
        texts.append(page_title)
    return texts
