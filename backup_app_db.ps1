<#
  Save as: backup_app_db.ps1
  Purpose: Daily backup of database/app.db with rolling retention (keep latest 30)
#>

# Resolve paths relative to this script file
$Root      = Split-Path -Parent $PSCommandPath
$DbPath    = Join-Path $Root 'database\app.db'
$BackupDir = Join-Path $Root 'database\backups'

# 1) Ensure backup directory exists
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# 2) Copy app.db with timestamped name
if (-not (Test-Path $DbPath)) {
  Write-Error "Database file not found: $DbPath"
  exit 1
}
$ts        = Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupDst = Join-Path $BackupDir ("app_{0}.db" -f $ts)
Copy-Item -Path $DbPath -Destination $BackupDst -Force

# 3) Rolling retention: keep latest 30 backups
try {
  Get-ChildItem -Path $BackupDir -Filter 'app_*.db' -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 30 |
    Remove-Item -Force
} catch {
  Write-Warning "Retention cleanup warning: $($_.Exception.Message)"
}


