param(
  [string]$Root = "."
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$rootPath = Resolve-Path -LiteralPath $Root
$forbiddenPatterns = @(
  "*.map",
  ".env",
  "*.db",
  "*.sqlite"
)
$forbiddenDirs = @(
  "node_modules",
  "__pycache__",
  "data"
)
$violations = @()
Get-ChildItem -LiteralPath $rootPath -Recurse -Force | ForEach-Object {
  $p = $_.FullName
  foreach ($d in $forbiddenDirs) {
    if ($_.PSIsContainer -and $_.Name -eq $d) {
      $violations += $p
      break
    }
    if ($p -like "*\$d\*") {
      $violations += $p
      break
    }
  }
  if (-not $_.PSIsContainer) {
    foreach ($pat in $forbiddenPatterns) {
      if ($_ .Name -like $pat) {
        $violations += $p
        break
      }
    }
  }
}
if ($violations.Count -gt 0) {
  Write-Host "Forbidden artifacts found:" -ForegroundColor Red
  $violations | Sort-Object | Get-Unique | ForEach-Object { Write-Host $_ }
  exit 1
}
Write-Host "OK: no forbidden artifacts." -ForegroundColor Green
exit 0
