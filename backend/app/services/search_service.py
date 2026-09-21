import logging
import csv
from pathlib import Path
from typing import Any, Dict, List

from app.config.settings import settings
from app.models.chat_models import SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    local_documents: List[Dict[str, Any]] = []

    def __init__(self) -> None:
        self.url = settings.elasticsearch_url
        self.index_name = settings.elasticsearch_index
        self.api_key = settings.elasticsearch_api_key
        self._client = None
        
        try:
            import importlib

            elasticsearch_module = importlib.import_module("elasticsearch")
            elasticsearch_class = getattr(elasticsearch_module, "Elasticsearch")
            
            connection_params = {
                "hosts": [self.url],
                "verify_certs": False, 
                "ssl_show_warn": False, 
                "request_timeout": 2,
                "max_retries": 0,
            }
            
            if self.api_key:
                connection_params["api_key"] = self.api_key
            elif settings.elasticsearch_user and settings.elasticsearch_password:
                connection_params["basic_auth"] = (
                    settings.elasticsearch_user,
                    settings.elasticsearch_password
                )
            
            
            self._client = elasticsearch_class(**connection_params)
            
            
            info = self._client.info()
            logger.info(
                "Elasticsearch client initialized.",
                extra={
                    "index_name": self.index_name,
                    "url": self.url,
                    "version": info.get("version", {}).get("number", "unknown")
                },
            )
            
        except Exception as exc:
            logger.warning(
                "Elasticsearch client unavailable during startup.",
                extra={"index_name": self.index_name, "url": self.url, "reason": str(exc)},
            )
            self._client = None

        if not SearchService.local_documents:
            catalog_path = Path(__file__).resolve().parents[2] / "data" / "ai_tooling_catalog.csv"
            try:
                with catalog_path.open(newline="", encoding="utf-8") as catalog_file:
                    SearchService.local_documents = list(csv.DictReader(catalog_file))
            except OSError:
                SearchService.local_documents = []
            
    def ensure_index(self) -> None:
        if not self._client:
            return
        if not self._client.indices.exists(index=self.index_name):
            logger.info("Creating Elasticsearch index.", extra={"index_name": self.index_name})
            self._client.indices.create(
                index=self.index_name,
                mappings={
                    "properties": {
                        "title": {"type": "text"},
                        "snippet": {"type": "text"},
                        "category": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "page_number": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "file_name": {"type": "keyword"},
                    }
                },
            )

    def _search_local(self, query: str) -> List[SearchResult]:
        terms = {term.lower() for term in query.split() if term.strip()}
        ranked = []
        for document in SearchService.local_documents:
            searchable = " ".join(str(value) for value in document.values()).lower()
            score = sum(term in searchable for term in terms)
            if score:
                ranked.append((score, document))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            SearchResult(
                title=str(document.get("title", "Untitled")),
                snippet=str(document.get("snippet", "")),
                score=float(score),
                source=str(document.get("source", "local catalog")),
                page_number=(int(document["page_number"]) if document.get("page_number") else None),
                file_name=document.get("file_name"),
            )
            for score, document in ranked[:5]
        ]
            
    def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> int:
        if not self._client:
            SearchService.local_documents.extend(documents)
            return len(documents)
        logger.info(
            "Bulk index started.",
            extra={"index_name": self.index_name, "document_count": len(documents)},
        )
        self.ensure_index()
        operations: List[Dict[str, Any]] = []
        for document in documents:
            operations.append({"index": {"_index": self.index_name}})
            operations.append(document)
        response = self._client.bulk(operations=operations, refresh=True)
        if response.get("errors"):
            logger.error("Bulk indexing completed with errors.", extra={"index_name": self.index_name})
            raise RuntimeError("Bulk indexing completed with errors.")
        logger.info(
            "Bulk index completed.",
            extra={"index_name": self.index_name, "document_count": len(documents)},
        )
        return len(documents)
    
    
    async def search(self, query: str) -> List[SearchResult]:
        if not self._client:
            return self._search_local(query)
        logger.info(
            "Elasticsearch query started.",
            extra={"index_name": self.index_name, "query_preview": query[:120]},
        )
        try:
            response = self._client.search(
                index=self.index_name,
                query={
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "snippet", "category"],
                    }
                },
                size=5,
            )
            hits = response.get("hits", {}).get("hits", [])
            logger.info(
                "Elasticsearch query completed.",
                extra={"index_name": self.index_name, "hits_count": len(hits)},
            )
            return [
                SearchResult(
                    title=hit.get("_source", {}).get("title", "Untitled"),
                    snippet=hit.get("_source", {}).get("snippet", ""),
                    score=float(hit.get("_score", 0.0)),
                    source=hit.get("_source", {}).get("source", "elasticsearch"),
                    page_number=hit.get("_source", {}).get("page_number"),
                    file_name=hit.get("_source", {}).get("file_name"),
                )
                for hit in hits
            ]
        except Exception as exc:
            logger.exception(
                "Elasticsearch query failed.",
                extra={"index_name": self.index_name, "query_preview": query[:120]},
            )
            logger.warning("Using local catalog fallback after Elasticsearch query failure.")
            return self._search_local(query)
        
    
    @property
    def available(self) -> bool:
     return self._client is not None