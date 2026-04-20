import logging
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
log = logging.getLogger(__name__)

def convert_to_pdf(html_path: Path) -> Path:
    pdf_path = html_path.with_suffix(".pdf")
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        log.info(f"PDF 변환 완료: {pdf_path}")
        return pdf_path
    except ImportError:
        log.warning("WeasyPrint 미설치 - PDF 변환 생략 (HTML만 사용)")
        return None
    except Exception as e:
        log.error(f"PDF 변환 실패: {e}")
        return None

if __name__ == "__main__":
    date_str = datetime.now().strftime("%Y-%m-%d")
    html_path = OUTPUT_DIR / f"{date_str}.html"

    if not html_path.exists():
        print(f"HTML 파일 없음: {html_path}")
        exit(1)

    pdf_path = convert_to_pdf(html_path)
    if pdf_path:
        print(f"PDF 생성: {pdf_path}")
    else:
        print("PDF 변환 실패 또는 생략 - HTML로 계속 진행")
