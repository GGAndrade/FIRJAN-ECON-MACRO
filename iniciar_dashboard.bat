@echo off
title Servidor Firjan - Dados MACRO
echo ========================================================
echo   Iniciando Servidor Streamlit - Firjan Dados MACRO
echo ========================================================
echo.
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m streamlit run INICIO.py --server.port=8501
pause
