$c = Get-Content -LiteralPath ".\App_auth.jsx" -Raw;
$depth = 0;
$inStr = $false;
$inTmpl = $false;
$strCh = '';
$i = 0;
$len = $c.Length;
while ($i -lt $len) {
  $ch = $c[$i];
  $next = if ($i + 1 -lt $len) { $c[$i+1] } else { '' };
  if ($inStr) {
    if ($ch -eq '\' -and ($next -eq $strCh -or $next -eq '\')) { $i += 2; continue };
    if ($ch -eq $strCh) { $inStr = $false };
    $i++; continue
  };
  if ($inTmpl) {
    if ($ch -eq '$' -and $next -eq '{') { $depth++; $i += 2; continue };
    if ($ch -eq '$') { $i++; continue };
    if ($ch -eq '}') { $depth--; $i++; continue };
    if ($ch -eq "`n" -or $ch -eq "`r") { $i++; continue };
    $i++; continue
  };
  if ($ch -eq "'" -or $ch -eq '"') { $inStr = $true; $strCh = $ch; $i++; continue };
  if ($ch -eq "``") { $inTmpl = $true; $i++; continue };
  if ($ch -eq '{' -and !$inTmpl) { $depth++ };
  if ($ch -eq '}' -and !$inTmpl) { $depth-- };
  $i++
};
Write-Host "Final depth: $depth"
