import csv
from pathlib import Path
from typing import Any, Dict, List


CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "ai_tooling_catalog.csv"


def _load_catalog() -> List[Dict[str, str]]:
    with CATALOG_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def search_knowledge(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Shared knowledge tool used by the API agent and the MCP server."""
    terms = {term.lower() for term in query.split() if term.strip()}
    ranked: List[tuple[int, Dict[str, str]]] = []
    for row in _load_catalog():
        searchable = " ".join(row.values()).lower()
        score = sum(term in searchable for term in terms)
        if score:
            ranked.append((score, row))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [{**row, "score": score} for score, row in ranked[: max(1, limit)]]


def list_knowledge_sources() -> List[Dict[str, str]]:
    return [{"name": "AI tooling catalog", "path": str(CATALOG_PATH), "format": "csv"}]


def get_source_record(title: str) -> Dict[str, str]:
    for row in _load_catalog():
        if row.get("title", "").lower() == title.lower():
            return row
    return {"error": f"No source record found for '{title}'."}
