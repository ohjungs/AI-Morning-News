import json
import logging
import sys
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
log = setup_logger(__name__)

TITLE_SIMILARITY_THRESHOLD = 0.85
HISTORY_DAYS = 7  # 7일 이내 히스토리만 유지

def load_history() -> dict:
    path = DATA_DIR / "history.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # seen_urls/seen_titles가 리스트면 날짜 기반 구조로 마이그레이션
    if data.get("seen_urls") and isinstance(data["seen_urls"][0], str):
        data["seen_urls"] = []
        data["seen_titles"] = []
    return data

def save_history(history: dict):
    # 7일 이내 항목만 유지
    cutoff = (datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)).isoformat()
    history["seen_urls"] = [
        e for e in history.get("seen_urls", [])
        if isinstance(e, dict) and e.get("date", "") >= cutoff
    ]
    history["seen_titles"] = [
        e for e in history.get("seen_titles", [])
        if isinstance(e, dict) and e.get("date", "") >= cutoff
    ]
    with open(DATA_DIR / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def is_similar_title(title: str, seen_titles: list) -> bool:
    for entry in seen_titles[-200:]:
        seen = entry["title"] if isinstance(entry, dict) else entry
        ratio = SequenceMatcher(None, title.lower(), seen.lower()).ratio()
        if ratio >= TITLE_SIMILARITY_THRESHOLD:
            return True
    return False

def deduplicate(items: list) -> list:
    history = load_history()
    now_iso = datetime.now(timezone.utc).isoformat()

    seen_url_set = {e["url"] for e in history.get("seen_urls", []) if isinstance(e, dict)}
    seen_titles = list(history.get("seen_titles", []))

    result = []
    today_urls = []
    today_titles = []

    for item in items:
        url = item.get("url", "")
        title = item.get("title", "")

        if url in seen_url_set:
            log.debug(f"URL 중복 제거: {title}")
            continue

        if is_similar_title(title, seen_titles + today_titles):
            log.debug(f"제목 유사 중복 제거: {title}")
            continue

        result.append(item)
        today_urls.append({"url": url, "date": now_iso})
        today_titles.append({"title": title, "date": now_iso})

    history["seen_urls"] = history.get("seen_urls", []) + today_urls
    history["seen_titles"] = history.get("seen_titles", []) + today_titles
    save_history(history)

    log.info(f"중복 제거: {len(items)}건 -> {len(result)}건")
    return result

if __name__ == "__main__":
    with open(DATA_DIR / "fetched.json", encoding="utf-8") as f:
        items = json.load(f)

    result = deduplicate(items)

    with open(DATA_DIR / "deduped.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"중복 제거 완료: {len(result)}건")
