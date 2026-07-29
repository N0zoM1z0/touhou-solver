@echo off
setlocal
set "PYTHON=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
set "TOOL=%~dp0scripts\tools\th08_finalb_scale_live_hotkey.py"
"%PYTHON%" "%TOOL%" %*
exit /b %errorlevel%
