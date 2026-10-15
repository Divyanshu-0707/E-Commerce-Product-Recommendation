import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class FeedbackRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=1000)
    helpful: bool

    @field_validator("product_id", "query")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


FEEDBACK_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "feedback.jsonl"
)


def record_feedback(feedback: FeedbackRequest) -> None:
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "product_id": feedback.product_id,
        "query": feedback.query,
        "helpful": feedback.helpful,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with FEEDBACK_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")