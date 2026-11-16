# Model Autopsy production migration safety gate.
# Run locally on Windows with PostgreSQL 17 client tools installed.
# NEVER paste the DATABASE_URL into ChatGPT or commit backup files.
param(
    [string]$OutputDirectory = "./backups"
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL_PG)) {
    throw "Set DATABASE_URL_PG to a direct PostgreSQL connection URI securely in your shell; not the asyncpg URL."
}
if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    throw "pg_dump is unavailable. Install PostgreSQL 17 client tools before attempting a backup."
}
if (-not (Get-Command pg_restore -ErrorAction SilentlyContinue)) {
    throw "pg_restore is unavailable. Install PostgreSQL 17 client tools."
}

$dir = (New-Item -ItemType Directory -Path $OutputDirectory -Force).FullName
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = Join-Path $dir "model-autopsy-before-tenant-rls-$stamp.dump"
& pg_dump --dbname="$env:DATABASE_URL_PG" --format=custom --no-owner --no-acl --file="$backup" --verbose
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed; do not migrate." }
& pg_restore --list "$backup" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Backup integrity listing failed; do not migrate." }
$info = Get-Item "$backup"
if ($info.Length -lt 1024) { throw "Backup unexpectedly small; verify before migrating." }
$hash = (Get-FileHash -Algorithm SHA256 -Path "$backup").Hash
Write-Host "Backup created: $backup"
Write-Host "Size: $($info.Length) bytes"
Write-Host "SHA-256: $hash"
Write-Host "IMPORTANT: Test restore to a SEPARATE scratch PostgreSQL database before upgrading production."
Write-Host "Do not place a backup on GitHub or share it publicly."
