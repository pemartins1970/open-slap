param(
  [switch]$BuildFrontend
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Resolve-Path -LiteralPath (Join-Path $root "..")
if ($BuildFrontend.IsPresent) {
  Push-Location (Join-Path $proj "src\frontend")
  npm run build | Out-Host
  Pop-Location
}
Push-Location $proj
& (Join-Path $root "verify_package.ps1") -Root "."
$code = $LASTEXITCODE
Pop-Location
exit $code
