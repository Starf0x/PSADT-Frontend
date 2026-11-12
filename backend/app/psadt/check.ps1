# Controleert alleen de syntax van een script met de PowerShell-parser; voert niets uit.
param([Parameter(Mandatory)][string]$Path)
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$null, [ref]$errors)
foreach ($e in $errors) { '{0}:{1} {2}' -f $e.Extent.StartLineNumber, $e.Extent.StartColumnNumber, $e.Message }
