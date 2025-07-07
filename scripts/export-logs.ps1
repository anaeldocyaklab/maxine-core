# Export Docker Container Logs Script
# This script exports logs from all containers defined in docker-compose.yml

param(
    [string]$OutputDir = "logs",
    [string]$TimestampFormat = "yyyy-MM-dd_HH-mm-ss",
    [switch]$IncludeTimestamps = $true,
    [int]$TailLines = 0  # 0 means all logs, otherwise specify number of recent lines
)

# Create logs directory if it doesn't exist (relative to script location)
$LogsPath = Join-Path (Split-Path $PSScriptRoot -Parent) $OutputDir
if (-not (Test-Path $LogsPath)) {
    New-Item -ItemType Directory -Path $LogsPath -Force
    Write-Host "Created logs directory: $LogsPath" -ForegroundColor Green
}

# Get timestamp for this export session
$Timestamp = Get-Date -Format $TimestampFormat
$SessionDir = Join-Path $LogsPath "export_$Timestamp"
New-Item -ItemType Directory -Path $SessionDir -Force

Write-Host "Exporting container logs to: $SessionDir" -ForegroundColor Yellow

# Define containers from your docker-compose.yml
$Containers = @("ollama", "searxng", "agent")

foreach ($Container in $Containers) {
    Write-Host "Exporting logs for container: $Container" -ForegroundColor Cyan
    
    # Check if container exists and is running
    $ContainerExists = docker ps -a --filter "name=$Container" --format "{{.Names}}" | Where-Object { $_ -eq $Container }
    
    if ($ContainerExists) {
        $LogFile = Join-Path $SessionDir "$Container.log"
        
        try {
            if ($TailLines -gt 0) {
                if ($IncludeTimestamps) {
                    docker logs --timestamps --tail $TailLines $Container > $LogFile
                } else {
                    docker logs --tail $TailLines $Container > $LogFile
                }
                Write-Host "  ✓ Exported last $TailLines lines to: $LogFile" -ForegroundColor Green
            } else {
                if ($IncludeTimestamps) {
                    docker logs --timestamps $Container > $LogFile
                } else {
                    docker logs $Container > $LogFile
                }
                Write-Host "  ✓ Exported all logs to: $LogFile" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "  ✗ Failed to export logs for $Container`: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠ Container '$Container' not found" -ForegroundColor Yellow
    }
}

# Export docker-compose logs as well (combined view)
Write-Host "Exporting combined docker-compose logs..." -ForegroundColor Cyan
$CombinedLogFile = Join-Path $SessionDir "docker-compose-combined.log"

try {
    # Change to the parent directory to run docker-compose commands
    Push-Location (Split-Path $PSScriptRoot -Parent)
    
    if ($TailLines -gt 0) {
        if ($IncludeTimestamps) {
            docker-compose logs --timestamps --tail=$TailLines > $CombinedLogFile
        } else {
            docker-compose logs --tail=$TailLines > $CombinedLogFile
        }
    } else {
        if ($IncludeTimestamps) {
            docker-compose logs --timestamps > $CombinedLogFile
        } else {
            docker-compose logs > $CombinedLogFile
        }
    }
    Write-Host "  ✓ Exported combined logs to: $CombinedLogFile" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Failed to export combined logs: $_" -ForegroundColor Red
}
finally {
    Pop-Location
}

# Create a summary file
$SummaryFile = Join-Path $SessionDir "export-summary.txt"
$Summary = @"
Docker Container Logs Export Summary
===================================
Export Date: $(Get-Date)
Export Directory: $SessionDir
Containers Exported: $($Containers -join ", ")
Include Timestamps: $IncludeTimestamps
Tail Lines: $(if ($TailLines -gt 0) { $TailLines } else { "All" })

Files Generated:
"@

Get-ChildItem $SessionDir -Filter "*.log" | ForEach-Object {
    $Size = [math]::Round($_.Length / 1KB, 2)
    $Summary += "`n- $($_.Name) ($Size KB)"
}

$Summary | Out-File -FilePath $SummaryFile -Encoding UTF8
Write-Host "`nExport completed! Summary saved to: $SummaryFile" -ForegroundColor Green
Write-Host "Total files exported: $(Get-ChildItem $SessionDir -Filter '*.log' | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Green
