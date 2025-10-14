@echo off
REM FIPE Price Tracker - Windows Setup Script
REM This script automates the initial setup process

echo ================================
echo FIPE Price Tracker - Setup
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python nao esta instalado ou nao esta no PATH
    echo Por favor, instale Python 3.8 ou superior
    pause
    exit /b 1
)

echo Python encontrado!
python --version
echo.

REM Create virtual environment
echo Criando ambiente virtual...
if not exist venv (
    python -m venv venv
    echo Ambiente virtual criado com sucesso!
) else (
    echo Ambiente virtual ja existe.
)
echo.

REM Activate virtual environment
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Install dependencies
echo Instalando dependencias...
pip install -r requirements.txt
echo.

REM Check if database file exists
if not exist "C:\Users\mathe\Desktop\Programming\fipe_scrapper\fipe_data.db" (
    echo.
    echo AVISO: Arquivo de banco de dados nao encontrado!
    echo Por favor, ajuste o caminho em config.py
    echo.
)

echo ================================
echo Setup concluido com sucesso!
echo ================================
echo.
echo Para iniciar a aplicacao, execute:
echo   1. venv\Scripts\activate
echo   2. python app.py
echo.
echo A aplicacao estara disponivel em: http://127.0.0.1:5000
echo.
pause
