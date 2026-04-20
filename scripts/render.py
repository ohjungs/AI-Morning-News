import json
import logging
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Undefined

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
log = logging.getLogger(__name__)

WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

def load_advisor() -> dict:
    path = DATA_DIR / "advisor.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def render_html(items: list) -> Path:
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekday = WEEKDAYS[today.weekday()]

    counts = {"official": 0, "news": 0, "blog": 0, "research": 0, "influencer": 0, "tech": 0, "security": 0}
    for item in items:
        cat = item.get("category", "news")
        if cat in counts:
            counts[cat] += 1

    advisor = load_advisor()

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("news.html")

    html = template.render(
        date=date_str,
        weekday=weekday,
        total=len(items),
        counts=counts,
        items=items,
        advisor=advisor
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
