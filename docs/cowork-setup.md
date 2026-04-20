# Cowork + Dispatch 설정 가이드

## 1. 사전 준비

### 1-1. 프로젝트 폴더 위치 확정
`run.bat`이 있는 폴더 경로를 확인한다.
예: `C:\Projects\morning-news\`

### 1-2. 최초 환경 세팅 (1회만)
```
C:\Projects\morning-news\setup.bat
```
Python 패키지 설치 + Claude CLI 확인 자동 진행.

### 1-3. Claude CLI 로그인 확인
```
claude
```
로그인 상태가 아니면 브라우저 인증 진행 후 재시도.

---

## 2. Cowork 스케줄 설정

Cowork는 Anthropic의 데스크톱 자동화 도구다.
아래 순서로 매일 08:00 자동 실행을 등록한다.

### 설정 방법

1. **Cowork 실행** → 좌측 사이드바 "Automations" 클릭
2. **New Automation** 클릭
3. 아래와 같이 입력:

| 항목 | 값 |
|------|-----|
| Name | Morning News |
| Trigger | Schedule |
| Time | 08:00 |
| Repeat | Daily (평일만 원하면 Weekdays 선택) |
| Action | Run Command |
| Command | `cmd /c "C:\Projects\morning-news\run.bat"` |

4. **Save** 후 **Enable** 토글 ON

---

## 3. Dispatch 연동 (선택)

Dispatch는 Claude Code 작업을 원격/비동기로 실행할 때 사용한다.
현재 구조(로컬 bat 실행)는 Cowork만으로 충분하나,
향후 서버 이전 시 아래 방식으로 전환 가능하다.

```json
{
  "task": "morning-news",
  "schedule": "0 8 * * *",
  "command": "python scripts/fetch_news.py && python scripts/deduplicate.py && python scripts/filter.py && python scripts/rank.py && python scripts/summarize.py && python scripts/render.py && python scripts/to_pdf.py",
  "working_dir": "C:/Projects/morning-news"
}
```

---

## 4. 수동 실행 방법

Cowork 없이 즉시 실행하고 싶을 때:
```
C:\Projects\morning-news\run.bat
```
더블클릭 또는 cmd에서 직접 실행 가능.

---

## 5. 로그 확인

실행 후 문제가 있을 경우:
```
C:\Projects\morning-news\logs\YYYY-MM-DD.log
```
수집 건수, 실패 소스, 요약 오류 등 전체 기록 확인 가능.

---

## 6. 출력 파일 위치

```
C:\Projects\morning-news\output\
├── 2026-04-20.html   ← 브라우저로 열림
└── 2026-04-20.pdf    ← PDF 저장
```

날짜별로 누적 저장되어 과거 뉴스 열람 가능.
