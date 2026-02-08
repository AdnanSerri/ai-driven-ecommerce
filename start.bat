@echo off
REM ============================================================================
REM Project 2 - Start Script (Windows)
REM ============================================================================
REM Starts both Laravel and ML Service in separate terminal windows
REM
REM Usage:
REM   start.bat           - Start Laravel and ML Service only
REM   start.bat infra     - Start infrastructure first, then apps
REM   start.bat all       - Same as 'infra'
REM ============================================================================

echo.
echo ========================================
echo   Project 2 - E-commerce Platform
echo ========================================
echo.

REM Check if infrastructure should be started
if "%1"=="infra" goto :start_infra
if "%1"=="all" goto :start_infra
goto :start_apps

:start_infra
echo [1/3] Starting Infrastructure (Docker)...
echo.
cd /d "%~dp0infrastructure"
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start infrastructure. Is Docker running?
    pause
    exit /b 1
)
echo.
echo Infrastructure started! Waiting 10 seconds for databases...
timeout /t 10 /nobreak >nul
echo.

:start_apps
echo [2/3] Starting Laravel Backend (port 8000)...
start "Laravel Backend" cmd /k "cd /d "%~dp0backend" && php artisan serve --port=8000"

echo [3/3] Starting ML Service (port 8001)...
timeout /t 2 /nobreak >nul
start "ML Service" cmd /k "cd /d "%~dp0ml-services" && .venv\Scripts\activate && uvicorn main:app --reload --port=8001"

echo.
echo ========================================
echo   All services starting!
echo ========================================
echo.
echo   Laravel:     http://localhost:8000
echo   ML Service:  http://localhost:8001
echo   Kafka UI:    http://localhost:8086
echo   pgAdmin:     http://localhost:5050
echo.
echo   Press any key to close this window...
echo   (Services will continue running)
echo.
pause >nul
