@echo off
:: ============================================================
::  X-Vault Launcher — Eleva para Administrador automaticamente
:: ============================================================

NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Solicitando permissões de Administrador...
    PowerShell -Command "Start-Process '%~f0' -Verb RunAs"
    EXIT /B
)

:: Já é admin — inicia o app
cd /d "%~dp0"
python src\main.py
pause
