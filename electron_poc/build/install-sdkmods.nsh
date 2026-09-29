!macro customInstall
  DetailPrint "Installing Borderlands 4 Modding Tools, AFK SHiFT PAK, and missing SDK/mod manager..."
  ExecWait '"$INSTDIR\MattsSDKBoostingTools.exe" --install-sdkmods-and-exit' $0
  DetailPrint "MSBT SDK mod installer helper exited with code $0."
  ${If} $0 != 0
    MessageBox MB_OK|MB_ICONEXCLAMATION "Borderlands 4 Modding Tools was installed, but game integration could not finish. Close Borderlands 4 and use Settings > Install / update SDK mod in the desktop app. Existing SDK/mod-manager files were preserved."
  ${EndIf}
!macroend
