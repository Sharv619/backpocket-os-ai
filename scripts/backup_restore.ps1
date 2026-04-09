param (
    [string]$Action = "backup",   # "backup" or "restore"
    [string]$TargetFolder = ""    # If restoring, specify the backup timestamp folder like "backup_20260404"
)

$ScriptsPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootPath = Resolve-Path (Join-Path $ScriptsPath "..")
$BackupRoot = Join-Path $RootPath "backups"

# Ensure backups directory exists
if (-not (Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot | Out-Null
}

if ($Action -eq "backup") {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $DestFolder = Join-Path $BackupRoot "backup_$Timestamp"
    New-Item -ItemType Directory -Path $DestFolder | Out-Null
    
    Write-Host "Creating backup in $DestFolder..." -ForegroundColor Cyan

    # 1. Backup Core Python Files
    Copy-Item (Join-Path $RootPath "main.py") $DestFolder
    Copy-Item (Join-Path $RootPath "services") $DestFolder -Recurse

    # 2. Backup Database (Safely copy)
    $DBPath = Join-Path $RootPath "backpocket.db"
    if (Test-Path $DBPath) {
        Copy-Item $DBPath $DestFolder
    }

    # 3. Backup UI
    Copy-Item (Join-Path $RootPath "static") $DestFolder -Recurse

    # 4. Backup Documentation (All docs!)
    $DocsPath = Join-Path $RootPath "docs"
    if (Test-Path $DocsPath) {
        Copy-Item $DocsPath $DestFolder -Recurse
    }

    # 5. Backup Session Logs (Critical for context!)
    Copy-Item (Join-Path $RootPath "SESSION_LOG.md") $DestFolder -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $RootPath "OPENCODE_CONTEXT.md") $DestFolder -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $RootPath "AGENTS.md") $DestFolder -ErrorAction SilentlyContinue

    # 6. Backup Config
    $EnvPath = Join-Path $RootPath ".env"
    if (Test-Path $EnvPath) {
        Copy-Item $EnvPath $DestFolder
    }

    Write-Host "✅ Backup Completed Successfully!" -ForegroundColor Green
}
elseif ($Action -eq "restore") {
    if ([string]::IsNullOrEmpty($TargetFolder)) {
        Write-Host "Please specify a TargetFolder. Ex: .\backup_restore.ps1 -Action restore -TargetFolder backup_20260404_120000" -ForegroundColor Red
        return
    }

    $SourceFolder = Join-Path $BackupRoot $TargetFolder
    if (-not (Test-Path $SourceFolder)) {
        Write-Host "Backup folder not found: $SourceFolder" -ForegroundColor Red
        return
    }

    Write-Host "Restoring from $SourceFolder..." -ForegroundColor Yellow

    # Copy files back to root, overwriting
    Copy-Item (Join-Path $SourceFolder "main.py") $RootPath -Force
    Copy-Item (Join-Path $SourceFolder "services") $RootPath -Recurse -Force
    Copy-Item (Join-Path $SourceFolder "static") $RootPath -Recurse -Force
    
    # Restore Docs
    $DocsSource = Join-Path $SourceFolder "docs"
    if (Test-Path $DocsSource) {
        Copy-Item $DocsSource $RootPath -Recurse -Force
    }
    
    $DBPath = Join-Path $SourceFolder "backpocket.db"
    if (Test-Path $DBPath) {
        Copy-Item $DBPath $RootPath -Force
    }

    Write-Host "✅ Restore Completed Successfully! Please restart your server." -ForegroundColor Green
}
else {
    Write-Host "Unknown action: $Action. Use 'backup' or 'restore'." -ForegroundColor Red
}
