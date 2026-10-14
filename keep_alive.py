"""
Serviço Keep-Alive automático para o Streamlit Cloud (Firjan Macro).
Envia pings HTTP periódicos para evitar que a aplicação entre em hibernação (sleep).
"""

import time
import datetime
import requests

URLS_PARA_PING = [
    "https://firjan-macro.streamlit.app",
    "https://firjan-macro.streamlit.app/PIM",
]

INTERVALO_SEGUNDOS = 20 * 60  # 20 minutos


def executar_ping():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for url in URLS_PARA_PING:
        try:
            resposta = requests.get(url, timeout=30)
            print(f"[{timestamp}] Ping em {url} -> HTTP {resposta.status_code}")
        except Exception as erro:
            print(f"[{timestamp}] Falha no ping de {url}: {erro}")


def loop_continuo():
    print("Iniciando serviço Keep-Alive para firjan-macro.streamlit.app...")
    while True:
        executar_ping()
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    loop_continuo()
