@echo off
setlocal enabledelayedexpansion

REM ---------------------------------------------------------------------
REM  To cmd diavazei to .bat kathws to ektelei, oxi mia kai kali sto
REM  ksekinima. Auto to arxeio zei mesa sto repo, ara to idio to update
REM  boroi na to allaksei sti mesi - kai apo ekei kai pera to cmd
REM  diavazei skoupidia. Gi' auto trexoume ena antigrafo apo to %TEMP%.
REM ---------------------------------------------------------------------
if /i not "%~1"=="--copy" (
  set "SELF=%TEMP%\jobhunter-update-%RANDOM%.bat"
  copy /y "%~f0" "!SELF!" >nul
  call "!SELF!" --copy "%~dp0"
  del "!SELF!" >nul 2>&1
  exit /b
)

cd /d "%~2"
title JobHunter - update

echo.
echo   JobHunter - update
echo   ==================
echo.

REM --- Eimaste se repository; ------------------------------------------
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto :norepo

REM --- Xwris tautotita, kathe commit skaei -----------------------------
set "GEMAIL="
for /f "delims=" %%e in ('git config user.email 2^>nul') do set "GEMAIL=%%e"
if not defined GEMAIL goto :noidentity

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "MINE=%%b"
if /i "!MINE!"=="main" ( set "THEIRS=Apo" ) else ( set "THEIRS=main" )

echo   Eisai sto branch: !MINE!
echo   To allo branch  : !THEIRS!
echo.

REM --- Adiavastes allages: den ta patame -------------------------------
git diff --quiet
if errorlevel 1 goto :dirty
git diff --cached --quiet
if errorlevel 1 goto :dirty

echo   [1/4] Katevazw ta panta apo to GitHub...
git fetch --all --prune
if errorlevel 1 goto :neterror

echo.
echo   [2/4] Enimerwnw to diko sou branch (!MINE!)...
git merge --ff-only "origin/!MINE!"
if errorlevel 1 goto :notff
goto :step3

:notff
echo.
echo   [*] To !MINE! den paei mprosta mono tou.
echo       Exeis dika sou commits pou den exoun anevei akoma:
echo         git push origin !MINE!
echo.

:step3
echo.
echo   [3/4] Ti exei to !THEIRS! pou den exeis...
git rev-parse --verify "origin/!THEIRS!" >nul 2>&1
if errorlevel 1 goto :nobranch

set "COUNT=0"
for /f %%n in ('git rev-list --count "HEAD..origin/!THEIRS!"') do set "COUNT=%%n"
if "!COUNT!"=="0" goto :uptodate

echo.
git log --oneline "HEAD..origin/!THEIRS!"
echo.
echo   !COUNT! commit^(s^) apo to !THEIRS!.
echo.
set "ANS="
set /p "ANS=  Na ta ferw sto !MINE!; (y/n): "
if /i not "!ANS!"=="y" goto :declined

echo.
echo   [4/4] Kanw merge to origin/!THEIRS!...
git merge --no-edit "origin/!THEIRS!"
if errorlevel 1 goto :mergefail

echo.
echo   Egine merge. Anevase to gia na to dei kai o allos:
echo       git push origin !MINE!
goto :done

:uptodate
echo         Tipota kainourio. Eisai plirws enimeros.
goto :done

:nobranch
echo         To branch !THEIRS! den yparxei sto GitHub - to prospernaw.
goto :done

:declined
echo.
echo         Entaxei, den efera tipota.
goto :done

REM --- Sygkroush i kati allo; Rotame to git, den mantevoume ------------
:mergefail
set "CONFLICTS="
for /f "delims=" %%f in ('git diff --name-only --diff-filter^=U 2^>nul') do set "CONFLICTS=1"
echo.
if defined CONFLICTS goto :conflict

echo   [*] To merge den oloklirwthike, alla den einai sygkroush arxeiwn.
echo       Diavase to minima tou git parapanw - synithws leei akrivws ti leipei.
echo       Gia na girisoun ola opws itan:  git merge --abort
echo.
pause
exit /b 1

:conflict
echo   [*] Sygkroush - allaksate kai oi dyo tin idia grammi.
echo.
echo       Arxeia pou theloun apofasi:
git diff --name-only --diff-filter=U
echo.
echo       Anoixe to kathena. To git exei valei mesa treis grammes-simadia:
echo         efta symvola "mikrotero"  = arxi tis dikis sou ekdosis
echo         efta symvola "ison"       = xwrisma
echo         efta symvola "megalytero" = arxi tis dikis tou ekdosis
echo.
echo       Krata oti prepei, svise tis treis grammes-simadia, kai meta:
echo         git add .
echo         git commit
echo.
echo       An theleis na to akyrwseis teleiws:
echo         git merge --abort
echo.
pause
exit /b 1

:dirty
echo   [*] Exeis alages pou den exoun ginei commit:
echo.
git status --short
echo.
echo       Kane prota commit:    git add .   kai meta   git commit -m "perigrafi"
echo       I vale tes stin akri: git stash
echo.
pause
exit /b 1

:noidentity
echo   [*] To git den xerei poios eisai, kai den mporei na kanei commit.
echo       Trekse mia fora auta ta dyo, me ta dika sou stoixeia:
echo.
echo         git config --global user.name "To Onoma Sou"
echo         git config --global user.email "to@email.sou"
echo.
echo       Meta ksanatrekse auto to arxeio.
echo.
pause
exit /b 1

:norepo
echo   [*] Autos o fakelos den einai git repository.
echo       Trekse prota:
echo         git clone https://github.com/GeorgasP/jobhunter.git
echo.
pause
exit /b 1

:neterror
echo.
echo   [*] Den mporesa na syndetho sto GitHub.
echo       Elegkse to internet sou kai an exeis prosvasi sto repository.
echo.
pause
exit /b 1

:done
echo.
echo   ------------------------------------------------------------
git log --oneline -1
echo   ------------------------------------------------------------
echo.
echo   Teleutaio vima - to Chrome den diavazei mono tou ta nea arxeia:
echo.
echo     Anoixe to JobHunter  ^>  Rythmiseis  ^>  Enimerwseis
echo     kai pata "Efarmogi enimerwsis"
echo.
echo     (isodynama: chrome://extensions  ^>  Reload sto JobHunter)
echo.
pause
exit /b 0
