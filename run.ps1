<#
.SYNOPSIS
    All-in-One Launcher for the Enterprise Slack AI Agent.

.DESCRIPTION
    Checks if initial setup is needed:
    - If needed: automatically installs 'uv', downloads Python 3.12, creates directories,
      generates .env, synchronizes virtual environment dependencies, and starts the bot.
    - If already set up: instantly launches the bot with zero delay.
#>

[CmdletBinding()]
param(
    [switch]$SetupOnly,
    [switch]$Test,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

# ------------------------------------------------------------------------------
# 1. Project Root Directory
# ------------------------------------------------------------------------------
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# Ensure uv is in PATH if installed in user profile
$userBinPaths = @(
    (Join-Path $env:USERPROFILE '.local\bin'),
    (Join-Path $env:USERPROFILE '.cargo\bin')
)
foreach ($p in $userBinPaths) {
    $uvExe = Join-Path $p 'uv.exe'
    if (Test-Path $uvExe) {
        if ($env:PATH -notlike ('*' + $p + '*')) {
            $env:PATH = $p + ';' + $env:PATH
        }
        break
    }
}

# ------------------------------------------------------------------------------
# 2. Check If Setup Is Needed
# ------------------------------------------------------------------------------
$hasUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)
$hasVenv = Test-Path (Join-Path $ProjectRoot '.venv\Scripts\python.exe')
$hasEnvFile = Test-Path (Join-Path $ProjectRoot '.env')
$hasDataDir = Test-Path (Join-Path $ProjectRoot 'data\charts')

$isSetupNeeded = (-not $hasUv) -or (-not $hasVenv) -or (-not $hasEnvFile) -or (-not $hasDataDir)

# ------------------------------------------------------------------------------
# 3. Setup Routine (Only Executed If Needed)
# ------------------------------------------------------------------------------
if ($isSetupNeeded) {
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host '  First-Time Setup Detected -- Configuring Environment...   ' -ForegroundColor White
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host ''

    # Step A: Install 'uv' if not present
    if (-not $hasUv) {
        Write-Host "[1/5] Installing 'uv' package manager via astral.sh..." -ForegroundColor Gray
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        }
        catch {
            Write-Host "Failed to install 'uv' automatically: $_" -ForegroundColor Red
            Write-Host 'Please install uv manually: winget install astral-sh.uv' -ForegroundColor Yellow
            exit 1
        }

        foreach ($p in $userBinPaths) {
            $uvExe = Join-Path $p 'uv.exe'
            if (Test-Path $uvExe) {
                $env:PATH = $p + ';' + $env:PATH
                break
            }
        }
        Write-Host "      [OK] 'uv' installed successfully." -ForegroundColor Green
    } else {
        $uvVer = & uv --version 2>&1
        Write-Host "[1/5] Package Manager: $uvVer" -ForegroundColor Green
    }

    # Step B: Install Python 3.12 standalone runtime via uv
    Write-Host '[2/5] Ensuring Python 3.12 runtime is installed...' -ForegroundColor Gray
    & uv python install 3.12
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Warning: Could not install Python 3.12 automatically via uv.' -ForegroundColor Yellow
    } else {
        Write-Host '      [OK] Python 3.12 runtime ready.' -ForegroundColor Green
    }

    # Step C: Create runtime directories
    Write-Host '[3/5] Creating runtime storage directories (data/, data/charts/)...' -ForegroundColor Gray
    foreach ($d in @('data', 'data\charts')) {
        $fullPath = Join-Path $ProjectRoot $d
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }
    Write-Host '      [OK] Storage directories created.' -ForegroundColor Green

    # Step D: Initialize .env
    $envPath = Join-Path $ProjectRoot '.env'
    $envExamplePath = Join-Path $ProjectRoot '.env.example'
    if (-not (Test-Path $envPath)) {
        if (Test-Path $envExamplePath) {
            Copy-Item -Path $envExamplePath -Destination $envPath
            Write-Host '[4/5] Created .env from .env.example.' -ForegroundColor Yellow
        }
    } else {
        Write-Host '[4/5] .env file found.' -ForegroundColor Green
    }

    # Step E: Synchronize dependencies into .venv
    Write-Host '[5/5] Synchronizing dependencies into virtual environment (.venv)...' -ForegroundColor Gray
    & uv sync
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Dependency synchronization failed.' -ForegroundColor Red
        exit 1
    }
    Write-Host '      [OK] Setup complete!' -ForegroundColor Green
    Write-Host ''
}

# ------------------------------------------------------------------------------
# 4. Quick Credentials Check
# ------------------------------------------------------------------------------
$envFile = Join-Path $ProjectRoot '.env'
function Test-HasValidCredentials {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    $txt = Get-Content -Path $Path -Raw -ErrorAction SilentlyContinue
    if (-not $txt) { return $false }
    $hasBot = ($txt -match 'SLACK_BOT_TOKEN=xoxb-[a-zA-Z0-9_-]+')
    $hasApp = ($txt -match 'SLACK_APP_TOKEN=xapp-[a-zA-Z0-9_-]+')
    $hasKey = ($txt -match 'OPENROUTER_API_KEY=\S{10,}')
    return ($hasBot -and $hasApp -and $hasKey)
}

if (-not (Test-HasValidCredentials -Path $envFile)) {
    Write-Host '============================================================' -ForegroundColor Yellow
    Write-Host '  ACTION REQUIRED: Set your credentials in .env             ' -ForegroundColor Yellow
    Write-Host '============================================================' -ForegroundColor Yellow
    Write-Host 'Please configure the following in .env:' -ForegroundColor White
    Write-Host '  - SLACK_BOT_TOKEN    (starts with xoxb-...)' -ForegroundColor Cyan
    Write-Host '  - SLACK_APP_TOKEN    (starts with xapp-...)' -ForegroundColor Cyan
    Write-Host '  - OPENROUTER_API_KEY (from https://openrouter.ai/keys)' -ForegroundColor Cyan
    Write-Host ''

    if ([Environment]::UserInteractive) {
        $ans = Read-Host 'Open .env in Notepad now to edit? (Y/n)'
        if ($ans -eq '' -or $ans -match '^[yY]') {
            Start-Process notepad.exe -ArgumentList $envFile -Wait
        }
    }

    if (-not (Test-HasValidCredentials -Path $envFile)) {
        Write-Host 'Credentials not yet configured. Please edit .env and run .\run.ps1 again.' -ForegroundColor Yellow
        exit 0
    }
}

# ------------------------------------------------------------------------------
# 5. Handle Target Action
# ------------------------------------------------------------------------------
if ($SetupOnly) {
    Write-Host '[OK] Setup is verified and ready. Run .\run.ps1 to start.' -ForegroundColor Green
    exit 0
}

if ($Test) {
    Write-Host '[+] Running test suite...' -ForegroundColor Cyan
    & uv run pytest -v
    exit $LASTEXITCODE
}

if ($Check) {
    Write-Host '[+] Running code quality verification (Ruff + Mypy)...' -ForegroundColor Cyan
    & uv run ruff check .
    & uv run ruff format --check .
    & uv run mypy src/ tests/
    exit $LASTEXITCODE
}

# ------------------------------------------------------------------------------
# 6. Run Application
# ------------------------------------------------------------------------------
Write-Host '============================================================' -ForegroundColor Green
Write-Host '  Starting Slack AI Assistant... (Ctrl+C to stop)           ' -ForegroundColor White
Write-Host '============================================================' -ForegroundColor Green
Write-Host ''

& uv run python main.py
