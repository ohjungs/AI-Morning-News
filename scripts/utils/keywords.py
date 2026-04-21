from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# keywords.md 섹션명 → filter.py에서 사용하는 키 매핑
SECTION_MAP = {
    "AI":          "keywords_ai",
    "테크":         "keywords_tech",
    "보안":         "keywords_security",
    "국내 IT/AI":   "keywords_kr",
    "차단 키워드":   "keywords_blocked",
}

def load_keywords(md_path: Path = DATA_DIR / "keywords.md") -> dict:
    text = md_path.read_text(encoding="utf-8")

    # HTML 주석 블록(<!-- ... -->)을 먼저 제거
    import re
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    result = {}
    current_key = None
    current_words = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            if current_key is not None:
                result[current_key] = current_words
            section = line[3:].strip()
            current_key = SECTION_MAP.get(section)
            current_words = []
        elif current_key is not None and line and not line.startswith("#") and line != "---":
            words = [w.strip() for w in line.split(",") if w.strip()]
            current_words.extend(words)

    if current_key is not None:
        result[current_key] = current_words

    return result
