# Morning News - AI 뉴스 자동화 프로젝트

## 목적
매일 아침 8시, AI 관련 최신 뉴스를 자동 수집·요약하여 HTML/PDF로 출력

## 실행 환경
- OS: Windows 로컬 PC
- Python 3.x
- Claude Code CLI (claude.ai 계정 인증)
- Cowork 스케줄러 (08:00 트리거)

## 실행 방법
```
# 최초 1회 환경 세팅
setup.bat

# 수동 실행
run.bat

# Claude Code 커스텀 커맨드
/morning-news
```

## 파이프라인 순서
1. fetch_news.py      - RSS/웹 뉴스 수집
2. deduplicate.py     - 중복 제거 (오늘 + 히스토리)
3. filter.py          - 신뢰도/키워드 필터
4. rank.py            - 중요도 랭킹
5. summarize.py       - Claude CLI 3줄 요약 + 한국어 번역
6. render.py          - HTML 생성
7. to_pdf.py          - PDF 변환
8. 브라우저 자동 오픈

## 디렉토리 구조
```
morning-news/
├── CLAUDE.md
├── CHANGELOG.md
├── setup.bat
├── run.bat
├── requirements.txt
├── .claude/commands/
│   └── morning-news.md
├── scripts/
│   ├── fetch_news.py
│   ├── deduplicate.py
│   ├── filter.py
│   ├── rank.py
│   ├── summarize.py
│   ├── render.py
│   └── to_pdf.py
├── templates/
│   └── news.html
├── data/
│   ├── history.json
│   ├── stats.json
│   └── sources.json
├── output/
│   └── YYYY-MM-DD.html / .pdf
└── logs/
    └── YYYY-MM-DD.log
```

## 소스 목록
sources.json 참조 (공식 블로그, RSS, 인플루언서)

## 주의사항
- Claude Code CLI 로그인 상태 유지 필요
- 외부 URL 검증 로직 포함 (filter.py)
- 히스토리 기반 중복 제거로 동일 기사 반복 방지
