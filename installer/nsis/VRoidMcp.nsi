; VRoid MCP Bridge - NSIS installer
;
; Built by installer/build_release.py:
;   makensis /DVERSION=0.12.0 /DPAYLOAD=<extracted release folder> /DOUTDIR=<dist> VRoidMcp.nsi
;
; The installer drives installer/install.ps1 (same logic as before), hidden, with its output in the
; progress window. Nothing to launch afterwards: no console, no .cmd.
;
; Silent install:   VRoidMcp-Setup-v<ver>.exe /S [/GAMEDIR=<VRoid Studio folder>] [/D=<install folder>]
;                   options: /NOCLAUDE /NODSH /FORCEBEPINEX
; Silent uninstall: Uninstall-VRoidMcp.exe /S [/REMOVEBEPINEX] [/REMOVECACHE]

Unicode true
ManifestDPIAware true

!ifndef VERSION
  !error "pass /DVERSION=x.y.z"
!endif
!ifndef PAYLOAD
  !error "pass /DPAYLOAD=<extracted release folder>"
!endif
!ifndef OUTDIR
  !define OUTDIR "."
!endif

!define APPNAME "VRoid MCP Bridge"
!define PUBLISHER "mcjo79"
!define URL "https://mcjo79.github.io/vroid-mcp/"
!define REGKEY "Software\VRoidMcp"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\VRoidMcp"
!define UNINSTEXE "Uninstall-VRoidMcp.exe"
!define PS '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass'

Name "${APPNAME} ${VERSION}"
OutFile "${OUTDIR}\VRoidMcp-Setup-v${VERSION}.exe"
InstallDir "$LOCALAPPDATA\VRoidMcp"
InstallDirRegKey HKCU "${REGKEY}" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUninstDetails show
BrandingText "${APPNAME} ${VERSION}"

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "${APPNAME} setup"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "LegalCopyright" "MIT License"

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

Var GameDir
Var Opts

; ---------------------------------------------------------------- pages
!define MUI_ABORTWARNING
!define MUI_LANGDLL_REGISTRY_ROOT HKCU
!define MUI_LANGDLL_REGISTRY_KEY "${REGKEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Language"
!define MUI_COMPONENTSPAGE_SMALLDESC

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS

!define MUI_PAGE_HEADER_TEXT "$(GameHeader)"
!define MUI_PAGE_HEADER_SUBTEXT "$(GameSubHeader)"
!define MUI_DIRECTORYPAGE_TEXT_TOP "$(GameTop)"
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "$(GameDest)"
!define MUI_DIRECTORYPAGE_VARIABLE $GameDir
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE GameDirLeave
!insertmacro MUI_PAGE_DIRECTORY

!define MUI_DIRECTORYPAGE_TEXT_TOP "$(InstTop)"
!insertmacro MUI_PAGE_DIRECTORY

!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_TITLE "$(FinishTitle)"
!define MUI_FINISHPAGE_TEXT "$(FinishText)"
!define MUI_FINISHPAGE_LINK "$(FinishLink)"
!define MUI_FINISHPAGE_LINK_LOCATION "${URL}"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\$(ReadmeFile)"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "$(FinishReadme)"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_RESERVEFILE_LANGDLL

!include "strings.nsh"

; ---------------------------------------------------------------- helpers
; Exit code 0 when VRoid Studio is not running.
!macro CheckVRoidClosed
  ${Do}
    nsExec::Exec '${PS} -Command "if (Get-Process -Name VRoidStudio -ErrorAction SilentlyContinue) { exit 1 }"'
    Pop $0
    ${If} $0 != 1
      ${ExitDo}
    ${EndIf}
    ${If} ${Cmd} `MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "$(VRoidRunning)" /SD IDCANCEL IDCANCEL`
      Abort "$(VRoidRunning)"
    ${EndIf}
  ${Loop}
!macroend

; ---------------------------------------------------------------- install
Section "$(SecBridge)" SecBridge
  SectionIn RO
  !insertmacro CheckVRoidClosed

  DetailPrint "$(Extracting)"
  SetDetailsPrint listonly
  SetOutPath "$PLUGINSDIR\payload"
  File /r "${PAYLOAD}\*.*"
  SetDetailsPrint both

  Call BuildOpts

  ; install.ps1 does the work (BepInEx, plugin, server, embedded Python, assistants).
  nsExec::ExecToLog /OEM '${PS} -File "$PLUGINSDIR\payload\install.ps1" -GameDir "$GameDir" -McpDir "$INSTDIR" -LogFile "$TEMP\VRoidMcp-install.log"$Opts'
  Pop $0
  ${If} $0 != 0
    SetOutPath "$TEMP"
    MessageBox MB_OK|MB_ICONSTOP "$(InstallFailed) ($0).$\r$\n$TEMP\VRoidMcp-install.log" /SD IDOK
    Abort "$(InstallFailed) ($0)"
  ${EndIf}

  ; Keep what the uninstaller needs (install.ps1 refuses to run without the plugin next to it).
  CreateDirectory "$INSTDIR\setup\plugin"
  CopyFiles /SILENT "$PLUGINSDIR\payload\install.ps1" "$INSTDIR\setup"
  CopyFiles /SILENT "$PLUGINSDIR\payload\register_mcp.py" "$INSTDIR\setup"
  CopyFiles /SILENT "$PLUGINSDIR\payload\register_dsh.py" "$INSTDIR\setup"
  CopyFiles /SILENT "$PLUGINSDIR\payload\merge_cache.py" "$INSTDIR\setup"
  CopyFiles /SILENT "$PLUGINSDIR\payload\plugin\VRoidMcpBridge.dll" "$INSTDIR\setup\plugin"
  SetOutPath "$INSTDIR"
  WriteUninstaller "$INSTDIR\${UNINSTEXE}"

  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\README.lnk" "$INSTDIR\$(ReadmeFile)"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\$(UninstallShortcut).lnk" "$INSTDIR\${UNINSTEXE}"

  WriteRegStr HKCU "${REGKEY}" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "${REGKEY}" "GameDir" "$GameDir"
  WriteRegStr HKCU "${REGKEY}" "Version" "${VERSION}"
  WriteRegStr HKCU "${UNINSTKEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "${UNINSTKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTKEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKCU "${UNINSTKEY}" "URLInfoAbout" "${URL}"
  WriteRegStr HKCU "${UNINSTKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTKEY}" "UninstallString" '"$INSTDIR\${UNINSTEXE}"'
  WriteRegStr HKCU "${UNINSTKEY}" "QuietUninstallString" '"$INSTDIR\${UNINSTEXE}" /S'
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  WriteRegDWORD HKCU "${UNINSTKEY}" "EstimatedSize" $0

  SetOutPath "$TEMP" ; release $PLUGINSDIR so it can be deleted
SectionEnd

Section "$(SecClaude)" SecClaude
SectionEnd

Section "$(SecDsh)" SecDsh
SectionEnd

Section /o "$(SecForceBie)" SecForceBie
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecBridge} "$(DescBridge)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecClaude} "$(DescClaude)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDsh} "$(DescDsh)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecForceBie} "$(DescForceBie)"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
  InitPluginsDir

  ; Command-line options (mostly for /S).
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/GAMEDIR=" $GameDir
  ${GetOptions} $R0 "/NOCLAUDE" $R1
  ${IfNot} ${Errors}
    !insertmacro UnselectSection ${SecClaude}
  ${EndIf}
  ClearErrors
  ${GetOptions} $R0 "/NODSH" $R1
  ${IfNot} ${Errors}
    !insertmacro UnselectSection ${SecDsh}
  ${EndIf}
  ClearErrors
  ${GetOptions} $R0 "/FORCEBEPINEX" $R1
  ${IfNot} ${Errors}
    !insertmacro SelectSection ${SecForceBie}
  ${EndIf}

  ; VRoid Studio folder: previous install, then the Steam libraries (same search as install.ps1).
  ${If} $GameDir == ""
    ReadRegStr $GameDir HKCU "${REGKEY}" "GameDir"
  ${EndIf}
  ${If} $GameDir == ""
  ${OrIfNot} ${FileExists} "$GameDir\VRoidStudio.exe"
    SetOutPath "$PLUGINSDIR\probe"
    File "${PAYLOAD}\install.ps1"
    nsExec::ExecToStack '${PS} -File "$PLUGINSDIR\probe\install.ps1" -FindGameDir'
    Pop $0
    Pop $1
    SetOutPath "$TEMP"
    ${If} $0 == 0
      ; trim the trailing newline
      ${Do}
        StrCpy $2 $1 1 -1
        ${If} $2 == "$\n"
        ${OrIf} $2 == "$\r"
          StrCpy $1 $1 -1
        ${Else}
          ${ExitDo}
        ${EndIf}
      ${Loop}
      StrCpy $GameDir $1
    ${EndIf}
  ${EndIf}
  ${If} $GameDir == ""
    StrCpy $GameDir "$PROGRAMFILES32\Steam\steamapps\common\VRoid Studio"
  ${EndIf}

  ${If} ${Silent}
  ${AndIfNot} ${FileExists} "$GameDir\VRoidStudio.exe"
    SetErrorLevel 3
    Quit
  ${EndIf}
FunctionEnd

; Options for install.ps1 from the selected components (sections are declared above).
Function BuildOpts
  StrCpy $Opts ""
  ${IfNot} ${SectionIsSelected} ${SecClaude}
    StrCpy $Opts "$Opts -NoClaude"
  ${EndIf}
  ${IfNot} ${SectionIsSelected} ${SecDsh}
    StrCpy $Opts "$Opts -NoDsh"
  ${EndIf}
  ${If} ${SectionIsSelected} ${SecForceBie}
    StrCpy $Opts "$Opts -ForceBepInEx"
  ${EndIf}
FunctionEnd

Function GameDirLeave
  ${IfNot} ${FileExists} "$GameDir\VRoidStudio.exe"
    MessageBox MB_OK|MB_ICONEXCLAMATION "$(GameNotFound)"
    Abort
  ${EndIf}
FunctionEnd

; ---------------------------------------------------------------- uninstall
Section "un.$(UnSecBridge)" UnSecBridge
  SectionIn RO
  !insertmacro CheckVRoidClosed
  ReadRegStr $GameDir HKCU "${REGKEY}" "GameDir"

  Call un.BuildOpts

  ; Plugin, BepInEx (optional) and assistant entries: done by install.ps1, run from a temp copy.
  ${If} ${FileExists} "$INSTDIR\setup\install.ps1"
    InitPluginsDir
    CopyFiles /SILENT "$INSTDIR\setup\*.*" "$PLUGINSDIR"
    nsExec::ExecToLog /OEM '${PS} -File "$PLUGINSDIR\install.ps1" -Uninstall -McpDir "$INSTDIR" -LogFile "$TEMP\VRoidMcp-uninstall.log"$Opts'
    Pop $0
    ${If} $0 != 0
      DetailPrint "$(UnCleanupWarn) ($0)"
    ${EndIf}
  ${EndIf}

  ; Program files. The preset cache is kept unless its option is selected.
  RMDir /r "$INSTDIR\mcp_server"
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\tools"
  RMDir /r "$INSTDIR\docs"
  RMDir /r "$INSTDIR\config"
  RMDir /r "$INSTDIR\setup"
  Delete "$INSTDIR\README*.md"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
  Delete "$INSTDIR\install-state.json"
  Delete "$INSTDIR\${UNINSTEXE}"

  RMDir /r "$SMPROGRAMS\${APPNAME}"
  DeleteRegKey HKCU "${UNINSTKEY}"
  DeleteRegKey HKCU "${REGKEY}"
SectionEnd

Section /o "un.$(UnSecBie)" UnSecBie
SectionEnd

Section /o "un.$(UnSecCache)" UnSecCache
  RMDir /r "$INSTDIR\preset_cache"
SectionEnd

Section "-un.finish"
  RMDir "$INSTDIR" ; only if empty
SectionEnd

!insertmacro MUI_UNFUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${UnSecBridge} "$(UnDescBridge)"
  !insertmacro MUI_DESCRIPTION_TEXT ${UnSecBie} "$(UnDescBie)"
  !insertmacro MUI_DESCRIPTION_TEXT ${UnSecCache} "$(UnDescCache)"
!insertmacro MUI_UNFUNCTION_DESCRIPTION_END

Function un.BuildOpts
  StrCpy $Opts ""
  ${If} ${SectionIsSelected} ${UnSecBie}
    StrCpy $Opts "$Opts -RemoveBepInEx"
  ${EndIf}
  ${If} $GameDir != ""
    StrCpy $Opts '$Opts -GameDir "$GameDir"'
  ${EndIf}
FunctionEnd

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/REMOVEBEPINEX" $R1
  ${IfNot} ${Errors}
    !insertmacro SelectSection ${UnSecBie}
  ${EndIf}
  ClearErrors
  ${GetOptions} $R0 "/REMOVECACHE" $R1
  ${IfNot} ${Errors}
    !insertmacro SelectSection ${UnSecCache}
  ${EndIf}
FunctionEnd
