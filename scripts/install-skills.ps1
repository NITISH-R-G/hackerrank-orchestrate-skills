# Install the Orchestrate skills into an agent's skills folder.
#
#   scripts/install-skills.ps1                  # Claude Code: $HOME\.claude\skills
#   scripts/install-skills.ps1 -Dest <folder>   # any other harness's skills folder
#
# Copies every skills\<name>\ folder. Existing folders with the same name are
# replaced. Nothing outside those folders is touched.
param(
    [string]$Dest = (Join-Path $HOME ".claude\skills")
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

Get-ChildItem -Directory (Join-Path $here "skills") | ForEach-Object {
    $target = Join-Path $Dest $_.Name
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    Copy-Item -Recurse $_.FullName $target
    Write-Output "installed $($_.Name) -> $target"
}
$count = (Get-ChildItem -Directory $Dest -Filter "orchestrate*").Count
Write-Output "done. $Dest now has $count orchestrate skills."
