import logging
import re

from app.config.settings import settings
from app.models.chat_models import AgentResult, SearchResult
from app.services.search_service import SearchService
from app.services.mcp_tools import search_knowledge
from app.state import GraphState

if settings.langfuse_enabled:
    try:
        from langfuse import observe
    except ImportError:
        def observe(*args,**kwargs):
            def decorator(func):
                return func
            return decorator if args and callable(args[0]) else decorator
else:
     def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    
logger  = logging.getLogger(__name__)


def _daily_total_from_document(question: str, snippet: str) -> str | None:
    weekdays = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    question_lower = question.lower()
    weekday = next((day for day in weekdays if day in question_lower), None)
    if not weekday or "total" not in question_lower or "sales" not in question_lower:
        return None

    totals_match = re.search(
        r"DAILY TOTALS\s+((?:\$[\d,]+\.\d{2}\s*){1,7})",
        snippet,
        flags=re.IGNORECASE,
    )
    if not totals_match:
        return None

    totals = re.findall(r"\$[\d,]+\.\d{2}", totals_match.group(1))
    weekday_index = weekdays.index(weekday)
    if weekday_index >= len(totals):
        return None
    return f"Direct table match: {weekday.title()} daily sales total = {totals[weekday_index]}."

class SearchAgent:
    def __init__(self,search_service:SearchService):
        self.search_service = search_service
        
    @observe(name="search_agent")
    async def run(self, state:GraphState) -> AgentResult:
        logger.info(
            "Search agent started.",
            extra={"route": state.route, "message_preview": state.user_message[:120]},
        )
        
        tool_results = search_knowledge(state.user_message)
        results = await self.search_service.search(state.user_message)
        if tool_results and not results:
            logger.info("MCP knowledge tool supplied search results.")
            results = [
                SearchResult(
                    title=str(item.get("title", "Untitled")),
                    snippet=str(item.get("snippet", "")),
                    score=float(item.get("score", 0)),
                    source=str(item.get("source", "mcp knowledge tool")),
                    file_name=item.get("file_name"),
                )
                for item in tool_results
            ]

        state.search_results = results
        lines = []
        for index, item in enumerate(results):
            location_parts = []
            if item.file_name:
                location_parts.append(item.file_name)
            if item.page_number is not None:
                location_parts.append(f"Page {item.page_number}")

            location = f" ({', '.join(location_parts)})" if location_parts else ""
            lines.append(
                f"{index + 1}. {item.title}{location} — {item.snippet}"
            )

        output = "Search results from Elasticsearch:\n" + "\n".join(lines) if lines else "No matching documents found."
        direct_matches = [
            match
            for item in results
            for match in [_daily_total_from_document(state.user_message, item.snippet)]
            if match
        ]
        if direct_matches:
            output = "\n".join(direct_matches) + "\n\n" + output
        
        state.search_output = output
        logger.info(
            "Search agent completed.",
            extra={"results_count": len(results), "index_name": self.search_service.index_name},
        )
        
        return AgentResult(
            agent="search",
            output=output,
            metadata={
                "results_count": len(results),
                "index_name" : self.search_service.index_name
            }
        )
 