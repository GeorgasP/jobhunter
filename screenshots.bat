@echo off
setlocal
cd /d "%~dp0"
title JobHunter - screenshots

echo.
echo   JobHunter - screenshots gia to Chrome Web Store
echo   ===============================================
echo.
echo   Anoigei topiko server kai tis 4 selides sto Chrome.
echo   Gia kathe mia:
echo.
echo     1. F12  (anoigei ta DevTools)
echo     2. Ctrl+Shift+P
echo     3. grapse:  screenshot
echo     4. dialekse "Capture screenshot"
echo.
echo   To arxeio pefteti sta Downloads se akrivws 1280x800.
echo   Meta valta sto store\screenshots\ os 1.png, 2.png, 3.png, 4.png
echo.
echo   ---------------------------------------------------------
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo   [*] Den vrika python. Anoixe ta arxeia me diplo klik anti gia auto:
  echo       store\screenshots\1-matches.html  ...kai ta ypoloipa
  echo.
  pause
  exit /b 1
)

start "" /min python -m http.server 8765
timeout /t 2 /nobreak >nul

for %%f in (1-matches 2-pipeline 3-autofill 4-onboarding) do (
  start "" "http://127.0.0.1:8765/store/screenshots/%%f.html"
  timeout /t 1 /nobreak >nul
)

echo.
echo   Oi 4 selides anoixan. Otan teleiwseis, kleise auto to parathyro
echo   gia na stamatisei o server.
echo.
pause

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do taskkill /f /pid %%p >nul 2>&1
exit /b 0
