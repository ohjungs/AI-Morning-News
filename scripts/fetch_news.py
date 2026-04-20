import feedparser
import requests
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dateutil import parser as dateparser

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

today_str = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(
    filename=LOG_DIR / f"{today_str}.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)
log = logging.getLogger(__name__)

TIMEOUT = 10
MAX_PER_SOURCE = 10
MAX_AGE_DAYS = 7  # 7일 이내 기사만 수집

def load_sources():
    with open(DATA_DIR / "sources.json", encoding="utf-8") as f:
        return json.load(f)

def parse_date(entry):
    for field in ["published", "updated", "created"]:
        val = getattr(entry, field, None)
        if val:
            try:
                return dateparser.parse(val)
            except Exception:
                pass
    return datetime.now(timezone.utc)

def fetch_rss(source: dict) -> list:
    items = []
    rss_url = source.get("rss")
    if not rss_url:
        return items

    try:
        feed = feedparser.parse(rss_url, request_headers={"User-Agent": "MorningNews/1.0"})
        if feed.bozo and not feed.entries:
            log.warning(f"[{source['id']}] RSS 파싱 오류: {feed.bozo_exception}")
            return items

        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

        for entry in feed.entries[:MAX_PER_SOURCE]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            published = parse_date(entry)

            if not title or not link:
                continue

            # 7일 이내 기사만 수집
            if published:
                pub_aware = published if published.tzinfo else published.replace(tzinfo=timezone.utc)
                if pub_aware < cutoff:
                    log.debug(f"오래된 기사 제외 ({published.date()}): {title}")
                    continue

            items.append({
                "id": source["id"],
                "source_name": source["name"],
                "category": source["category"],
                "trust_score": source["trust_score"],
                "title": title,
                "url": link,
                "summary_raw": summary[:500],
                "published": published.isoformat() if published else None
            })

        log.info(f"[{source['id']}] {len(items)}건 수집 완료")

    except Exception as e:
        log.error(f"[{source['id']}] 수집 실패: {e}")

    return items

def fetch_all() -> list:
    config = load_sources()
    all_items = []
    failed_sources = []

    for source in config["sources"]:
        if not source.get("active", True):
            continue
        items = fetch_rss(source)
        if not items:
            failed_sources.append(source["id"])
            log.warning(f"[{source['id']}] 수집 결과 없음 - 소스 상태 점검 필요")
        all_items.extend(items)
        time.sleep(0.5)

    log.info(f"전체 수집 완료: {len(all_items)}건 / 실패 소스: {failed_sources}")

    update_stats(len(all_items), failed_sources)
    return all_items

def update_stats(total: int, failed: list):
    stats_path = DATA_DIR / "stats.json"
    with open(stats_path, encoding="utf-8") as f:
        stats = json.load(f)

    stats["runs"].append({
        "date": today_str,
        "total_fetched": total,
        "failed_sources": failed,
        "timestamp": datetime.now().isoformat()
    })

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    items = fetch_all()
    out_path = DATA_DIR / "fetched.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"수집 완료: {len(items)}건 -> {out_path}")
