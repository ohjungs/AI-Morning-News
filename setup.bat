@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Morning News - 초기 환경 세팅
echo ========================================

echo [1/4] Python 버전 확인...
python --version
if errorlevel 1 (
  echo [ERROR] Python이 설치되어 있지 않습니다.
  echo         https://www.python.org 에서 Python 3.10 이상 설치 후 재실행하세요.
  pause & exit /b 1
)

echo [2/4] Python 패키지 설치 중...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] 패키지 설치 실패 & pause & exit /b 1 )

echo [3/4] Claude Code CLI 확인...
claude --version
if errorlevel 1 (
  echo [WARNING] Claude CLI가 설치되어 있지 않습니다.
  echo           다음 명령어로 설치하세요:
  echo           npm install -g @anthropic-ai/claude-code
  echo           설치 후 'claude' 명령어로 로그인 완료 후 run.bat을 실행하세요.
) else (
  echo Claude CLI 확인 완료.
)

echo [4/4] 디렉토리 초기화...
if not exist output mkdir output
if not exist logs mkdir logs
if not exist data\history.json (
  echo {"seen_urls": [], "seen_titles": []} > data\history.json
)
if not exist data\stats.json (
  echo {"runs": []} > data\stats.json
)

echo.
echo ========================================
echo   세팅 완료! run.bat 으로 시작하세요.
echo ========================================
pause
