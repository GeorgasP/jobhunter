@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title JobHunter - update

echo.
echo   JobHunter - update
echo   ==================
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo   [!] Auto o fakelos den einai git repository.
  echo       Trekse: git clone https://github.com/GeorgasP/jobhunter.git
  echo.
  pause
  exit /b 1
)

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "MINE=%%b"
if /i "!MINE!"=="main" ( set "THEIRS=Apo" ) else ( set "THEIRS=main" )

echo   Eisai sto branch: !MINE!
echo   To allo branch  : !THEIRS!
echo.

REM --- Adiavastes allages: den ta patame, rotame ---------------------
git diff --quiet && git diff --cached --quiet
if errorlevel 1 (
  echo   [!] Exeis alages pou den exoun ginei commit:
  echo.
  git status --short
  echo.
  echo   Kane prota commit i stash, alliws mporei na xathoun.
  echo.
  pause
  exit /b 1
)

echo   [1/4] Katevazw ta panta apo to GitHub...
git fetch --all --prune
if errorlevel 1 goto :neterror

echo.
echo   [2/4] Enimerwnw to diko sou branch (!MINE!)...
git merge --ff-only "origin/!MINE!"
if errorlevel 1 (
  echo.
  echo   [!] To !MINE! den paei mprosta me fast-forward.
  echo       Exeis dika sou commits pou den exoun anevei. Kane:  git push origin !MINE!
  echo.
)

REM --- Ti exei to allo branch pou den exoume ------------------------
echo.
echo   [3/4] Ti exei to !THEIRS! pou den exeis...
git rev-parse --verify "origin/!THEIRS!" >nul 2>&1
if errorlevel 1 (
  echo         To branch !THEIRS! den yparxei sto GitHub - to prospernaw.
  goto :done
)

set "COUNT=0"
for /f %%n in ('git rev-list --count "HEAD..origin/!THEIRS!"') do set "COUNT=%%n"

if "!COUNT!"=="0" (
  echo         Tipota kainourio. Eisai enimeros.
  goto :done
)

echo.
git log --oneline --no-merges "HEAD..origin/!THEIRS!"
echo.
echo   !COUNT! commit^(s^) apo to !THEIRS!.
echo.
set "ANS="
set /p "ANS=  Na ta ferw sto !MINE!; (y/n): "
if /i not "!ANS!"=="y" (
  echo         Entaxei, den ta efera.
  goto :done
)

echo.
echo   [4/4] Kanw merge to origin/!THEIRS!...
git merge --no-edit "origin/!THEIRS!"
if errorlevel 1 (
  echo.
  echo   [!] Sygkroush - dyo anthropoi allaksan tin idia grammi.
  echo       Anoixe ta arxeia pou leei to git status, dialekse ti krataei,
  echo       kai meta:   git add .   ^&^&   git commit
  echo       Akyrwsi:    git merge --abort
  echo.
  pause
  exit /b 1
)

echo.
echo   Egine merge. Mi ksexaseis na to anebaseis wste na to dei kai o allos:
echo       git push origin !MINE!
echo.

:done
echo.
echo   ------------------------------------------------------------
git log --oneline -1
echo   ------------------------------------------------------------
echo.
echo   Teleutaio vima - to Chrome den diavazei mono tou ta nea arxeia:
echo.
echo     Anoixe to JobHunter  ^>  Rythmiseis  ^>  Enimerwseis
echo     kai pata "Efarmogi enimerwsis".
echo.
pause
exit /b 0

:neterror
echo.
echo   [!] Den mporesa na syndetho sto GitHub. Elegkse to internet sou.
echo.
pause
exit /b 1
