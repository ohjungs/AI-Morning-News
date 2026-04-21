import json
import sys
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.keywords import load_tab_sections, load_focus_topics
log = setup_logger(__name__)

WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def load_advisor() -> dict:
    path = DATA_DIR / "advisor.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_focus_articles(items: list, focus_topics: list) -> list:
    result = []
    for topic in focus_topics:
        matching = [
            item for item in items
            if topic["name"] in item.get("matched_focus", [])
        ]
        result.append({"topic": topic, "articles": matching[:3]})
    return result


def merge_rank_meta(items: list) -> list:
    """summarized.json에 matched_sections/matched_focus가 없으면 ranked.json에서 보완."""
    ranked_path = DATA_DIR / "ranked.json"
    if not ranked_path.exists():
        return items
    with open(ranked_path, encoding="utf-8") as f:
        ranked = json.load(f)
    rank_by_url = {r["url"]: r for r in ranked}
    for item in items:
        if "matched_sections" not in item or "matched_focus" not in item:
            ref = rank_by_url.get(item.get("url"), {})
            item.setdefault("matched_sections", ref.get("matched_sections", []))
            item.setdefault("matched_focus",    ref.get("matched_focus",    []))
    return items


def render_html(items: list) -> Path:
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekday = WEEKDAYS[today.weekday()]

    items = merge_rank_meta(items)
    tab_sections   = load_tab_sections()
    focus_topics   = load_focus_topics()
    focus_articles = build_focus_articles(items, focus_topics)

    section_counts = {
        section: (
            sum(1 for item in items if item.get("category") == "news_kr")
            if section == "국내 IT/AI"
            else sum(1 for item in items if section in item.get("matched_sections", []))
        )
        for section in tab_sections
    }
    focus_total = sum(1 for item in items if item.get("matched_focus"))

    advisor = load_advisor()

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("news.html")

    html = template.render(
        date=date_str,
        weekday=weekday,
        total=len(items),
        items=items,
        advisor=advisor,
        tab_sections=tab_sections,
        section_counts=section_counts,
        focus_articles=focus_articles,
        focus_total=focus_total,
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{date_str}.html"
    out_path.write_text(html, encoding="utf-8")
    log.info(f"HTML 생성 완료: {out_path}")
    return out_path


if __name__ == "__main__":
    with open(DATA_DIR / "summarized.json", encoding="utf-8") as f:
        items = json.load(f)

    path = render_html(items)
    print(f"HTML 생성: {path}")
