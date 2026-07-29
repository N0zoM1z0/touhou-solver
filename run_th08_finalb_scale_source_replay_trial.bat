@echo off
setlocal
set "PYTHON=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
set "TRIAL=%~dp0scripts\tools\th08_finalb_scale_source_replay_trial.py"
"%PYTHON%" "%TRIAL%" --armed %*
exit /b %errorlevel%
