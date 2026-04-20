import json
import logging
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
log = logging.getLogger(__name__)

CATEGORY_WEIGHT = {
    "official": 5,
    "research": 4,
    "blog": 3,
    "news": 2,
    "influencer": 2
}

HIGH_PRIORITY_KEYWORDS = [
    "GPT-5", "Claude 4", "Gemini", "breakthrough", "release", "launch",
    "AGI", "safety", "출시", "발표", "공개", "새로운"
]

def recency_score(published_str: str) -> float:
    if not published_str:
        return 0.0
    try:
        pub = datetime.fromisoformat(published_str)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours_ago = (now - pub).total_seconds() / 3600
        if hours_ago <= 6:
            return 5.0
        elif hours_ago <= 24:
            return 3.0
        elif hours_ago <= 72:
            return 1.0
        else:
            return 0.0
    except Exception:
        return 0.0

def keyword_boost(item: dict) -> float:
    text = (item.get("title", "") + " " + item.get("summary_raw", "")).lower()
    score = sum(1.0 for kw in HIGH_PRIORITY_KEYWORDS if kw.lower() in text)
    return min(score, 3.0)

def assign_priority(score: float) -> str:
    if score >= 10:
        return "high"
    elif score >= 6:
        return "medium"
    else:
        return "low"

def rank_items(items: list) -> list:
    for item in items:
        cat_score = CATEGORY_WEIGHT.get(item.get("category", "news"), 1)
        trust_score = item.get("trust_score", 5) * 0.3
        rec_score = recency_score(item.get("published"))
        kw_score = keyword_boost(item)

        total = cat_score + trust_score + rec_score + kw_score
        item["rank_score"] = round(total, 2)
        item["priority"] = assign_priority(total)

    ranked = sorted(items, key=lambda x: x["rank_score"], reverse=True)
    log.info(f"랭킹 완료: {len(ranked)}건")
    return ranked

if __name__ == "__main__":
    with open(DATA_DIR / "filtered.json", encoding="utf-8") as f:
        items = json.load(f)

    result = rank_items(items)

    with open(DATA_DIR / "ranked.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"랭킹 완료: {len(result)}건")
