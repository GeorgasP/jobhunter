@echo off
REM ════════════════════════════════════════════════════════════════
REM  JobHunter — launcher. Double-click to start.
REM  No pip install needed: runs on plain Python 3.11+.
REM ════════════════════════════════════════════════════════════════
chcp 65001 >nul
title JobHunter
cd /d "%~dp0"

where python.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   ERROR: Python was not found.
    echo   Install it from https://python.org/downloads and tick "Add to PATH".
    echo.
    pause
    exit /b 1
)

if not exist "data\profile.json" (
    echo.
    echo   First run — let's set up your profile.
    echo.
    python -m jobhunter init
    echo.
    pause
    exit /b 0
)

:menu
cls
echo.
echo   ╔══════════════════════════════════════════════════╗
echo   ║               JobHunter                          ║
echo   ╚══════════════════════════════════════════════════╝
echo.
echo    1.  Dashboard (opens in your browser)
echo    2.  Scan and prepare 5 applications
echo    3.  Scan only
echo    4.  Show matches
echo    5.  Application history
echo    6.  Check inbox for replies
echo    7.  Diagnostics
echo    8.  Edit my profile
echo    9.  Exit
echo.
set /p choice="   Choice: "

if "%choice%"=="1" (python -m jobhunter serve & goto menu)
if "%choice%"=="2" (python -m jobhunter run --apply 5 & pause & goto menu)
if "%choice%"=="3" (python -m jobhunter run & pause & goto menu)
if "%choice%"=="4" (python -m jobhunter matches & pause & goto menu)
if "%choice%"=="5" (python -m jobhunter history & pause & goto menu)
if "%choice%"=="6" (python -m jobhunter inbox & pause & goto menu)
if "%choice%"=="7" (python -m jobhunter doctor & pause & goto menu)
if "%choice%"=="8" (notepad data\profile.json & python -m jobhunter rescore & pause & goto menu)
if "%choice%"=="9" exit /b 0
goto menu
