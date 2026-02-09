@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM Project 2 - Unified Dev Server
REM ============================================================================
REM
REM Usage:
REM   start.bat              - Start all 3 services (unified output)
REM   start.bat infra        - Start infrastructure first, then services
REM   start.bat stop         - Stop all services
REM   start.bat status       - Check service statuses
REM
REM ============================================================================

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo   ======================================================
echo     E-COMMERCE PLATFORM  -  DEV SERVER
echo   ======================================================
echo.
echo     NESTJS    http://localhost:8000   API Backend
echo     NEXTJS    http://localhost:3000   Frontend
echo     ML        http://localhost:8001   ML Service
echo.
echo   ======================================================
echo.

if "%1"=="stop" goto :stop
if "%1"=="status" goto :status
if "%1"=="infra" goto :infra
goto :start

REM --- Infrastructure -------------------------------------------------------

:infra
echo   Starting infrastructure (Docker)...
echo.
cd /d "%ROOT%infrastructure"
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   FAILED - Is Docker Desktop running?
    pause
    exit /b 1
)
echo.
echo   Infrastructure up. Waiting 10s for databases...
timeout /t 10 /nobreak >nul
cd /d "%ROOT%"
echo.

REM --- Start Services -------------------------------------------------------

:start
if not exist "%ROOT%node_modules\.bin\concurrently.cmd" (
    echo   Installing concurrently...
    call bun install
    echo.
)

echo   Press Ctrl+C to stop all services
echo.
echo   --------------------------------------------------------
echo.

"%ROOT%node_modules\.bin\concurrently.cmd" --pad-prefix --kill-others-on-fail -p [{name}] -n NESTJS,NEXTJS,ML -c red.bold,cyan.bold,magenta.bold "cd nestjs-backend && bun run start:dev" "cd frontend && bun run dev" "cd ml-services && .venv\Scripts\python -m uvicorn main:app --reload --port=8001"
goto :eof

REM --- Stop Services --------------------------------------------------------

:stop
echo   Stopping services...
echo.
for %%p in (8000 3000 8001) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%%p.*LISTENING"') do (
        echo     Stopping PID %%a on :%%p
        taskkill /F /PID %%a >nul 2>&1
    )
)
echo.
echo   All services stopped.
echo.
pause
goto :eof

REM --- Status ---------------------------------------------------------------

:status
echo   Checking ports...
echo.
for %%p in (8000 3000 8001 8002 5432 27017 6379 8085 29092 8086 5050) do (
    netstat -aon 2>nul | findstr ":%%p.*LISTENING" >nul 2>&1
    if !errorlevel!==0 (
        echo     :%%p   UP
    ) else (
        echo     :%%p   --
    )
)
echo.
pause
goto :eof
