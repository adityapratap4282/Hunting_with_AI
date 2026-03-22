@echo off
setlocal
cd /d %~dp0

where py >nul 2>nul
if %errorlevel%==0 (
  py start_app.py
  goto end
)

where python >nul 2>nul
if %errorlevel%==0 (
  python start_app.py
  goto end
)

echo Python was not found on PATH. Please install Python 3.11 and try again.
pause
exit /b 1

:end
if errorlevel 1 (
  echo.
  echo The local app exited with an error.
  pause
)
