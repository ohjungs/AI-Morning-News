@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   AI Morning News - %date% %time:~0,5%
echo ========================================

set PYTHON=python
set SCRIPTS=scripts

echo [1/7] 뉴스 수집 중...
%PYTHON% %SCRIPTS%\fetch_news.py
if errorlevel 1 ( echo [ERROR] 뉴스 수집 실패 & goto :error )

echo [2/7] 중복 제거 중...
%PYTHON% %SCRIPTS%\deduplicate.py
if errorlevel 1 ( echo [ERROR] 중복 제거 실패 & goto :error )

echo [3/7] 필터링 중...
%PYTHON% %SCRIPTS%\filter.py
if errorlevel 1 ( echo [ERROR] 필터링 실패 & goto :error )

echo [4/7] 랭킹 산정 중...
%PYTHON% %SCRIPTS%\rank.py
if errorlevel 1 ( echo [ERROR] 랭킹 실패 & goto :error )

echo [5/7] 요약 생성 중 (Claude CLI)...
%PYTHON% %SCRIPTS%\summarize.py
if errorlevel 1 ( echo [ERROR] 요약 실패 & goto :error )

echo [6/8] Advisor 분석 중 (Claude Opus)...
%PYTHON% %SCRIPTS%\advisor.py
if errorlevel 1 ( echo [WARN] Advisor 생성 실패 - 계속 진행 )

echo [7/8] HTML 렌더링 중...
%PYTHON% %SCRIPTS%\render.py
if errorlevel 1 ( echo [ERROR] HTML 렌더링 실패 & goto :error )

echo [8/8] PDF 변환 중...
%PYTHON% %SCRIPTS%\to_pdf.py

echo.
echo ========================================
echo   완료! 브라우저 열기...
echo ========================================

for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
  set YY=%%a
  set MM=%%b
  set DD=%%c
)
set TODAY=%YY%-%MM%-%DD%
start "" "output\%TODAY%.html"
goto :end

:error
echo.
echo [FAIL] 파이프라인 중단 - logs\ 폴더의 로그를 확인하세요.
pause
exit /b 1

:end
echo 정상 완료.
