@echo off
setlocal

set "ROOT=%~dp0"
set "APPDIR=%ROOT%MattsSDKBoostingTools_external"

if exist "%APPDIR%\MattsBoostingToolsExternal.exe" (
  start "" "%APPDIR%\MattsBoostingToolsExternal.exe"
  exit /b 0
)

if exist "%APPDIR%\matts_external_app_v22.pyw" (
  start "" "%APPDIR%\matts_external_app_v22.pyw"
  exit /b 0
)

if exist "%APPDIR%\matts_external_app_v22.py" (
  start "" pythonw "%APPDIR%\matts_external_app_v22.py"
  exit /b 0
)

if exist "%ROOT%MattsBoostingToolsExternal.exe" (
  start "" "%ROOT%MattsBoostingToolsExternal.exe"
  exit /b 0
)

if exist "%ROOT%matts_external_app_v22.pyw" (
  start "" "%ROOT%matts_external_app_v22.pyw"
  exit /b 0
)

if exist "%ROOT%matts_external_app_v22.py" (
  start "" pythonw "%ROOT%matts_external_app_v22.py"
  exit /b 0
)

echo External app not found.
echo Expected MattsBoostingToolsExternal.exe in:
echo   %APPDIR%
echo.
echo Place the MattsSDKBoostingTools_external folder next to this launcher.
pause
exit /b 1
