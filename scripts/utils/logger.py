"""
공통 로깅 설정 유틸
모든 스크립트에서 setup_logger()를 호출해 일관된 로그 파일 생성
"""
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / "logs"


def setup_logger(name: str = __name__) -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{today}.log"

    # 루트 로거에 이미 핸들러가 있으면 중복 설정 방지
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            encoding="utf-8",
        )
        # 콘솔에도 ERROR 이상 출력
        console = logging.StreamHandler()
        console.setLevel(logging.ERROR)
        console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        root.addHandler(console)

    return logging.getLogger(name)
