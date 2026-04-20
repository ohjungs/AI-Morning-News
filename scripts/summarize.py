import json
import subprocess
import logging
import time
import sys
import shutil
import tempfile
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
log = setup_logger(__name__)

MAX_ITEMS = 50  # 30 → 50으로 확장
RETRY_COUNT = 2
RETRY_DELAY = 3

PROMPT_TEMPLATE = """다음 뉴스 기사들을 각각 한국어로 요약해줘.
각 기사마다 반드시:
1. 제목을 한국어로 번역
2. 내용을 한국어 3줄 이내로 요약

반드시 JSON 배열 형식으로만 반환하고, 다른 텍스트는 절대 포함하지 마.
코드블록(```)도 포함하지 마. 순수 JSON만 반환.

형식:
[
  {{"index": 0, "title_ko": "한국어 제목", "summary": "첫 번째 줄\\n두 번째 줄\\n세 번째 줄"}},
  ...
]

뉴스 목록:
{news_list}
"""

def build_news_list(items: list) -> str:
    lines = []
    for i, item in enumerate(items):
        title = item.get("title", "")
        raw = item.get("summary_raw", "")[:300]
        lines.append(f"[{i}] 제목: {title}\n    내용: {raw}")
    return "\n\n".join(lines)

def load_model_config() -> dict:
    config_path = DATA_DIR / "model_config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def find_claude_cmd() -> str:
    for name in ["claude", "claude.cmd"]:
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError("Claude CLI를 찾을 수 없습니다.")

def call_claude_cli(prompt: str, model: str = None) -> str:
    """
    프롬프트를 임시 파일에 저장 후 type 파이프로 전달.
    Windows에서 긴 인수 전달 시 cmd.exe가 특수문자를 망가뜨리는 문제 방지.
    """
    try:
        claude_cmd = find_claude_cmd()
    except FileNotFoundError as e:
        log.error(str(e))
        return ""  # CLI 없으면 빈 문자열 → 파이프라인 중단 없이 계속 진행

    for attempt in range(RETRY_COUNT):
        tmp_path = None
        try:
            if not claude_cmd:
                raise FileNotFoundError("Claude CLI를 찾을 수 없습니다. 'npm install -g @anthropic-ai/claude-code' 실행 후 재시도.")
            # 임시 파일에 프롬프트 저장
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(prompt)
                tmp_path = f.name

            # type 명령으로 파일 내용을 claude stdin에 파이프
            # text=False로 raw bytes 수신 후 UTF-8 수동 디코딩 (Windows CP949 오디코딩 방지)
            model_flag = f'--model {model}' if model else ''
            cmd = f'type "{tmp_path}" | "{claude_cmd}" --output-format text {model_flag}'.strip()
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,
                shell=True
            )
            stdout = result.stdout.decode("utf-8", errors="replace").strip()
            stderr = result.stderr.decode("utf-8", errors="replace").strip()

            if result.returncode == 0 and stdout:
                return stdout
            log.warning(f"Claude CLI 응답 없음 (시도 {attempt+1}): {stderr[:200]}")

        except subprocess.TimeoutExpired:
            log.error(f"Claude CLI 타임아웃 (시도 {attempt+1})")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if attempt < RETRY_COUNT - 1:
            time.sleep(RETRY_DELAY)

    return ""

def parse_summaries(response: str, count: int) -> list:
    try:
        cleaned = response.strip()
        # 코드블록 제거
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        data = json.loads(cleaned)
        summaries = [{"title_ko": "", "summary": ""}] * count
        for entry in data:
            idx = entry.get("index", -1)
            if 0 <= idx < count:
                summaries[idx] = {
                    "title_ko": entry.get("title_ko", ""),
                    "summary": entry.get("summary", "")
                }
        return summaries
    except Exception as e:
        log.error(f"요약 파싱 실패: {e}\n원본: {response[:300]}")
        return [{"title_ko": "", "summary": "요약 생성 실패"}] * count

def summarize(items: list) -> list:
    model_cfg = load_model_config()
    model = model_cfg.get("summarize")
    log.info(f"요약 모델: {model}")

    items = items[:MAX_ITEMS]
    batch_size = 5  # 배치 크기 줄여서 프롬프트 길이 제한
    all_summaries = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        news_list = build_news_list(batch)
        prompt = PROMPT_TEMPLATE.format(news_list=news_list)

        log.info(f"요약 요청: {i}~{i+len(batch)-1}번 기사")
        response = call_claude_cli(prompt, model=model)

        if response:
            summaries = parse_summaries(response, len(batch))
        else:
            summaries = [{"title_ko": "", "summary": "요약 생성 실패"}] * len(batch)

        all_summaries.extend(summaries)
        time.sleep(1)

    for i, item in enumerate(items):
        if i < len(all_summaries):
            item["title_ko"] = all_summaries[i].get("title_ko") or item.get("title", "")
            item["summary_ko"] = all_summaries[i].get("summary", "")
        else:
            item["title_ko"] = item.get("title", "")
            item["summary_ko"] = ""

    log.info(f"요약 완료: {len(items)}건")
    return items

if __name__ == "__main__":
    with open(DATA_DIR / "ranked.json", encoding="utf-8") as f:
        items = json.load(f)

    result = summarize(items)

    with open(DATA_DIR / "summarized.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"요약 완료: {len(result)}건")
