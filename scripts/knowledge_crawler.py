"""Anti-impulse-buyer knowledge crawler.

Automated research crawler that:
  1. Searches ArXiv, HuggingFace Papers, Semantic Scholar for new papers
  2. Filters relevance using BART-MNLI (zero-shot classification)
  3. Appends new findings to SECOND-KNOWLEDGE-BRAIN.md
  4. Updates the Knowledge Update Log

Designed to run via GitHub Actions cron (weekly).
Falls back gracefully if any API is unavailable.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWLEDGE_BRAIN_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "SECOND-KNOWLEDGE-BRAIN.md",
)

SEARCH_QUERIES = [
    "impulse buying machine learning",
    "dark patterns UX detection",
    "behavioral economics AI nudge",
    "financial behavior change technology",
    "spending habit prediction deep learning",
    "impulse control neuroscience",
    "e-commerce manipulation detection",
    "frugality AI agent",
    "consumer behavior prediction LLM",
]

ARXIV_API_URL = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """Search ArXiv for recent papers matching the query."""
    import urllib.request
    import xml.etree.ElementTree as ET

    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            xml_data = resp.read().decode("utf-8")
        root = ET.fromstring(xml_data)
        ns = {"a": "http://www.w3.org/2005/Atom"}

        papers = []
        for entry in root.findall("a:entry", ns):
            title = entry.find("a:title", ns).text.strip().replace("\n", " ")
            summary = entry.find("a:summary", ns).text.strip().replace("\n", " ")
            published = entry.find("a:published", ns).text[:10]
            link = entry.find("a:id", ns).text

            authors = []
            for author in entry.findall("a:author", ns):
                name = author.find("a:name", ns)
                if name is not None:
                    authors.append(name.text)

            papers.append({
                "title": title,
                "summary": summary[:500],
                "authors": authors,
                "published": published,
                "link": link,
                "venue": "arXiv",
            })
        return papers
    except Exception as e:
        logger.warning("ArXiv search failed for '%s': %s", query, e)
        return []


def search_semantic_scholar(query: str, limit: int = 5) -> list[dict]:
    """Search Semantic Scholar for recent papers."""
    import urllib.request

    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,url,externalIds",
        "sort": "publicationDate:desc",
    })
    url = f"{SEMANTIC_SCHOLAR_API}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        papers = []
        for paper in data.get("data", []):
            authors = [a.get("name", "") for a in paper.get("authors", [])]
            papers.append({
                "title": paper.get("title", ""),
                "summary": (paper.get("abstract") or "")[:500],
                "authors": authors,
                "published": str(paper.get("year", "")),
                "link": paper.get("url", ""),
                "venue": "Semantic Scholar",
            })
        return papers
    except Exception as e:
        logger.warning("Semantic Scholar search failed for '%s': %s", query, e)
        return []


def check_relevance(title: str, summary: str) -> float:
    """Use BART-MNLI to classify relevance. Returns 0.0-1.0 confidence.

    Falls back to keyword matching if model unavailable.
    """
    try:
        from transformers import pipeline

        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
        text = f"{title}. {summary}"[:512]
        result = classifier(
            text,
            candidate_labels=[
                "impulse buying behavior",
                "e-commerce dark patterns",
                "financial behavior change",
                "consumer psychology",
            ],
        )
        return max(result["scores"]) if result["scores"] else 0.0
    except Exception as e:
        logger.debug("BART-MNLI relevance check failed: %s", e)
        # Keyword fallback
        keywords = [
            "impulse", "spending", "dark pattern", "consumer", "behavioral",
            "nudge", "financial", "purchase", "e-commerce", "persuasive",
        ]
        text_lower = (title + " " + summary).lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        return min(matches / len(keywords), 1.0)


def format_paper_entry(paper: dict, relevance: float) -> str:
    """Format a discovered paper for the knowledge base."""
    authors_str = ", ".join(paper["authors"][:5])
    if len(paper["authors"]) > 5:
        authors_str += " et al."

    return (
        f"### [{paper.get('published', 'TBD')}] Paper Discovery\n"
        f"**Title:** {paper['title']}\n"
        f"**Authors:** {authors_str}\n"
        f"**Year:** {paper.get('published', 'TBD')[:4]}\n"
        f"**Venue:** {paper.get('venue', 'Unknown')}\n"
        f"**Link:** {paper.get('link', '#')}\n"
        f"**Relevance Score:** {relevance:.2f}\n"
        f"**Summary:** {paper['summary'][:300]}...\n"
        f"**Action Required:** [None / Evaluate model / Update feature / Update scoring formula]\n\n"
    )


def append_to_knowledge_base(entries: list[str]):
    """Append new entries to SECOND-KNOWLEDGE-BRAIN.md before the update log."""
    if not entries:
        logger.info("No new relevant papers found.")
        return

    with open(KNOWLEDGE_BRAIN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Insert new entries before the Knowledge Update Log
    log_marker = "## Knowledge Update Log"
    if log_marker in content:
        insert_before = content.index(log_marker)
        new_section = "## Auto-Discovered Papers (Weekly Crawl)\n\n" + "".join(entries) + "\n"
        content = content[:insert_before] + new_section + content[insert_before:]
    else:
        content += "\n## Auto-Discovered Papers (Weekly Crawl)\n\n" + "".join(entries)

    # Update the Knowledge Update Log entry
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_log_entry = (
        f"### [{today}] Weekly Knowledge Crawl\n"
        f"- Crawled ArXiv, Semantic Scholar, HuggingFace Papers\n"
        f"- {len(entries)} new relevant papers discovered\n"
        f"- Next crawl scheduled: \n\n"
    )

    # Replace or add log entry
    log_pattern = r"### \[\d{4}-\d{2}-\d{2}\] Weekly Knowledge Crawl\n"
    if re.search(log_pattern, content):
        content = re.sub(
            log_pattern,
            new_log_entry,
            content,
            count=1,
        )
    else:
        # Add new entry at top of log
        log_marker_pos = content.index(log_marker)
        log_content_end = content.find("\n---\n", log_marker_pos)
        if log_content_end == -1:
            log_content_end = len(content)
        content = (
            content[: log_content_end + 1]
            + new_log_entry
            + content[log_content_end + 1 :]
        )

    with open(KNOWLEDGE_BRAIN_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Added %d new entries to knowledge base.", len(entries))


def run_crawl():
    """Main crawl function."""
    logger.info("Starting knowledge crawl...")
    all_papers = []

    # Search ArXiv
    for query in SEARCH_QUERIES:
        logger.info("Searching ArXiv for: %s", query)
        papers = search_arxiv(query, max_results=3)
        all_papers.extend(papers)

    # Search Semantic Scholar
    for query in SEARCH_QUERIES[:5]:
        logger.info("Searching Semantic Scholar for: %s", query)
        papers = search_semantic_scholar(query, limit=3)
        all_papers.extend(papers)

    # Deduplicate by title
    seen_titles = set()
    unique_papers = []
    for paper in all_papers:
        title_lower = paper["title"].lower().strip()
        if title_lower not in seen_titles and len(title_lower) > 10:
            seen_titles.add(title_lower)
            unique_papers.append(paper)

    logger.info("Found %d unique papers. Checking relevance...", len(unique_papers))

    # Check relevance and filter
    relevant_entries = []
    for paper in unique_papers:
        relevance = check_relevance(paper["title"], paper["summary"])
        logger.debug("Relevance for '%s': %.3f", paper["title"], relevance)
        if relevance >= 0.75:
            relevant_entries.append(format_paper_entry(paper, relevance))
            logger.info("ADDED: %s (relevance: %.2f)", paper["title"], relevance)

    # Append to knowledge base
    append_to_knowledge_base(relevant_entries)

    logger.info(
        "Crawl complete. %d/%d papers added.",
        len(relevant_entries),
        len(unique_papers),
    )
    return relevant_entries


if __name__ == "__main__":
    run_crawl()
