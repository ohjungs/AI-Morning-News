import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.keywords import get_section_keyword_map, load_focus_topics
log = setup_logger(__name__)

CATEGORY_WEIGHT = {
    "official":   5,
    "research":   4,
    "security":   4,
    "blog":       3,
    "news":       3,
    "news_kr":    3,
    "tech":       3,
    "influencer": 2,
}

HIGH_PRIORITY_KEYWORDS = [
    "GPT-5", "Claude 4", "Gemini", "breakthrough", "release", "launch",
    "AGI", "safety", "출시", "발표", "공개", "새로운",
    "quantum", "chip", "semiconductor", "robot", "space", "반도체", "양자", "로봇",
    "zero-day", "critical", "vulnerability", "breach", "ransomware",
    "CVE", "exploit", "취약점", "해킹", "랜섬웨어",
]


def recency_score(published_str: str) -> float:
    if not published_str:
        return 0.0
    try:
        pub = datetime.fromisoformat(published_str)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        hours_ago = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
        if hours_ago <= 6:   return 5.0
        if hours_ago <= 24:  return 3.0
        if hours_ago <= 72:  return 1.0
        return 0.0
    except Exception:
        return 0.0


def keyword_boost(item: dict) -> float:
    text = (item.get("title", "") + " " + item.get("summary_raw", "")).lower()
    return min(sum(1.0 for kw in HIGH_PRIORITY_KEYWORDS if kw.lower() in text), 3.0)


def assign_priority(score: float) -> str:
    if score >= 10: return "high"
    if score >= 6:  return "medium"
    return "low"


def tag_sections(items: list, section_kw_map: dict, focus_topics: list) -> list:
    """각 기사에 matched_sections / matched_focus 필드 부착 + 중점주제 점수 부스트."""
    for item in items:
        text = (item.get("title", "") + " " + item.get("summary_raw", "")).lower()

        matched_sections = [
            section for section, kws in section_kw_map.items()
            if any(kw.lower() in text for kw in kws)
        ]
        item["matched_sections"] = matched_sections

        matched_focus = [
            t["name"] for t in focus_topics
            if any(kw.lower() in text for kw in t.get("keywords", []))
        ]
        item["matched_focus"] = matched_focus

        if matched_focus:
            item["rank_score"] = round(
                item.get("rank_score", 0) + 3.0 * len(matched_focus), 2
            )

    return items


def rank_items(items: list) -> list:
    section_kw_map = get_section_keyword_map()
    focus_topics   = load_focus_topics()

    for item in items:
        cat_score   = CATEGORY_WEIGHT.get(item.get("category", "news"), 1)
        trust_score = item.get("trust_score", 5) * 0.3
        rec_score   = recency_score(item.get("published"))
        kw_score    = keyword_boost(item)

        total = cat_score + trust_score + rec_score + kw_score
        item["rank_score"] = round(total, 2)
        item["priority"]   = assign_priority(total)

    items = tag_sections(items, section_kw_map, focus_topics)
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
