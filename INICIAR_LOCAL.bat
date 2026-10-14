@echo off
title Servidor Streamlit - Firjan Macro
cd /d "%~dp0"

echo ========================================================
echo  Iniciando servidor local Streamlit (Firjan Macro)...
echo ========================================================
echo.

:: Garante configuracoes para nunca pedir email no terminal
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit" >nul 2>&1
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    (
        echo [general]
        echo email = ""
    ) > "%USERPROFILE%\.streamlit\credentials.toml"
)
if not exist ".streamlit" mkdir ".streamlit" >nul 2>&1
if not exist ".streamlit\credentials.toml" (
    (
        echo [general]
        echo email = ""
    ) > ".streamlit\credentials.toml"
)

:: Encerra processos residuais na porta 8501, se houver
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501 ^| findstr LISTENING') do (
    echo Liberando porta 8501...
    taskkill /F /PID %%a >nul 2>&1
)

:: Abre o navegador automaticamente apos 3 segundos
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8501"

echo Acesse em: http://localhost:8501
echo Para encerrar o dashboard, basta fechar esta janela.
echo ========================================================
echo.

.\.venv\Scripts\python.exe -m streamlit run INICIO.py --server.port=8501 --browser.gatherUsageStats=false

pause
