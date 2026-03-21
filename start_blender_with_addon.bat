@echo off
setlocal
taskkill /F /IM blender.exe /T 2>nul

:: Unblock files that might be restricted because they were downloaded from the internet (GitHub)
powershell -ExecutionPolicy Bypass -Command "Get-ChildItem -Path '%~dp0' -Recurse | Unblock-File"

:: Running through Python to avoid Smart App Control blocks on complex batch logic
python "%~dp0dev_tool.py" start
if %ERRORLEVEL% NEQ 0 pause
