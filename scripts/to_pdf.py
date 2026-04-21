"""
to_pdf.py - HTML → PDF 변환
우선순위: pdfkit(wkhtmltopdf) → weasyprint → 생략
wkhtmltopdf 설치: https://wkhtmltopdf.org/downloads.html
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
log = setup_logger(__name__)

# wkhtmltopdf 기본 설치 경로 (Windows)
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"


def convert_with_pdfkit(html_path: Path) -> Path | None:
    try:
        import pdfkit
        pdf_path = html_path.with_suffix(".pdf")
        config = None
        if Path(WKHTMLTOPDF_PATH).exists():
            config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
        pdfkit.from_file(str(html_path), str(pdf_path), configuration=config,
                         options={"encoding": "UTF-8", "quiet": ""})
        log.info(f"PDF 변환 완료 (pdfkit): {pdf_path}")
        return pdf_path
    except OSError as e:
        log.warning(f"pdfkit 실패 (wkhtmltopdf 미설치): {e}")
        return None
    except Exception as e:
        log.error(f"pdfkit 오류: {e}")
        return None


def convert_with_weasyprint(html_path: Path) -> Path | None:
    try:
        from weasyprint import HTML
        pdf_path = html_path.with_suffix(".pdf")
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        log.info(f"PDF 변환 완료 (weasyprint): {pdf_path}")
        return pdf_path
    except Exception as e:
        log.warning(f"weasyprint 실패: {e}")
        return None


def convert_to_pdf(html_path: Path) -> Path | None:
    """pdfkit → weasyprint 순으로 시도, 둘 다 실패 시 None 반환"""
    result = convert_with_pdfkit(html_path)
    if result:
        return result
    result = convert_with_weasyprint(html_path)
    if result:
        return result
    log.warning("PDF 변환 불가 — HTML로 계속 진행. "
                "wkhtmltopdf 설치 권장: https://wkhtmltopdf.org/downloads.html")
    return None


if __name__ == "__main__":
    date_str = datetime.now().strftime("%Y-%m-%d")
    html_path = OUTPUT_DIR / f"{date_str}.html"

    if not html_path.exists():
        print(f"HTML 파일 없음: {html_path}")
        sys.exit(1)

    pdf_path = convert_to_pdf(html_path)
    if pdf_path:
        print(f"PDF 생성: {pdf_path}")
    else:
        print("PDF 생략 - HTML 파일로 계속 진행")
