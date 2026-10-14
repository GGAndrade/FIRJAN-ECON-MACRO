# Mantem o dashboard Streamlit sempre no ar em http://localhost:8501
# Se o processo cair, reinicia sozinho apos 5 segundos.
$ErrorActionPreference = "SilentlyContinue"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$port = 8501

# Evita iniciar uma segunda instancia se a porta ja estiver em uso
if (Get-NetTCPConnection -LocalPort $port -State Listen) { exit 0 }

while ($true) {
    & $python -m streamlit run INICIO.py --server.port=$port --server.headless=true
    Start-Sleep -Seconds 5
}
