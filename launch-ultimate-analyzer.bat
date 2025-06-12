@echo off
title Enterprise Log Analyzer - Ultimate Edition
echo Starting Enterprise Log Analyzer - Ultimate Edition...
echo.
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo Installing required dependencies...
python -m pip install customtkinter requests --upgrade --quiet 2>nul

echo Launching Ultimate Log Analyzer...
echo.
python desktop-analyzer-ultimate.py
pause