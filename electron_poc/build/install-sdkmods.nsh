!include "nsDialogs.nsh"
!include "LogicLib.nsh"

!ifndef BUILD_UNINSTALLER
Var MSBTReportChoice
Var MSBTDumpChoice
Var MSBTReportCheckbox
Var MSBTDumpCheckbox

!macro customPageAfterChangeDir
  Page custom MSBTReportPageCreate MSBTReportPageLeave
!macroend

Function MSBTReportPageCreate
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 40u "Optional private failure reports. New installs default off; leaving this unchecked keeps any existing choice. Reports go to a private Cloudflare inbox and are scheduled for deletion after seven days. They include limited redacted logs and crash context, never saves or command inputs. Change this later in the Report tab."
  Pop $0
  ${NSD_CreateCheckbox} 0 50u 100% 12u "Send failure reports automatically"
  Pop $MSBTReportCheckbox
  ${NSD_CreateCheckbox} 0 68u 100% 20u "Also include crash memory dumps (may contain private game or account data)"
  Pop $MSBTDumpCheckbox
  ${If} $MSBTReportChoice == "true"
    ${NSD_Check} $MSBTReportCheckbox
    ${If} $MSBTDumpChoice == "true"
      ${NSD_Check} $MSBTDumpCheckbox
    ${EndIf}
  ${Else}
    EnableWindow $MSBTDumpCheckbox 0
  ${EndIf}
  ${NSD_OnClick} $MSBTReportCheckbox MSBTReportChoiceChanged
  nsDialogs::Show
FunctionEnd

Function MSBTReportChoiceChanged
  Pop $0
  ${NSD_GetState} $MSBTReportCheckbox $0
  ${If} $0 == ${BST_CHECKED}
    EnableWindow $MSBTDumpCheckbox 1
  ${Else}
    EnableWindow $MSBTDumpCheckbox 0
    ${NSD_SetState} $MSBTDumpCheckbox ${BST_UNCHECKED}
  ${EndIf}
FunctionEnd

Function MSBTReportPageLeave
  ${NSD_GetState} $MSBTReportCheckbox $0
  StrCpy $MSBTReportChoice ""
  StrCpy $MSBTDumpChoice "false"
  ${If} $0 == ${BST_CHECKED}
    StrCpy $MSBTReportChoice "true"
    ${NSD_GetState} $MSBTDumpCheckbox $0
    ${If} $0 == ${BST_CHECKED}
      StrCpy $MSBTDumpChoice "true"
    ${EndIf}
  ${EndIf}
FunctionEnd
!endif

!macro customInstall
  DetailPrint "Installing Borderlands 4 Modding Tools, AFK SHiFT PAK, and missing SDK/mod manager..."
  ExecWait '"$INSTDIR\MattsSDKBoostingTools.exe" --install-sdkmods-and-exit' $0
  DetailPrint "MSBT SDK mod installer helper exited with code $0."
  ${If} $0 != 0
    MessageBox MB_OK|MB_ICONEXCLAMATION "Borderlands 4 Modding Tools was installed, but game integration could not finish. Close Borderlands 4 and use Settings > Install / update SDK mod in the desktop app. Existing SDK/mod-manager files were preserved." /SD IDOK
  ${EndIf}
  ${If} $MSBTReportChoice == "true"
    StrCpy $1 "--set-failure-reporting=logs"
    ${If} $MSBTDumpChoice == "true"
      StrCpy $1 "--set-failure-reporting=dumps"
    ${EndIf}
    ${StdUtils.ExecShellAsUser} $0 "$INSTDIR\MattsSDKBoostingTools.exe" "open" "$1"
    DetailPrint "Optional failure reporting choice sent to the installing user's app profile."
  ${EndIf}
!macroend
