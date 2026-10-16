@echo off
setlocal enabledelayedexpansion
title Jurista - AI Indian Legal Assistant

:: Ensure script runs in the directory where run.bat is located
cd /d "%~dp0"

echo =====================================================================
echo                 JURISTA - AI INDIAN LEGAL ASSISTANT
echo =====================================================================
echo  Accessible, Grounded Legal Document Analysis ^& Information System
echo =====================================================================
echo.

:: 1. Check for Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python was not found on your system PATH.
        echo Please install Python 3.10+ from https://www.python.org/
        echo Make sure to check the box "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

:: 2. Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [NOTICE] .env not found. Creating from .env.example...
        copy ".env.example" ".env" >nul
        echo [WARNING] Please open .env and add your GEMINI_API_KEY from:
        echo           https://aistudio.google.com/
        echo.
    ) else (
        echo [WARNING] Neither .env nor .env.example was found.
        echo.
    )
)

:: 3. Optional dependency verification flag
if "%1"=="--install" (
    echo [INFO] Installing / updating required dependencies from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo.
)

:: 4. Announce and launch browser
echo [INFO] Starting Jurista local server on http://127.0.0.1:8000 ...
echo [INFO] Press Ctrl+C in this terminal window to stop the server anytime.
echo.

:: Open browser after 2 seconds in a background thread
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/"

:: 5. Launch FastAPI backend
%PYTHON_CMD% main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Server terminated with an error.
    pause
)
