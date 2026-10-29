<#
.SYNOPSIS
  Installe ou met à jour le pont MCP pour VRoid Studio (plugin BepInEx + serveur MCP).

.DESCRIPTION
  1. Trouve VRoid Studio (bibliothèques Steam) ou utilise -GameDir.
  2. Installe BepInEx 6.0.0-be.791 (IL2CPP) si absent ; remplace une autre version (BepInEx 5...) après
     sauvegarde ; laisse en place un BepInEx 6 déjà correct.
  3. Copie le plugin VRoidMcpBridge dans BepInEx\plugins.
  4. Copie le serveur MCP, le cache des presets, la documentation et les outils dans -McpDir
     (par défaut %LOCALAPPDATA%\VRoidMcp). Les annotations du cache déjà présentes sont conservées.
  5. Déclare le serveur MCP "vroid" dans Claude Code et Claude Desktop (sauf -NoClaude), avec sauvegarde.

.EXAMPLE
  .\install.ps1
  .\install.ps1 -GameDir "D:\SteamLibrary\steamapps\common\VRoid Studio"
  .\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$GameDir,
    [string]$McpDir = (Join-Path $env:LOCALAPPDATA "VRoidMcp"),
    [switch]$ForceBepInEx,
    [switch]$SkipBepInEx,
    [switch]$NoClaude,
    [switch]$Uninstall,
    [string]$BepInExZip   # archive BepInEx locale (hors ligne), sinon téléchargée
)

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

# Isolation du Python local : UTF-8, variables PYTHON* ignorées, site-packages utilisateur désactivé.
# Un Python 3.12 installé sur la machine ne peut donc pas influencer celui du paquet.
$script:pyFlags = @("-X", "utf8", "-E", "-s")

$BieVersion = "6.0.0-be.791"
$BieUrl = "https://builds.bepinex.dev/projects/bepinex_be/791/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.791%2Bb782da4.zip"
$BieSha256 = "bb1c510909b69522733791f3a0817a487379a52da6468a492f1c9c19b3ec6f9a"
$BieFiles = @("BepInEx", "dotnet", "winhttp.dll", "doorstop_config.ini", ".doorstop_version", "changelog.txt")

function Info($m) { Write-Host "  $m" }
function Step($m) { Write-Host ""; Write-Host "== $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "  ! $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host ""; Write-Host "ERREUR : $m" -ForegroundColor Red; exit 1 }

# ---------- VRoid Studio ----------
function Find-VRoid {
    $libs = New-Object System.Collections.Generic.List[string]
    foreach ($key in @("HKCU:\Software\Valve\Steam", "HKLM:\SOFTWARE\WOW6432Node\Valve\Steam", "HKLM:\SOFTWARE\Valve\Steam")) {
        try {
            $p = (Get-ItemProperty -Path $key -ErrorAction Stop)
            foreach ($n in @("SteamPath", "InstallPath")) { if ($p.$n) { $libs.Add(($p.$n -replace "/", "\")) } }
        } catch { }
    }
    foreach ($root in @($libs)) {
        $vdf = Join-Path $root "steamapps\libraryfolders.vdf"
        if (Test-Path $vdf) {
            foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
                $libs.Add(($m.Groups[1].Value -replace "\\\\", "\"))
            }
        }
    }
    foreach ($lib in ($libs | Select-Object -Unique)) {
        $d = Join-Path $lib "steamapps\common\VRoid Studio"
        if (Test-Path (Join-Path $d "VRoidStudio.exe")) { return $d }
    }
    return $null
}

# Lance Python sans que sa sortie d'erreur interrompe le script (comportement de PowerShell 5.1).
function Invoke-Py {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $script:python @script:pyFlags @args 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "^\s*$" } | ForEach-Object { Write-Host "  $_" } }
    finally { $ErrorActionPreference = $prev }
    return $LASTEXITCODE
}

function Find-Python {
    # Candidats : lanceur py (toutes versions installées), puis python/python3 du PATH.
    # Préférence à un Python 3 qui a déjà numpy et Pillow.
    $cands = New-Object System.Collections.Generic.List[string]
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            foreach ($l in (& py -0p 2>$null)) { if ($l -match "([A-Za-z]:\\.+python\.exe)") { $cands.Add($Matches[1].Trim()) } }
        }
        foreach ($c in @("python", "python3")) {
            $cmd = Get-Command $c -ErrorAction SilentlyContinue
            if ($cmd) {
                $exe = & $cmd.Source -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $exe) { $cands.Add($exe.Trim()) }
            }
        }
        $first = $null
        foreach ($exe in ($cands | Select-Object -Unique)) {
            if (-not (Test-Path $exe)) { continue }
            & $exe -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            if (-not $first) { $first = $exe }
            & $exe -c "import numpy, PIL" 2>$null
            if ($LASTEXITCODE -eq 0) { return $exe }
        }
        return $first
    } finally { $ErrorActionPreference = $prev }
}

function Find-BundledPython {
    # Python livré dans le paquet de release (python\python.exe). Prioritaire sur le Python système :
    # c'est ce qui évite à l'utilisateur d'installer quoi que ce soit.
    $p = Join-Path $Here "python\python.exe"
    if (Test-Path $p) { return $p }
    return $null
}

function Get-BieState($dir) {
    $il2cpp = Join-Path $dir "BepInEx\core\BepInEx.Unity.IL2CPP.dll"
    $core = Join-Path $dir "BepInEx\core\BepInEx.Core.dll"
    $bie5 = Join-Path $dir "BepInEx\core\BepInEx.dll"
    if ((Test-Path $il2cpp) -and (Test-Path $core)) {
        $v = (Get-Item $core).VersionInfo.ProductVersion
        if ($v -like "$BieVersion*") { return @{ State = "ok"; Version = $v } }
        return @{ State = "other6"; Version = $v }
    }
    if (Test-Path $bie5) {
        $v5 = (Get-Item $bie5).VersionInfo.ProductVersion
        if (-not $v5) { $v5 = "5 (version inconnue)" }
        return @{ State = "other"; Version = $v5 }
    }
    if (Test-Path (Join-Path $dir "BepInEx")) { return @{ State = "other"; Version = "inconnue" } }
    return @{ State = "none"; Version = $null }
}

function Install-BepInEx($dir) {
    $tmp = Join-Path $env:TEMP ("vroidmcp_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        $zip = $BepInExZip
        if (-not $zip) {
            $zip = Join-Path $tmp "bepinex.zip"
            Info "Téléchargement de BepInEx $BieVersion..."
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $old = $ProgressPreference; $ProgressPreference = "SilentlyContinue"
            Invoke-WebRequest -Uri $BieUrl -OutFile $zip -UseBasicParsing
            $ProgressPreference = $old
        }
        $sha = (Get-FileHash -Algorithm SHA256 $zip).Hash.ToLower()
        if ($sha -ne $BieSha256) { Fail "l'archive BepInEx n'a pas l'empreinte attendue ($sha)." }
        Info "Archive vérifiée (SHA-256)."
        $x = Join-Path $tmp "x"
        Expand-Archive -Path $zip -DestinationPath $x -Force
        Copy-Item -Path (Join-Path $x "*") -Destination $dir -Recurse -Force
        Info "BepInEx $BieVersion installé."
    } finally {
        Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    }
}

function Backup-BepInEx($dir) {
    $bak = Join-Path $dir ("BepInEx_sauvegarde_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    New-Item -ItemType Directory -Path $bak | Out-Null
    foreach ($f in $BieFiles) {
        $p = Join-Path $dir $f
        if (Test-Path $p) { Move-Item -Path $p -Destination $bak }
    }
    Info "Ancienne installation déplacée dans : $bak"
    Info "(ses plugins ne sont pas recopiés : ceux de BepInEx 5 ne fonctionnent pas avec BepInEx 6 IL2CPP)"
}

# ---------- Claude ----------
function Register-Claude($python, $server, [switch]$Remove) {
    $reg = Join-Path $Here "register_mcp.py"
    $targets = @((Join-Path $env:USERPROFILE ".claude.json"))
    $desktopDir = Join-Path $env:APPDATA "Claude"
    if (Test-Path $desktopDir) { $targets += (Join-Path $desktopDir "claude_desktop_config.json") }
    foreach ($t in $targets) {
        if ($Remove) { $rc = Invoke-Py $reg --remove $t } else { $rc = Invoke-Py $reg $t $python $server }
        if ($rc -ne 0) { Warn "échec de la mise à jour de $t" }
    }
}

# ================================================================
Write-Host "Pont MCP pour VRoid Studio - installation" -ForegroundColor Green

if (-not $GameDir) { $GameDir = Find-VRoid }
if (-not $GameDir -or -not (Test-Path (Join-Path $GameDir "VRoidStudio.exe"))) {
    Fail "VRoid Studio introuvable. Relancez avec -GameDir `"<dossier de VRoid Studio>`"."
}
Info "VRoid Studio : $GameDir"

if (Get-Process -Name "VRoidStudio" -ErrorAction SilentlyContinue) {
    Fail "VRoid Studio est ouvert. Enregistrez votre travail, fermez-le, puis relancez l'installation."
}

$pluginDir = Join-Path $GameDir "BepInEx\plugins\VRoidMcpBridge"
$script:bundledPython = $false
$script:python = Find-BundledPython
if ($script:python) {
    $script:bundledPython = $true
} else {
    $script:python = Find-Python
}
$python = $script:python

if ($Uninstall) {
    Step "Désinstallation"
    if (Test-Path $pluginDir) { Remove-Item -Recurse -Force $pluginDir; Info "Plugin retiré." }
    if ($python -and -not $NoClaude) { Register-Claude $python "" -Remove }
    Info "BepInEx et $McpDir sont laissés en place (à supprimer à la main si souhaité)."
    exit 0
}

Step "BepInEx"
if ($SkipBepInEx) {
    Info "Étape ignorée (-SkipBepInEx)."
} else {
    $st = Get-BieState $GameDir
    switch ($st.State) {
        "ok" {
            if ($ForceBepInEx) { Info "Réinstallation forcée."; Install-BepInEx $GameDir }
            else { Info "BepInEx $($st.Version) déjà installé : rien à faire." }
        }
        "other6" {
            if ($ForceBepInEx) { Backup-BepInEx $GameDir; Install-BepInEx $GameDir }
            else { Warn "BepInEx 6 $($st.Version) présent (version testée : $BieVersion). Conservé ; -ForceBepInEx pour le remplacer." }
        }
        "other" { Info "Version $($st.Version) trouvée : remplacement par BepInEx $BieVersion."; Backup-BepInEx $GameDir; Install-BepInEx $GameDir }
        "none" { Install-BepInEx $GameDir }
    }
}

Step "Plugin VRoidMcpBridge"
New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null
Copy-Item -Force (Join-Path $Here "plugin\VRoidMcpBridge.dll") $pluginDir
$pv = (Get-Item (Join-Path $pluginDir "VRoidMcpBridge.dll")).VersionInfo.FileVersion
Info "Installé dans $pluginDir"

Step "Serveur MCP"
New-Item -ItemType Directory -Force -Path $McpDir | Out-Null
foreach ($d in @("mcp_server", "tools", "docs", "config")) {
    $src = Join-Path $Here $d
    if (Test-Path $src) {
        New-Item -ItemType Directory -Force -Path (Join-Path $McpDir $d) | Out-Null
        Copy-Item -Recurse -Force (Join-Path $src "*") (Join-Path $McpDir $d)
    }
}
foreach ($f in @("README.md", "README-fr.md", "LICENSE", "THIRD_PARTY_NOTICES.md")) {
    $p = Join-Path $Here $f
    if (Test-Path $p) { Copy-Item -Force $p $McpDir }
}
# Python embarqué : copié dans $McpDir pour survivre à la suppression du dossier de release.
# Une mise à jour ne recopie que si la version livrée diffère de celle déjà en place.
if ($script:bundledPython) {
    $pySrc = Join-Path $Here "python"
    $pyDst = Join-Path $McpDir "python"
    $copyPy = $true
    if (Test-Path (Join-Path $pyDst "python.exe")) {
        $vSrc = (Get-Item (Join-Path $pySrc "python.exe")).VersionInfo.ProductVersion
        $vDst = (Get-Item (Join-Path $pyDst "python.exe")).VersionInfo.ProductVersion
        if ($vSrc -eq $vDst) { $copyPy = $false; Info "Python embarqué déjà en place ($vDst)." }
    }
    if ($copyPy) {
        if (Test-Path $pyDst) { Remove-Item -Recurse -Force $pyDst }
        Copy-Item -Recurse -Force $pySrc $pyDst
        Info "Python embarqué installé dans $pyDst"
    }
    $script:python = Join-Path $pyDst "python.exe"
    $python = $script:python
}
# Cache des presets : données locales, jamais fournies par la release. Un cache existant est conservé ;
# sinon il se remplit à l'usage (vroid_preset_cache_sync / vroid_preset_cache_build).
$cacheDst = Join-Path $McpDir "preset_cache"
$cacheSrc = Join-Path $Here "preset_cache"
if (Test-Path (Join-Path $cacheDst "catalog.json")) {
    Info "Cache des presets existant conservé."
    if ((Test-Path (Join-Path $cacheSrc "catalog.json")) -and $python) {
        Invoke-Py (Join-Path $Here "merge_cache.py") $cacheSrc $cacheDst | Out-Null
    }
} else {
    New-Item -ItemType Directory -Force -Path $cacheDst | Out-Null
    Info "Cache des presets vide créé (il se remplit à l'usage)."
}
$server = Join-Path $McpDir "mcp_server\vroid_mcp.py"
Info "Serveur : $server"

Step "Python et Claude"
if (-not $python) {
    Warn "Python 3 introuvable : installez-le (https://www.python.org) puis relancez l'installation."
} else {
    Info "Python : $python"
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    & $python @script:pyFlags -c "import numpy, PIL" 2>&1 | Out-Null
    $hasLibs = ($LASTEXITCODE -eq 0); $ErrorActionPreference = $prev
    if (-not $hasLibs) {
        Info "Installation de numpy et Pillow (vignettes et textures)..."
        $rcLyb = Invoke-Py -m pip install --quiet --disable-pip-version-check --no-warn-script-location numpy pillow
        if ($rcLyb -eq 0) { Info "numpy et Pillow installés." }
        else {
            Warn "numpy et Pillow absents (vignettes et retouches de textures indisponibles). Pour les installer :"
            Warn "  `"$python`" -m pip install numpy pillow"
        }
    }
    if ($NoClaude) { Info "Déclaration dans Claude ignorée (-NoClaude)." }
    else { Register-Claude $python $server }
}

Step "Terminé"
Info "Plugin $pv installé. Au premier lancement après une installation de BepInEx, VRoid Studio met"
Info "une à deux minutes de plus à démarrer (génération des assemblages d'interopérabilité)."
Info "Vérification : VRoid ouvert, http://127.0.0.1:7811/status doit répondre."
Info "Redémarrez Claude Code / Claude Desktop pour voir les outils vroid_*."
