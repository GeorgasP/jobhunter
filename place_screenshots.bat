@echo off
setlocal
cd /d "%~dp0"
title JobHunter - topothetisi screenshots
echo.
echo   Psaxnw tis lipseis sta Downloads kai tis vazw sti thesi tous...
echo.
python store\place_screenshots.py
echo.
pause
