import json
import uuid
from typing import Any, Dict, List

from app.config.settings import settings
from app.memory.redis_memory import RedisMemoryService


class FeedbackService:
    def __init__(self) -> None:
        self.memory = RedisMemoryService(settings.redis_url, settings.redis_ttl_seconds)
        self.local_feedback: List[Dict[str, Any]] = []

    def save(self, payload: Dict[str, Any]) -> str:
        feedback_id = str(uuid.uuid4())
        record = {"id": feedback_id, **payload}
        key = f"feedback:{feedback_id}"
        self.memory.set_value(key, json.dumps(record), ttl=-1)
        self.local_feedback.append(record)
        signal = "grounded" if payload.get("rating") == "down" else "normal"
        self.memory.set_value("feedback:routing_signal", signal, ttl=-1)
        return feedback_id

    def routing_signal(self) -> str:
        return self.memory.get_value("feedback:routing_signal") or "normal"

    def metrics(self) -> Dict[str, Any]:
        records = self.local_feedback
        positive = sum(item.get("rating") == "up" for item in records)
        negative = sum(item.get("rating") == "down" for item in records)
        approved = sum(item.get("approved", False) for item in records)
        comments = [item["comment"] for item in records if item.get("comment")]
        review_queue = sum(
            item.get("rating") == "down" and not item.get("approved", False)
            for item in records
        )
        return {
            "total": len(records),
            "positive": positive,
            "negative": negative,
            "approval_rate": round(approved / len(records), 2) if records else 0.0,
            "review_queue": review_queue,
            "recent_comments": comments[-5:],
        }
