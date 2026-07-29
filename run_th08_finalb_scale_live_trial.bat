@echo off
setlocal
set "PYTHON=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
set "SUPERVISOR=%~dp0scripts\th08_practice_supervisor.py"
set "STATIC_ECL=%~dp0artifacts\decoded\ecldata7.ecl"
"%PYTHON%" -c "import numpy" >nul 2>&1
if errorlevel 1 (
  echo Windows Python with numpy is required: "%PYTHON%"
  exit /b 1
)
"%PYTHON%" "%SUPERVISOR%" --armed --stage 6b --difficulty lunatic ^
  --runtime-ecl-static-image "%STATIC_ECL%" ^
  --runtime-ecl-static-sha256 20b35dca3820438f0b90ae44e3362a7af27d2fc1ac7ae5888c477dc1c89a3734 ^
  --enable-finalb-scale-source-authority %*
exit /b %errorlevel%
