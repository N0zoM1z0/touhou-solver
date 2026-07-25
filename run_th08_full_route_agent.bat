@echo off
setlocal
set "PYTHON=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
set "SUPERVISOR=\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\scripts\th08_full_route_supervisor.py"
"%PYTHON%" -c "import numpy" >nul 2>&1
if errorlevel 1 (
  echo Windows Python with numpy is required: "%PYTHON%"
  exit /b 1
)
"%PYTHON%" "%SUPERVISOR%" --armed %*
exit /b %errorlevel%
