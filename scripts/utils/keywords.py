import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# keywords.md 섹션명 → filter.py 키워드 딕셔너리 키 매핑
SECTION_MAP = {
    "AI":          "keywords_ai",
    "테크":         "keywords_tech",
    "보안":         "keywords_security",
    "국내 IT/AI":   "keywords_kr",
    "주식":         "keywords_stock",
    "차단 키워드":   "keywords_blocked",
}

# 탭으로 노출할 섹션 순서 (차단·중점주제 제외)
TAB_ORDER = ["AI", "테크", "보안", "국내 IT/AI", "주식"]


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def load_keywords(md_path: Path = DATA_DIR / "keywords.md") -> dict:
    """각 섹션의 키워드 리스트 반환. 중점주제는 별도 함수로 처리."""
    text = _strip_comments(md_path.read_text(encoding="utf-8"))
    result = {}
    current_key = None
    current_words = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            if current_key is not None:
                result[current_key] = current_words
            section = line[3:].strip()
            current_key = SECTION_MAP.get(section)  # 중점주제 → None (무시)
            current_words = []
        elif current_key is not None and line and not line.startswith("#") and line != "---":
            words = [w.strip() for w in line.split(",") if w.strip()]
            current_words.extend(words)

    if current_key is not None:
        result[current_key] = current_words

    return result


# 중점주제 키워드 추출 시 제외할 범용어
_FOCUS_STOP = {
    # 한국어 범용
    "및", "등", "의", "과", "와", "이", "가", "을", "를", "은", "는",
    "에서", "에", "으로", "서", "도", "만", "을", "를", "위한",
    "서비스", "현황", "도입", "출시", "기업", "현업", "개발", "기술",
    "동향", "관련", "분야", "시장", "업체", "산업", "플랫폼", "솔루션",
    "최신", "주요", "글로벌", "국내", "해외", "성능", "경쟁",
    # 영어 범용 (소문자 비교)
    "and", "the", "of", "in", "to", "for", "with", "by", "on", "at",
    "latest", "new", "top", "best", "key",
}


def load_focus_topics(md_path: Path = DATA_DIR / "keywords.md") -> list:
    """## 중점주제 섹션 파싱 → 구체적 키워드만 추출 (범용어 제외).

    Returns:
        [{"name": str, "detail": str, "keywords": [str]}]
    """
    text = _strip_comments(md_path.read_text(encoding="utf-8"))
    in_focus = False
    topics = []

    for line in text.splitlines():
        line = line.strip()
        if line == "## 중점주제":
            in_focus = True
            continue
        if in_focus:
            if line.startswith("## "):
                break
            if line.startswith("- "):
                content = line[2:].strip()
                if ":" in content:
                    name, detail = content.split(":", 1)
                else:
                    name, detail = content, ""
                name = name.strip()
                detail = detail.strip()

                raw = f"{name} {detail}"
                strip_chars = "·,.()/「」『』[]【】<>《》''\""
                keywords = []
                for w in re.split(r"[\s·/,]+", raw):
                    w = w.strip(strip_chars)
                    # 3자 이상이고 범용어 아닌 것만
                    if len(w) >= 3 and w.lower() not in _FOCUS_STOP:
                        keywords.append(w)

                topics.append({"name": name, "detail": detail, "keywords": keywords})

    return topics


def load_tab_sections(md_path: Path = DATA_DIR / "keywords.md") -> list:
    """keywords.md에서 실제로 정의된 탭 섹션 목록 반환 (차단 키워드·중점주제 제외)."""
    text = _strip_comments(md_path.read_text(encoding="utf-8"))
    found = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            name = line[3:].strip()
            if name not in ("차단 키워드", "중점주제") and name in SECTION_MAP:
                found.append(name)
    # TAB_ORDER 기준으로 정렬 (keywords.md 순서 무시, 일관성 유지)
    return [s for s in TAB_ORDER if s in found]


def get_section_keyword_map(md_path: Path = DATA_DIR / "keywords.md") -> dict:
    """탭 섹션명 → 키워드 리스트 매핑 반환."""
    kw_dict = load_keywords(md_path)
    result = {}
    for section_name in TAB_ORDER:
        kw_key = SECTION_MAP.get(section_name)
        if kw_key:
            kws = kw_dict.get(kw_key, [])
            if kws:
                result[section_name] = kws
    return result
