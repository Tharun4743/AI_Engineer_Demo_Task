@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM AI_Engineer_Demo_Task - Autonomous AI Competitive Intelligence Pipeline
REM Execution Launcher (Windows Batch Script)
REM ==============================================================================

title AI_Engineer_Demo_Task

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Set PYTHONPATH so src/ modules resolve reliably
set "PYTHONPATH=%SCRIPT_DIR%"

REM Determine Python executable (virtual environment first, then system python)
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    set "PYTHON_CMD=%SCRIPT_DIR%venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

REM Verify Python is accessible
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH.
    echo Please install Python 3.10+ or activate your virtual environment.
    exit /b 1
)

REM Handle command arguments
set "CMD=%~1"

if "%CMD%"=="" goto MENU
if /i "%CMD%"=="all" goto CLI_ALL
if /i "%CMD%"=="phase1" goto CLI_PHASE1
if /i "%CMD%"=="phase2" goto CLI_PHASE2
if /i "%CMD%"=="export" goto CLI_EXPORT
if /i "%CMD%"=="test" goto CLI_TEST
if /i "%CMD%"=="verify" goto CLI_VERIFY
if /i "%CMD%"=="pdf" goto CLI_PDF
if /i "%CMD%"=="help" goto USAGE
goto INVALID_ARG

:MENU
cls
echo ==============================================================================
echo   AI_ENGINEER_DEMO_TASK - AUTONOMOUS AI INTELLIGENCE PIPELINE
echo   Live Sheet: https://docs.google.com/spreadsheets/d/1NBvDUVfU9koTYhPR03eda0DGdKY3Hix9xAFDsDEUAcY/edit?usp=sharing
echo   Repository: https://github.com/Tharun4743/AI_Engineer_Demo_Task
echo ==============================================================================
echo.
echo   [1] Run Full Pipeline (Phase 1 + Phase 2 + Export)
echo   [2] Run Phase 1: Foundational Intelligence (Startups, Products, Papers)
echo   [3] Run Phase 2: Real-Time 24h Signals (News, Jobs)
echo   [4] Run Data Export (Google Sheets + CSV Backups)
echo   [5] Run Full Regression Test Suite (18 Pytest Tests)
echo   [6] Run Acceptance Verification (Definition of Done Audit)
echo   [7] Recompile Architecture PDF (architecture.pdf)
echo   [0] Exit
echo.
echo ==============================================================================
set /p "CHOICE=Enter selection [0-7]: "

if "%CHOICE%"=="1" goto MENU_ALL
if "%CHOICE%"=="2" goto MENU_PHASE1
if "%CHOICE%"=="3" goto MENU_PHASE2
if "%CHOICE%"=="4" goto MENU_EXPORT
if "%CHOICE%"=="5" goto MENU_TEST
if "%CHOICE%"=="6" goto MENU_VERIFY
if "%CHOICE%"=="7" goto MENU_PDF
if "%CHOICE%"=="0" exit /b 0
echo [ERROR] Invalid selection.
timeout /t 2 >nul
goto MENU

:MENU_ALL
call :DO_ALL
pause
goto MENU

:MENU_PHASE1
call :DO_PHASE1
pause
goto MENU

:MENU_PHASE2
call :DO_PHASE2
pause
goto MENU

:MENU_EXPORT
call :DO_EXPORT
pause
goto MENU

:MENU_TEST
call :DO_TEST
pause
goto MENU

:MENU_VERIFY
call :DO_VERIFY
pause
goto MENU

:MENU_PDF
call :DO_PDF
pause
goto MENU

REM --- Non-Interactive CLI targets ---
:CLI_ALL
call :DO_ALL
exit /b %errorlevel%

:CLI_PHASE1
call :DO_PHASE1
exit /b %errorlevel%

:CLI_PHASE2
call :DO_PHASE2
exit /b %errorlevel%

:CLI_EXPORT
call :DO_EXPORT
exit /b %errorlevel%

:CLI_TEST
call :DO_TEST
exit /b %errorlevel%

:CLI_VERIFY
call :DO_VERIFY
exit /b %errorlevel%

:CLI_PDF
call :DO_PDF
exit /b %errorlevel%

REM --- Task Implementations ---
:DO_ALL
echo.
echo [INFO] Executing Full Intelligence Pipeline (Phase 1 + Phase 2 + Export)...
%PYTHON_CMD% src/main.py all
if %errorlevel% neq 0 (
    echo [ERROR] Full pipeline run encountered an error.
    exit /b %errorlevel%
)
echo.
echo [INFO] Running automated Definition of Done acceptance verification...
%PYTHON_CMD% scripts/verify_output.py
exit /b %errorlevel%

:DO_PHASE1
echo.
echo [INFO] Executing Phase 1: Foundational Data Acquisition...
%PYTHON_CMD% src/main.py phase1
exit /b %errorlevel%

:DO_PHASE2
echo.
echo [INFO] Executing Phase 2: Real-Time Temporal Ingestion (^<=24h)...
%PYTHON_CMD% src/main.py phase2
exit /b %errorlevel%

:DO_EXPORT
echo.
echo [INFO] Exporting datasets to Google Sheets and local CSV backups...
%PYTHON_CMD% src/main.py export
exit /b %errorlevel%

:DO_TEST
echo.
echo [INFO] Executing full automated pytest regression test suite...
%PYTHON_CMD% -m pytest tests/ -v
exit /b %errorlevel%

:DO_VERIFY
echo.
echo [INFO] Executing Definition of Done (DoD) acceptance verification...
%PYTHON_CMD% scripts/verify_output.py
exit /b %errorlevel%

:DO_PDF
echo.
echo [INFO] Recompiling architecture.pdf (strictly 3 pages)...
%PYTHON_CMD% scripts/generate_pdf.py
%PYTHON_CMD% -c "import pypdf; r=pypdf.PdfReader('architecture.pdf'); print(f'Compiled Page Count: {len(r.pages)}'); assert len(r.pages) ^<= 3, 'Exceeds 3 pages!'"
exit /b %errorlevel%

:USAGE
echo.
echo Usage: run.bat [COMMAND]
echo.
echo Available Commands:
echo   all       Execute Phase 1, Phase 2, and Data Export sequentially
echo   phase1    Acquire Startups (^>=1,000), Products (^>=1,000), Papers (^>=1,000)
echo   phase2    Ingest real-time News and Jobs (100%% ^<=24h fresh across 5 sources)
echo   export    Sync database to 6-tab Google Sheet and export output/*.csv
echo   test      Execute 18/18 pytest test cases
echo   verify    Run Definition of Done automated audit
echo   pdf       Recompile 3-page architecture.pdf via ReportLab
echo.
exit /b 0

:INVALID_ARG
echo [ERROR] Unknown argument '%CMD%'. Run 'run.bat help' for usage instructions.
exit /b 1
