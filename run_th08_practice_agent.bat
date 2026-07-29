@echo off
setlocal
set "PYTHON=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
set "SUPERVISOR=%~dp0scripts\th08_practice_supervisor.py"
"%PYTHON%" -c "import numpy" >nul 2>&1
if errorlevel 1 (
  echo Windows Python with numpy is required: "%PYTHON%"
  exit /b 1
)
"%PYTHON%" "%SUPERVISOR%" --armed %*
exit /b %errorlevel%
