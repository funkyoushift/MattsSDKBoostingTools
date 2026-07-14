!macro customInstall
  DetailPrint "Installing bundled MSBT SDK mod files into Borderlands 4 sdk_mods..."
  ExecWait '"$INSTDIR\MattsSDKBoostingTools.exe" --install-sdkmods-and-exit' $0
  DetailPrint "MSBT SDK mod installer helper exited with code $0."
  DetailPrint "If Borderlands 4 was open, fully restart the game before testing live actions."
!macroend
