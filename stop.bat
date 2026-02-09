@echo off
setlocal

REM ============================================================================
REM Project 2 - Stop All Services
REM ============================================================================
REM
REM Usage:
REM   stop.bat           - Stop app services only
REM   stop.bat all       - Stop apps + infrastructure (Docker)
REM   stop.bat infra     - Stop infrastructure only
REM
REM ============================================================================

echo.
echo   ======================================================
echo     Stopping Project 2 Services
echo   ======================================================
echo.

if "%1"=="infra" goto :stop_infra

REM ─── Stop apps by port ──────────────────────────────────────

echo   Stopping applications...
echo.

for %%p in (8000 3000 8001) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%%p.*LISTENING"') do (
        echo     Stopping PID %%a on :%%p
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo.
echo   Applications stopped.

if not "%1"=="all" goto :done

REM ─── Stop infrastructure ────────────────────────────────────

:stop_infra
echo.
echo   Stopping infrastructure (Docker)...
cd /d "%~dp0infrastructure"
docker-compose down
echo   Infrastructure stopped.

:done
echo.
echo   ======================================================
echo     All done.
echo   ======================================================
echo.
pause
