@echo off
chcp 65001 > nul
echo ========================================================
echo   Enviando Dashboard Firjan para o GitHub (@GGAndrade)
echo ========================================================
echo.
set "PATH=C:\Users\gerla\AppData\Local\Programs\MinGit\cmd;C:\Users\gerla\AppData\Local\Programs\bin;%PATH%"

echo 1. Verificando alterações...
git add .
git commit -m "update: Atualizações do Dashboard Firjan" 2>nul

echo 2. Enviando para https://github.com/GGAndrade/CNI-ECON-GERAL...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCESSO] Projeto enviado com sucesso para:
    echo https://github.com/GGAndrade/CNI-ECON-GERAL
) else (
    echo.
    echo [ATENCAO] Caso o repositorio ainda nao tenha sido criado ou solicite login:
    echo 1. Crie o repositorio vazio em: https://github.com/new (nome: CNI-ECON-GERAL)
    echo 2. Autentique-se com sua conta @GGAndrade.
)
echo.
pause
