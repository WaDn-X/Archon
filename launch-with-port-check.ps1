# Zippy-Archon Launch Script with Port Conflict Resolution (PowerShell)
# This script checks for port conflicts and resolves them before launching

param(
    [string]$Mode = "full",
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$NC = "White"

function Write-Colored {
    param([string]$Color, [string]$Message)
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-Colored $Blue "[INFO] $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Colored $Green "[SUCCESS] $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Colored $Yellow "[WARNING] $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Colored $Red "[ERROR] $Message"
}

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonSrcDir = Join-Path $ScriptDir "python\src"
$PortManagerScript = Join-Path $PythonSrcDir "utils\port_manager.py"
$PortConfigFile = Join-Path $ScriptDir ".zippy-archon-ports.json"

# Check if Python is available
function Test-Python {
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python is available: $pythonVersion"
            return $true
        }
    }
    catch {
        Write-Error "Python is not available in PATH"
        return $false
    }

    try {
        $python3Version = & python3 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python 3 is available: $python3Version"
            return $true
        }
    }
    catch {
        Write-Error "Python 3 is not available in PATH"
        return $false
    }

    Write-Error "Python is not installed. Please install Python 3.8 or higher."
    return $false
}

# Check for port conflicts and resolve them
function Test-AndResolve-Ports {
    Write-Info "Checking for port conflicts..."

    try {
        $result = & python $PortManagerScript --check --resolve 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Port conflicts resolved successfully"
            return $true
        }
        else {
            Write-Error "Failed to resolve port conflicts"
            Write-Host $result
            return $false
        }
    }
    catch {
        Write-Error "Error running port scanner: $_"
        return $false
    }
}

# Load port configuration if available
function Load-PortConfig {
    if (Test-Path $PortConfigFile) {
        Write-Info "Loading port configuration from $PortConfigFile"

        try {
            $config = Get-Content $PortConfigFile -Raw | ConvertFrom-Json
            $allocations = $config.allocations

            foreach ($envVar in $allocations.PSObject.Properties.Name) {
                $allocation = $allocations.$envVar
                $port = $allocation.allocated_port
                if ($port) {
                    $env:$envVar = $port
                    Write-Host "Set $envVar=$port"
                }
            }
        }
        catch {
            Write-Warning "Could not load port config: $_"
        }
    }
}

# Validate environment
function Test-Environment {
    Write-Info "Validating environment..."

    $requiredVars = @("SUPABASE_URL", "SUPABASE_SERVICE_KEY")
    $missingVars = @()

    foreach ($var in $requiredVars) {
        if (-not (Get-Variable -Name $var -ErrorAction SilentlyContinue)) {
            $missingVars += $var
        }
    }

    if ($missingVars.Count -gt 0) {
        Write-Error "Required environment variables are not set: $($missingVars -join ', ')"
        Write-Info "Please set them in your .env file or as system environment variables"
        return $false
    }

    Write-Success "Environment validation passed"
    return $true
}

# Start services based on mode
function Start-Services {
    param([string]$ServiceMode)

    Write-Info "Starting $ServiceMode services..."

    try {
        switch ($ServiceMode) {
            "full" {
                & docker-compose up -d
            }
            "backend" {
                & docker-compose --profile backend up -d
            }
            "frontend" {
                & docker-compose --profile frontend up -d
            }
            "monitoring" {
                & docker-compose --profile monitoring up -d
            }
            default {
                Write-Error "Unknown mode: $ServiceMode"
                Write-Info "Available modes: full, backend, frontend, monitoring"
                return $false
            }
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Services started successfully"
            return $true
        }
        else {
            Write-Error "Failed to start services"
            return $false
        }
    }
    catch {
        Write-Error "Error starting services: $_"
        return $false
    }
}

# Wait for services to be healthy
function Wait-ForHealth {
    Write-Info "Waiting for services to become healthy..."

    $maxAttempts = 60
    $attempt = 1
    $serverPort = $env:ARCHON_SERVER_PORT
    $uiPort = $env:ARCHON_UI_PORT

    if (-not $serverPort) { $serverPort = "8181" }
    if (-not $uiPort) { $uiPort = "3737" }

    while ($attempt -le $maxAttempts) {
        Write-Info "Health check attempt $attempt/$maxAttempts"

        try {
            # Check server health
            $serverResponse = Invoke-WebRequest -Uri "http://localhost:$serverPort/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($serverResponse.StatusCode -eq 200) {
                # Check frontend health
                $uiResponse = Invoke-WebRequest -Uri "http://localhost:$uiPort" -TimeoutSec 5 -ErrorAction SilentlyContinue
                if ($uiResponse.StatusCode -eq 200) {
                    Write-Success "All services are healthy!"
                    return $true
                }
            }
        }
        catch {
            # Services not ready yet, continue waiting
        }

        Start-Sleep -Seconds 5
        $attempt++
    }

    Write-Warning "Services may not be fully healthy after $maxAttempts attempts"
    Write-Info "You can check service status with: docker-compose ps"
    return $true
}

# Show service URLs
function Show-ServiceUrls {
    $serverPort = $env:ARCHON_SERVER_PORT
    $uiPort = $env:ARCHON_UI_PORT
    $grafanaPort = $env:GRAFANA_PORT
    $prometheusPort = $env:PROMETHEUS_PORT

    if (-not $serverPort) { $serverPort = "8181" }
    if (-not $uiPort) { $uiPort = "3737" }
    if (-not $grafanaPort) { $grafanaPort = "3827" }
    if (-not $prometheusPort) { $prometheusPort = "9090" }

    Write-Success "Services are running!"
    Write-Host ""
    Write-Host "Service URLs:" -ForegroundColor $Green
    Write-Host "  Frontend (React UI):    http://localhost:$uiPort" -ForegroundColor $Blue
    Write-Host "  API Server (FastAPI):   http://localhost:$serverPort" -ForegroundColor $Blue
    Write-Host "  API Documentation:     http://localhost:$serverPort/docs" -ForegroundColor $Blue
    Write-Host "  Health Check:          http://localhost:$serverPort/health" -ForegroundColor $Blue
    Write-Host "  Grafana Dashboards:    http://localhost:$grafanaPort" -ForegroundColor $Blue
    Write-Host "  Prometheus Metrics:    http://localhost:$prometheusPort" -ForegroundColor $Blue
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor $Yellow
    Write-Host "  View logs:      docker-compose logs -f" -ForegroundColor $NC
    Write-Host "  Stop services:  docker-compose down" -ForegroundColor $NC
    Write-Host "  Restart:        docker-compose restart" -ForegroundColor $NC
    Write-Host ""
}

# Main launch function
function Start-Launch {
    Write-Info "Starting Zippy-Archon with port conflict resolution..."

    # Show help if requested
    if ($Help) {
        Write-Host "Zippy-Archon Launch Script" -ForegroundColor $Green
        Write-Host ""
        Write-Host "This script will automatically:" -ForegroundColor $Blue
        Write-Host "  ✓ Check for port conflicts and resolve them" -ForegroundColor $Blue
        Write-Host "  ✓ Validate environment configuration" -ForegroundColor $Blue
        Write-Host "  ✓ Start the specified services" -ForegroundColor $Blue
        Write-Host "  ✓ Wait for services to become healthy" -ForegroundColor $Blue
        Write-Host ""
        Write-Host "Usage: .\launch-with-port-check.ps1 [-Mode <full|backend|frontend|monitoring>] [-Help]" -ForegroundColor $Yellow
        Write-Host ""
        Write-Host "Modes:" -ForegroundColor $Yellow
        Write-Host "  full       - Start all services (default)" -ForegroundColor $NC
        Write-Host "  backend    - Start only backend services" -ForegroundColor $NC
        Write-Host "  frontend   - Start only frontend" -ForegroundColor $NC
        Write-Host "  monitoring - Start only monitoring stack" -ForegroundColor $NC
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor $Yellow
        Write-Host "  .\launch-with-port-check.ps1" -ForegroundColor $NC
        Write-Host "  .\launch-with-port-check.ps1 -Mode backend" -ForegroundColor $NC
        Write-Host "  .\launch-with-port-check.ps1 -Mode monitoring" -ForegroundColor $NC
        return
    }

    # Validate mode
    $validModes = @("full", "backend", "frontend", "monitoring")
    if ($Mode -notin $validModes) {
        Write-Error "Invalid mode: $Mode"
        Write-Info "Valid modes are: $($validModes -join ', ')"
        return
    }

    # Run checks and setup
    if (-not (Test-Python)) { return }
    Load-PortConfig
    if (-not (Test-AndResolve-Ports)) { return }
    if (-not (Test-Environment)) { return }

    # Start services
    if (-not (Start-Services -ServiceMode $Mode)) { return }
    if (-not (Wait-ForHealth)) {
        Write-Warning "Continuing despite health check issues..."
    }
    Show-ServiceUrls

    Write-Success "Zippy-Archon is now running successfully!"
}

# Run the launch function
Start-Launch
