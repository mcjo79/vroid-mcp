# Publication du site - a lancer seulement apres validation.
#
#   powershell -ExecutionPolicy Bypass -File website/publish.ps1        (simulation)
#   powershell -ExecutionPolicy Bypass -File website/publish.ps1 -Go    (commit + push)
#
# Le workflow .github/workflows/pages.yml publie ensuite website/ sur GitHub Pages.

[CmdletBinding()]
param(
    [switch]$Go
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host ""
Write-Host "VRoid MCP Bridge - publication du site" -ForegroundColor Cyan
Write-Host "Depot : $(git remote get-url origin)" -ForegroundColor DarkGray
Write-Host "Branche : $(git branch --show-current)" -ForegroundColor DarkGray
Write-Host ""

$status = @(git status --porcelain)
if ($status.Count -eq 0) {
    Write-Host "Rien a publier : le depot est deja a jour." -ForegroundColor Yellow
    exit 0
}

$unexpected = @()
foreach ($line in $status) {
    $path = $line.Substring(3).Trim('"')
    if ($path -eq 'website/' -or $path -like 'website/*' -or $path -eq '.github/' -or $path -eq '.github/workflows/pages.yml' -or $path -eq 'docs/CHARACTER_PROMPT.md' -or $path -eq 'docs/REFERENCE.md') { continue }
    $unexpected += $path
}

if ($unexpected.Count -gt 0) {
    Write-Warning "Des modifications hors du site sont presentes :"
    $unexpected | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host "Committez-les ou mettez-les de cote avant de publier le site." -ForegroundColor Yellow
    exit 1
}

Write-Host "Fichiers qui seraient publies :" -ForegroundColor White
$status | ForEach-Object { Write-Host "  $_" }
Write-Host ""

if (-not $Go) {
    Write-Host "Simulation terminee. Aucun commit, aucun push." -ForegroundColor Green
    Write-Host "Pour publier apres validation :" -ForegroundColor White
    Write-Host "  powershell -ExecutionPolicy Bypass -File website/publish.ps1 -Go" -ForegroundColor DarkGray
    exit 0
}

git add website .github/workflows/pages.yml docs/CHARACTER_PROMPT.md docs/REFERENCE.md
git commit -m "Site web du projet" -m "- Site bilingue EN/FR dans website/ : anglais par defaut, francais dans fr/, selecteur de langue." -m "- Test de personnage, 34 outils, installation, coulisses, FAQ." -m "- Brief du test dans docs/CHARACTER_PROMPT.md." -m "- Reference MCP regeneree (0.10.0, 34 outils)." -m "- Workflow GitHub Pages pour publier website/."

Write-Host ""
Write-Host "Push vers origin/main..." -ForegroundColor Cyan
git push origin main

Write-Host ""
Write-Host "Publie. GitHub Actions construit le site." -ForegroundColor Green
Write-Host "Site :    https://mcjo79.github.io/vroid-mcp/" -ForegroundColor White
Write-Host "Actions : https://github.com/mcjo79/vroid-mcp/actions" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Si Pages n'est pas encore active : Settings -> Pages -> Source : GitHub Actions." -ForegroundColor Yellow
Write-Host "Pensez aussi a renseigner l'URL du site dans l'onglet About du depot." -ForegroundColor Yellow
