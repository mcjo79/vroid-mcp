<#
.SYNOPSIS
  Installeur graphique du pont VRoid (Claude Code / DeepSeek Harness).

.DESCRIPTION
  Interface WinForms sans dépendance : choisit le dossier de VRoid Studio (détection
  Steam, ou parcours manuel si elle échoue), le dossier du serveur MCP, et lance
  install.ps1 en affichant sa sortie en direct.

  La version ligne de commande reste disponible : Installer.cmd (ou install.ps1).
  Ce script ne fait que préparer les arguments et afficher la progression.

.EXAMPLE
  .\Installer-GUI.ps1
#>
param(
    [string]$GameDir,          # pré-remplit le dossier de VRoid (sinon détection Steam)
    [string]$McpDir            # pré-remplit le dossier du serveur
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallScript = Join-Path $Here "install.ps1"
[System.Windows.Forms.Application]::EnableVisualStyles()

# --- détection de VRoid Studio (même logique que install.ps1) -----------------
function Find-VRoid {
    $libs = New-Object System.Collections.Generic.List[string]
    foreach ($key in @("HKCU:\Software\Valve\Steam", "HKLM:\SOFTWARE\WOW6432Node\Valve\Steam", "HKLM:\SOFTWARE\Valve\Steam")) {
        try {
            $p = Get-ItemProperty -Path $key -ErrorAction Stop
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

function Test-GameDir($path) {
    return ($path -and (Test-Path (Join-Path $path "VRoidStudio.exe")))
}

# --- fenêtre -----------------------------------------------------------------
$form = New-Object System.Windows.Forms.Form
$form.Text = "VRoid - installation du pont IA"
$form.ClientSize = New-Object System.Drawing.Size(660, 560)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$font = New-Object System.Drawing.Font("Segoe UI", 9)
$form.Font = $font

$y = 14
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "Connecter votre IA a VRoid Studio"
$lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$lblTitle.AutoSize = $true
$lblTitle.Location = New-Object System.Drawing.Point(16, $y)
$form.Controls.Add($lblTitle)
$y += 34

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Installe le plugin dans VRoid, le serveur local, et declare le connecteur dans vos assistants."
$lblSub.AutoSize = $true
$lblSub.ForeColor = [System.Drawing.Color]::DimGray
$lblSub.Location = New-Object System.Drawing.Point(18, $y)
$form.Controls.Add($lblSub)
$y += 30

function New-PathRow($caption, $defaultValue, $y) {
    $lbl = New-Object System.Windows.Forms.Label
    $lbl.Text = $caption
    $lbl.AutoSize = $true
    $lbl.Location = New-Object System.Drawing.Point(18, ($y + 4))
    $form.Controls.Add($lbl)

    $box = New-Object System.Windows.Forms.TextBox
    $box.Text = $defaultValue
    $box.Location = New-Object System.Drawing.Point(18, ($y + 22))
    $box.Width = 520
    $form.Controls.Add($box)

    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = "Parcourir..."
    $btn.Location = New-Object System.Drawing.Point(546, ($y + 20))
    $btn.Width = 96
    $form.Controls.Add($btn)
    return @{ Box = $box; Button = $btn; Label = $lbl }
}

$gameDefault = if ($GameDir) { $GameDir } else { Find-VRoid }
$rowGame = New-PathRow "Dossier de VRoid Studio" $gameDefault $y
$y += 58
$mcpDefault = if ($McpDir) { $McpDir } else { Join-Path $env:LOCALAPPDATA "VRoidMcp" }
$rowMcp = New-PathRow "Dossier du serveur (donnees locales)" $mcpDefault $y
$y += 58

$rowGame.Button.Add_Click({
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Choisissez le dossier qui contient VRoidStudio.exe"
    if ($rowGame.Box.Text -and (Test-Path $rowGame.Box.Text)) { $dlg.SelectedPath = $rowGame.Box.Text }
    if ($dlg.ShowDialog() -eq "OK") { $rowGame.Box.Text = $dlg.SelectedPath }
})
$rowMcp.Button.Add_Click({
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Choisissez le dossier du serveur MCP"
    if (Test-Path $rowMcp.Box.Text) { $dlg.SelectedPath = $rowMcp.Box.Text }
    if ($dlg.ShowDialog() -eq "OK") { $rowMcp.Box.Text = $dlg.SelectedPath }
})

$chkBepInEx = New-Object System.Windows.Forms.CheckBox
$chkBepInEx.Text = "Reinstaller BepInEx meme s'il est deja present"
$chkBepInEx.AutoSize = $true
$chkBepInEx.Location = New-Object System.Drawing.Point(20, $y)
$form.Controls.Add($chkBepInEx)
$y += 26

$chkClaude = New-Object System.Windows.Forms.CheckBox
$chkClaude.Text = "Connecter Claude Code / Claude Desktop"
$chkClaude.Checked = $true
$chkClaude.AutoSize = $true
$chkClaude.Location = New-Object System.Drawing.Point(20, $y)
$form.Controls.Add($chkClaude)
$y += 26

$chkDsh = New-Object System.Windows.Forms.CheckBox
$chkDsh.Text = "Connecter DeepSeek Harness"
$chkDsh.Checked = $true
$chkDsh.AutoSize = $true
$chkDsh.Location = New-Object System.Drawing.Point(20, $y)
$form.Controls.Add($chkDsh)
$y += 34

$btnInstall = New-Object System.Windows.Forms.Button
$btnInstall.Text = "Installer"
$btnInstall.Location = New-Object System.Drawing.Point(18, $y)
$btnInstall.Width = 120
$btnInstall.Height = 30
$form.Controls.Add($btnInstall)

$btnUninstall = New-Object System.Windows.Forms.Button
$btnUninstall.Text = "Desinstaller"
$btnUninstall.Location = New-Object System.Drawing.Point(146, $y)
$btnUninstall.Width = 120
$btnUninstall.Height = 30
$form.Controls.Add($btnUninstall)

$btnClose = New-Object System.Windows.Forms.Button
$btnClose.Text = "Fermer"
$btnClose.Location = New-Object System.Drawing.Point(546, $y)
$btnClose.Width = 96
$btnClose.Height = 30
$form.Controls.Add($btnClose)
$y += 42

$log = New-Object System.Windows.Forms.RichTextBox
$log.Location = New-Object System.Drawing.Point(18, $y)
$log.Size = New-Object System.Drawing.Size(624, 190)
$log.ReadOnly = $true
$log.Font = New-Object System.Drawing.Font("Consolas", 8.5)
$log.BackColor = [System.Drawing.Color]::FromArgb(250, 250, 250)
$log.WordWrap = $false
$form.Controls.Add($log)

$status = New-Object System.Windows.Forms.StatusStrip
$statusLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
$statusLabel.Text = "Prêt."
$status.Items.Add($statusLabel) | Out-Null
$form.Controls.Add($status)

# --- exécution ---------------------------------------------------------------
$script:proc = $null
$script:logFile = $null
$script:read = 0

function Set-Busy($busy) {
    foreach ($c in @($btnInstall, $btnUninstall, $rowGame.Button, $rowMcp.Button, $chkBepInEx, $chkClaude, $chkDsh, $rowGame.Box, $rowMcp.Box)) {
        $c.Enabled = -not $busy
    }
    $btnClose.Enabled = $true
    if ($busy) { $statusLabel.Text = "Installation en cours..." } else { $statusLabel.Text = "Prêt." }
}

function Start-Install([bool]$uninstall, [bool]$removeBepInEx = $false, [bool]$removeData = $false) {
    if (-not (Test-GameDir $rowGame.Box.Text)) {
        [System.Windows.Forms.MessageBox]::Show("Ce dossier ne contient pas VRoidStudio.exe.`n`nUtilisez 'Parcourir...' pour indiquer le dossier de VRoid Studio.", "Dossier invalide", "OK", "Warning") | Out-Null
        return
    }

    $log.Clear()
    $script:read = 0
    $script:logFile = Join-Path $env:TEMP ("vroid_install_" + [guid]::NewGuid().ToString("N") + ".log")
    try {
        @(
            "Commande : $InstallScript",
            "VRoid : $($rowGame.Box.Text)",
            "Donnees : $($rowMcp.Box.Text)",
            "Date : $(Get-Date -Format o)",
            ""
        ) | Set-Content -Path $script:logFile -Encoding UTF8
    } catch { }

    $argv = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $InstallScript,
              "-GameDir", $rowGame.Box.Text, "-McpDir", $rowMcp.Box.Text)
    if ($uninstall) { $argv += "-Uninstall" }
    if ($removeBepInEx) { $argv += "-RemoveBepInEx" }
    if ($removeData) { $argv += "-RemoveData" }
    if ($chkBepInEx.Checked) { $argv += "-ForceBepInEx" }
    if (-not $chkClaude.Checked) { $argv += "-NoClaude" }
    if (-not $chkDsh.Checked) { $argv += "-NoDsh" }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $psi.Arguments = ($argv | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join " "
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8

    $script:proc = New-Object System.Diagnostics.Process
    $script:proc.StartInfo = $psi
    $script:outQueue = New-Object 'System.Collections.Concurrent.ConcurrentQueue[string]'
    $script:proc.add_OutputDataReceived({ param($sender, $e) if ($null -ne $e.Data) { $script:outQueue.Enqueue($e.Data) } })
    $script:proc.add_ErrorDataReceived({ param($sender, $e) if ($null -ne $e.Data) { $script:outQueue.Enqueue($e.Data) } })
    $script:proc.Start() | Out-Null
    $script:proc.BeginOutputReadLine()
    $script:proc.BeginErrorReadLine()
    Set-Busy $true
}

function Flush-Output {
    # Les handlers stdout/stderr remplissent une file thread-safe : le timer UI ne
    # fait jamais de ReadLine bloquant, sinon la fenêtre passe en "Ne répond pas".
    if ($script:outQueue -eq $null) { return }
    $line = $null
    while ($script:outQueue.TryDequeue([ref]$line)) {
        if ($null -ne $line) {
            $log.AppendText($line + "`r`n")
            $log.ScrollToCaret()
            try { Add-Content -Path $script:logFile -Value $line -Encoding UTF8 } catch { }
        }
    }
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 250
$timer.Add_Tick({
    if ($script:proc -eq $null) { return }
    Flush-Output
    if ($script:proc.HasExited) {
        Flush-Output
        $code = $script:proc.ExitCode
        $timer.Stop()
        Set-Busy $false
        $script:proc = $null
        if ($code -eq 0) {
            $statusLabel.Text = "Termine."
            [System.Windows.Forms.MessageBox]::Show("Installation terminee.`n`nJournal : $script:logFile`n`nRedemarrez Claude Code / DeepSeek Harness pour voir les outils vroid.", "VRoid", "OK", "Information") | Out-Null
        } else {
            $statusLabel.Text = "Echec (code $code) - journal conserve."
            [System.Windows.Forms.MessageBox]::Show("Echec de l'operation (code $code).`n`nLe journal est conserve ici :`n$script:logFile`n`nLa fenetre reste ouverte.", "VRoid", "OK", "Error") | Out-Null
        }
    }
})
$timer.Start()

$btnInstall.Add_Click({ Start-Install $false })
$btnUninstall.Add_Click({
    $r = [System.Windows.Forms.MessageBox]::Show(
        "Retirer le plugin de VRoid et les declarations dans les assistants ?",
        "Desinstaller", "YesNo", "Question")
    if ($r -ne "Yes") { return }

    $rb = [System.Windows.Forms.MessageBox]::Show(
        "Supprimer aussi BepInEx et ses sauvegardes ?`n`nAttention : BepInEx peut contenir d'autres plugins.`nChoisir Non conserve BepInEx.",
        "BepInEx", "YesNoCancel", "Question",
        [System.Windows.Forms.MessageBoxDefaultButton]::Button2)
    if ($rb -eq "Cancel") { return }

    $rd = [System.Windows.Forms.MessageBox]::Show(
        "Supprimer aussi le serveur MCP, le runtime Python et le cache des presets ?`n`nChoisir Non conserve ces donnees locales.",
        "Donnees locales", "YesNoCancel", "Question",
        [System.Windows.Forms.MessageBoxDefaultButton]::Button2)
    if ($rd -eq "Cancel") { return }

    Start-Install $true ($rb -eq "Yes") ($rd -eq "Yes")
})
$btnClose.Add_Click({ $form.Close() })
$form.Add_FormClosing({
    if ($script:proc -ne $null) {
        if ([System.Windows.Forms.MessageBox]::Show("Une installation est en cours. Quitter quand meme ?", "VRoid", "YesNo", "Warning") -ne "Yes") {
            $_.Cancel = $true
        }
    }
})

$form.AcceptButton = $btnInstall
[void]$form.ShowDialog()
