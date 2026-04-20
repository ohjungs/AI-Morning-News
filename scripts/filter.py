import json
import logging
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
log = setup_logger(__name__)

MIN_TRUST_SCORE = 6

# 카테고리별 키워드 매핑 키
CATEGORY_KEYWORD_MAP = {
    "official":   "keywords_ai",
    "news":       "keywords_ai",
    "blog":       "keywords_ai",
    "research":   "keywords_ai",
    "influencer": "keywords_ai",
    "tech":       "keywords_tech",
    "security":   "keywords_security",
}

def load_config() -> dict:
    with open(DATA_DIR / "sources.json", encoding="utf-8") as f:
        return json.load(f)

def is_valid_url(url: str, blocked_domains: list) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        for domain in blocked_domains:
            if domain in parsed.netloc:
                return False
        for pattern in [r"javascript:", r"data:", r"vbscript:", r"\.\./", r"%2e%2e", r"<script"]:
            if re.search(pattern, url, re.IGNORECASE):
                log.warning(f"의심 URL 차단: {url}")
                return False
        return True
    except Exception:
        return False

def has_keyword(item: dict, keywords: list) -> bool:
    text = (item.get("title", "") + " " + item.get("summary_raw", "")).lower()
    return any(kw.lower() in text for kw in keywords)

def has_blocked_keyword(item: dict, keywords_blocked: list) -> bool:
    text = (item.get("title", "") + " " + item.get("summary_raw", "")).lower()
    return any(kw.lower() in text for kw in keywords_blocked)

def filter_items(items: list) -> list:
    config = load_config()
    blocked_domains = config.get("blocked_domains", [])
    keywords_blocked = config.get("keywords_blocked", [])

    result = []
    for item in items:
        url = item.get("url", "")
        trust = item.get("trust_score", 0)
        category = item.get("category", "news")

        if trust < MIN_TRUST_SCORE:
            log.debug(f"신뢰도 부족 제거: {item.get('title')}")
            continue

        if not is_valid_url(url, blocked_domains):
            log.warning(f"URL 검증 실패: {url}")
            continue

        if has_blocked_keyword(item, keywords_blocked):
            log.debug(f"차단 키워드 제거: {item.get('title')}")
            continue

        # 카테고리에 맞는 키워드 목록으로 필터
        kw_key = CATEGORY_KEYWORD_MAP.get(category)
        if kw_key:
            keywords = config.get(kw_key, [])
            if keywords and not has_keyword(item, keywords):
                log.debug(f"[{category}] 키워드 미매칭 제거: {item.get('title')}")
                continue

        result.append(item)

    log.info(f"필터링: {len(items)}건 -> {len(result)}건")
    return result

if __name__ == "__main__":
    with open(DATA_DIR / "deduped.json", encoding="utf-8") as f:
        items = json.load(f)

    result = filter_items(items)

    with open(DATA_DIR / "filtered.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"필터링 완료: {len(result)}건")
