# ============================================================================
# Project 2 - Unified Dev Server
# ============================================================================
#
# Usage:
#   .\start.ps1                - Start all 3 services (unified output)
#   .\start.ps1 -Infra         - Start infrastructure first, then services
#   .\start.ps1 -Stop          - Stop all services
#   .\start.ps1 -Status        - Check all service statuses
#
# ============================================================================

param(
    [switch]$Infra,
    [switch]$Stop,
    [switch]$Status
)

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# --- Helpers ----------------------------------------------------------------

function Test-Port {
    param([int]$Port)
    try {
        $tcp = [System.Net.Sockets.TcpClient]::new()
        $tcp.Connect("127.0.0.1", $Port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

function Write-StatusLine {
    param([string]$Name, [int]$Port, [string]$Desc)
    $pad = " " * (14 - $Name.Length)
    $running = Test-Port $Port
    if ($running) {
        Write-Host "    $Name$pad" -NoNewline
        Write-Host "UP" -ForegroundColor Green -NoNewline
        Write-Host "      :$Port   $Desc" -ForegroundColor DarkGray
    } else {
        Write-Host "    $Name$pad" -NoNewline
        Write-Host "--" -ForegroundColor DarkGray -NoNewline
        Write-Host "      :$Port   $Desc" -ForegroundColor DarkGray
    }
}

# --- Banner -----------------------------------------------------------------

function Write-Banner {
    Write-Host ""
    Write-Host "  ========================================================" -ForegroundColor Cyan
    Write-Host "                                                          " -ForegroundColor Cyan
    Write-Host "          E-COMMERCE PLATFORM  -  DEV SERVER              " -ForegroundColor Cyan
    Write-Host "                                                          " -ForegroundColor Cyan
    Write-Host "  ========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "    " -NoNewline
    Write-Host "NESTJS" -ForegroundColor Red -NoNewline
    Write-Host "    http://localhost:8000   " -ForegroundColor White -NoNewline
    Write-Host "API Backend" -ForegroundColor DarkGray
    Write-Host "    " -NoNewline
    Write-Host "NEXTJS" -ForegroundColor Cyan -NoNewline
    Write-Host "    http://localhost:3000   " -ForegroundColor White -NoNewline
    Write-Host "Frontend" -ForegroundColor DarkGray
    Write-Host "    " -NoNewline
    Write-Host "ML    " -ForegroundColor Magenta -NoNewline
    Write-Host "    http://localhost:8001   " -ForegroundColor White -NoNewline
    Write-Host "ML Service" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  ========================================================" -ForegroundColor Cyan
    Write-Host ""
}

# --- Infrastructure ---------------------------------------------------------

function Start-Infrastructure {
    Write-Host "  Starting infrastructure..." -ForegroundColor Yellow
    Write-Host ""
    Set-Location "$ProjectRoot\infrastructure"
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  FAILED - Is Docker Desktop running?" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    Write-Host "  Infrastructure up. Waiting 10s for databases..." -ForegroundColor Green
    Start-Sleep -Seconds 10
    Set-Location $ProjectRoot
    Write-Host ""
}

# --- Status -----------------------------------------------------------------

function Show-Status {
    Write-Host ""
    Write-Host "  Services" -ForegroundColor White
    Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
    Write-StatusLine "NestJS"     8000  "API Backend"
    Write-StatusLine "Next.js"    3000  "Frontend"
    Write-StatusLine "ML Service" 8001  "ML Microservice"
    Write-StatusLine "Laravel"    8002  "Admin Panel (Docker)"
    Write-Host ""
    Write-Host "  Infrastructure" -ForegroundColor White
    Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
    Write-StatusLine "PostgreSQL" 5432  ""
    Write-StatusLine "MongoDB"    27017 ""
    Write-StatusLine "Redis"      6379  ""
    Write-StatusLine "Weaviate"   8085  ""
    Write-StatusLine "Kafka"      29092 ""
    Write-StatusLine "Kafka UI"   8086  ""
    Write-StatusLine "pgAdmin"    5050  ""
    Write-Host ""
}

# --- Stop -------------------------------------------------------------------

function Stop-AllServices {
    Write-Host ""
    Write-Host "  Stopping services..." -ForegroundColor Yellow
    Write-Host ""

    $ports = @(8000, 3000, 8001)
    foreach ($port in $ports) {
        $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "    Stopping $($proc.ProcessName) on :$port" -ForegroundColor DarkGray
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }

    Write-Host ""
    Write-Host "  All services stopped." -ForegroundColor Green
    Write-Host ""
}

# --- Install ----------------------------------------------------------------

function Install-Dependencies {
    if (!(Test-Path "$ProjectRoot\node_modules\.bin\concurrently.cmd")) {
        Write-Host "  Installing concurrently..." -ForegroundColor Yellow
        bun install --cwd "$ProjectRoot" 2>$null
        Write-Host ""
    }
}

# --- Launch -----------------------------------------------------------------

function Start-Services {
    Install-Dependencies

    Write-Host "  Press " -ForegroundColor DarkGray -NoNewline
    Write-Host "Ctrl+C" -ForegroundColor White -NoNewline
    Write-Host " to stop all services" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  --------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""

    & "$ProjectRoot\node_modules\.bin\concurrently.cmd" `
        --pad-prefix `
        --kill-others-on-fail `
        -p '[{name}]' `
        -n 'NESTJS,NEXTJS,ML' `
        -c 'red.bold,cyan.bold,magenta.bold' `
        "cd nestjs-backend && bun run start:dev" `
        "cd frontend && bun run dev" `
        "cd ml-services && .venv\Scripts\python -m uvicorn main:app --reload --port=8001"
}

# --- Main -------------------------------------------------------------------

Write-Banner

if ($Stop) {
    Stop-AllServices
    exit 0
}

if ($Status) {
    Show-Status
    exit 0
}

if ($Infra) {
    Start-Infrastructure
}

Start-Services
