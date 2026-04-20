"""
advisor.py - Claude Opus가 오늘 뉴스 전체를 분석해 AI 트렌드 인사이트를 생성
"""
import json
import subprocess
import logging
import tempfile
import os
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
log = setup_logger(__name__)

RETRY_COUNT = 2
RETRY_DELAY = 5

ADVISOR_PROMPT = """당신은 AI 산업 전문 애널리스트입니다.
오늘 수집된 AI 뉴스 {count}건을 분석해 아래 형식으로 반환하세요.
반드시 JSON만 반환하고, 코드블록(```)이나 다른 텍스트는 절대 포함하지 마세요.

{{
  "one_line": "오늘 AI 판을 한 문장으로 요약",
  "top_trends": [
    {{"rank": 1, "theme": "트렌드명", "desc": "2~3문장 설명", "articles": [관련 기사 인덱스 숫자들]}},
    {{"rank": 2, "theme": "트렌드명", "desc": "2~3문장 설명", "articles": []}},
    {{"rank": 3, "theme": "트렌드명", "desc": "2~3문장 설명", "articles": []}}
  ],
  "spotlight": {{"company": "주목 기업/프로젝트명", "reason": "주목하는 이유 2문장"}},
  "watchout": "오늘 놓치면 안 될 핵심 포인트 한 문장",
  "sentiment": "bullish 또는 bearish 또는 neutral",
  "sentiment_reason": "센티먼트 판단 근거 한 문장"
}}

오늘 뉴스 목록:
{news_list}
"""

def build_news_list(items: list) -> str:
    lines = []
    for i, item in enumerate(items):
        title = item.get("title_ko") or item.get("title", "")
        summary = item.get("summary_ko", "")[:150]
        source = item.get("source_name", "")
        lines.append(f"[{i}] [{source}] {title}\n    {summary}")
    return "\n\n".join(lines)

def find_claude_cmd() -> str:
    for name in ["claude", "claude.cmd"]:
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError("Claude CLI를 찾을 수 없습니다.")

def load_model_config() -> dict:
    with open(DATA_DIR / "model_config.json", encoding="utf-8") as f:
        return json.load(f)

def call_claude(prompt: str, model: str) -> str:
    claude_cmd = find_claude_cmd()

    for attempt in range(RETRY_COUNT):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(prompt)
                tmp_path = f.name

            cmd = f'type "{tmp_path}" | "{claude_cmd}" --output-format text --model {model}'
            result = subprocess.run(
                cmd, capture_output=True, timeout=180, shell=True
            )
            stdout = result.stdout.decode("utf-8", errors="replace").strip()
            if result.returncode == 0 and stdout:
                return stdout
            log.warning(f"Advisor CLI 응답 없음 (시도 {attempt+1}): {result.stderr.decode('utf-8', errors='replace')[:100]}")
        except subprocess.TimeoutExpired:
            log.error(f"Advisor 타임아웃 (시도 {attempt+1})")
        except Exception as e:
            log.error(f"Advisor 호출 오류 (시도 {attempt+1}): {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if attempt < RETRY_COUNT - 1:
            time.sleep(RETRY_DELAY)

    return ""

def generate_advisor(items: list) -> dict:
    model_cfg = load_model_config()
    model = model_cfg.get("advisor", "claude-opus-4-6")
    log.info(f"Advisor 모델: {model}")

    news_list = build_news_list(items)
    prompt = ADVISOR_PROMPT.format(count=len(items), news_list=news_list)

    response = call_claude(prompt, model)
    if not response:
        log.error("Advisor 응답 없음")
        return _empty_advisor()

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            end = next((i for i in range(len(lines)-1, 0, -1) if lines[i].strip() == "```"), len(lines))
            cleaned = "\n".join(lines[1:end])
        data = json.loads(cleaned)
        log.info("Advisor 생성 완료")
        data["model"] = model
        data["generated_at"] = datetime.now().isoformat()
        return data
    except Exception as e:
        log.error(f"Advisor 파싱 실패: {e}\n원본: {response[:300]}")
        return _empty_advisor()

def _empty_advisor() -> dict:
    return {
        "one_line": "오늘의 AI 인사이트를 생성할 수 없습니다.",
        "top_trends": [],
        "spotlight": {"company": "-", "reason": "-"},
        "watchout": "-",
        "sentiment": "neutral",
        "sentiment_reason": "-",
        "model": "",
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    with open(DATA_DIR / "summarized.json", encoding="utf-8") as f:
        items = json.load(f)

    advisor = generate_advisor(items)

    out_path = DATA_DIR / "advisor.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(advisor, f, ensure_ascii=False, indent=2)

    print(f"Advisor 생성 완료 ({advisor.get('model', '')})")
    print(f"  오늘의 한 줄: {advisor.get('one_line', '')}")
