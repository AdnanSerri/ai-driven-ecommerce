@echo off
REM ============================================================================
REM Project 2 - Stop Script (Windows)
REM ============================================================================
REM Stops all services
REM
REM Usage:
REM   stop.bat           - Stop apps only (keep databases running)
REM   stop.bat all       - Stop everything including databases
REM ============================================================================

echo.
echo ========================================
echo   Stopping Project 2 Services
echo ========================================
echo.

REM Kill Laravel PHP processes
echo Stopping Laravel...
taskkill /F /IM php.exe /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   Laravel stopped.
) else (
    echo   Laravel was not running.
)

REM Kill Python/Uvicorn processes
echo Stopping ML Service...
taskkill /F /IM python.exe /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   ML Service stopped.
) else (
    echo   ML Service was not running.
)

REM Check if infrastructure should be stopped
if "%1"=="all" goto :stop_infra
if "%1"=="infra" goto :stop_infra
goto :done

:stop_infra
echo.
echo Stopping Infrastructure (Docker)...
cd /d "%~dp0infrastructure"
docker-compose down
echo   Infrastructure stopped.

:done
echo.
echo ========================================
echo   All services stopped!
echo ========================================
echo.
pause
