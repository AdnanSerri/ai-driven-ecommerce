# ============================================================================
# Project 2 - Start Script (PowerShell)
# ============================================================================
# Starts both Laravel and ML Service in separate terminal windows
#
# Usage:
#   .\start.ps1              - Start Laravel and ML Service only
#   .\start.ps1 -Infra       - Start infrastructure first, then apps
#   .\start.ps1 -Stop        - Stop all services
#   .\start.ps1 -Status      - Check status of all services
# ============================================================================

param(
    [switch]$Infra,
    [switch]$Stop,
    [switch]$Status
)

$ProjectRoot = $PSScriptRoot

function Write-Header {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Project 2 - E-commerce Platform" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Start-Infrastructure {
    Write-Host "[1/3] Starting Infrastructure (Docker)..." -ForegroundColor Yellow
    Set-Location "$ProjectRoot\infrastructure"
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to start infrastructure. Is Docker running?" -ForegroundColor Red
        exit 1
    }
    Write-Host "Infrastructure started! Waiting 10 seconds for databases..." -ForegroundColor Green
    Start-Sleep -Seconds 10
    Set-Location $ProjectRoot
}

function Start-Laravel {
    Write-Host "[2/3] Starting Laravel Backend (port 8000)..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$ProjectRoot\backend`" && php artisan serve --port=8000" -WindowStyle Normal
}

function Start-MLService {
    Write-Host "[3/3] Starting ML Service (port 8001)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2

    # Check if .venv exists
    $venvPath = "$ProjectRoot\ml-services\.venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\ml-services'; & '.\.venv\Scripts\Activate.ps1'; uvicorn main:app --reload --port=8001" -WindowStyle Normal
    } else {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$ProjectRoot\ml-services`" && uvicorn main:app --reload --port=8001" -WindowStyle Normal
    }
}

function Stop-AllServices {
    Write-Host "Stopping all services..." -ForegroundColor Yellow

    # Stop Docker infrastructure
    Set-Location "$ProjectRoot\infrastructure"
    docker-compose down

    # Kill Laravel and Uvicorn processes
    Get-Process -Name "php" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*uvicorn*" } | Stop-Process -Force

    Write-Host "All services stopped." -ForegroundColor Green
    Set-Location $ProjectRoot
}

function Get-ServiceStatus {
    Write-Host "Checking service status..." -ForegroundColor Yellow
    Write-Host ""

    # Check Docker containers
    Write-Host "Docker Containers:" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "infra-"
    Write-Host ""

    # Check Laravel
    Write-Host "Laravel (port 8000): " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -ErrorAction SilentlyContinue
        Write-Host "Running" -ForegroundColor Green
    } catch {
        Write-Host "Not running" -ForegroundColor Red
    }

    # Check ML Service
    Write-Host "ML Service (port 8001): " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        Write-Host "Running" -ForegroundColor Green
    } catch {
        Write-Host "Not running" -ForegroundColor Red
    }
    Write-Host ""
}

function Show-URLs {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  All services starting!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Laravel:     " -NoNewline; Write-Host "http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  ML Service:  " -NoNewline; Write-Host "http://localhost:8001" -ForegroundColor Cyan
    Write-Host "  ML Docs:     " -NoNewline; Write-Host "http://localhost:8001/docs" -ForegroundColor Cyan
    Write-Host "  Kafka UI:    " -NoNewline; Write-Host "http://localhost:8086" -ForegroundColor Cyan
    Write-Host "  pgAdmin:     " -NoNewline; Write-Host "http://localhost:5050" -ForegroundColor Cyan
    Write-Host ""
}

# Main execution
Write-Header

if ($Stop) {
    Stop-AllServices
    exit 0
}

if ($Status) {
    Get-ServiceStatus
    exit 0
}

if ($Infra) {
    Start-Infrastructure
}

Start-Laravel
Start-MLService
Show-URLs
