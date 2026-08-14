@echo off
REM ════════════════════════════════════════════════════════════════
REM  Κατεβάζει τις αλλαγές από το GitHub.
REM  Μετά: στο JobHunter → Settings → «Apply update» (ή reload στο
REM  chrome://extensions). Ο Chrome ΔΕΝ φορτώνει ποτέ κώδικα από το
REM  internet — τα αρχεία πρέπει να είναι στον δίσκο.
REM ════════════════════════════════════════════════════════════════
chcp 65001 >nul
title JobHunter — update
cd /d "%~dp0"

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo   ΣΦΑΛΜΑ: δεν βρεθηκε git. https://git-scm.com/downloads
    pause & exit /b 1
)

echo.
echo   Κατεβαζω αλλαγες...
echo.

for /f %%i in ('git rev-parse --short HEAD') do set BEFORE=%%i
git pull --rebase
if %errorlevel% neq 0 (
    echo.
    echo   Το pull απετυχε. Συνηθως φταινε τοπικες αλλαγες που δεν εχουν γινει commit.
    echo   Δες τι αλλαξες:   git status
    pause & exit /b 1
)
for /f %%i in ('git rev-parse --short HEAD') do set AFTER=%%i

echo.
if "%BEFORE%"=="%AFTER%" (
    echo   Εισαι ηδη ενημερωμενος ^(%AFTER%^).
) else (
    echo   Ενημερωθηκε: %BEFORE% -^> %AFTER%
    echo.
    echo   Τι αλλαξε:
    git log --oneline %BEFORE%..%AFTER%
    echo.
    echo   ┌────────────────────────────────────────────────┐
    echo   │  ΤΕΛΕΥΤΑΙΟ ΒΗΜΑ                                │
    echo   │  Ανοιξε το JobHunter -^> Settings -^> Apply update │
    echo   │  ή πατα το ↻ στο chrome://extensions           │
    echo   └────────────────────────────────────────────────┘
)
echo.
pause
