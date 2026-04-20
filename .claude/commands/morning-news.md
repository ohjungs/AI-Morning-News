# /morning-news

AI 뉴스 수집 파이프라인을 실행하고 오늘의 뉴스 HTML을 생성합니다.

## 사용법
```
/morning-news
```

## 실행 순서
1. `scripts/fetch_news.py` - RSS/웹에서 AI 뉴스 수집
2. `scripts/deduplicate.py` - 중복 기사 제거
3. `scripts/filter.py` - 신뢰도/키워드 필터링
4. `scripts/rank.py` - 중요도 랭킹 산정
5. `scripts/summarize.py` - 한국어 3줄 요약 생성
6. `scripts/render.py` - HTML 렌더링
7. `scripts/to_pdf.py` - PDF 변환
8. 브라우저에서 output/YYYY-MM-DD.html 오픈

## 실행 명령
```bash
cd /path/to/morning-news
python scripts/fetch_news.py && \
python scripts/deduplicate.py && \
python scripts/filter.py && \
python scripts/rank.py && \
python scripts/summarize.py && \
python scripts/render.py && \
python scripts/to_pdf.py
```

출력 완료 후 `output/` 디렉토리에서 오늘 날짜 파일을 확인하세요.
