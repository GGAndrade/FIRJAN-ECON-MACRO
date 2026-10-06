import streamlit as st
import locale
from cac.main import update_cac_pcons, update_cac_pcorr
from cac.cac_dash import render_cac_dashboard
from func import (
    check_password,
    config_page,
    header_firjan,
    footer_firjan,
    to_excel,
)

###### CONFIGURAÇÕES INICIAIS

# Configuração da página e identidade visual Firjan
config_page("CAC SHWEB | Firjan - GEE")
header_firjan()

# Verificação de segurança por senha
if not check_password():
    footer_firjan()
    st.stop()

# Especificar locale
locale.setlocale(locale.LC_TIME, locale="pt_BR")

st.title("Coeficientes de Abertura Comercial (CAC) - Firjan")

tab_dash, tab_planilhas = st.tabs(["📊 DASHBOARD DE INDICADORES", "📁 GERADOR DE PLANILHAS (CARGAS SHWEB)"])

with tab_dash:
    render_cac_dashboard()

with tab_planilhas:
    if check_password():
        col1, col2 = st.columns(2)

        with col1:
            pcons = st.file_uploader(
                label="Planilha preços constantes",
                type="xlsx",
                key="pcons",
                help="Selecione a planilha de preços constantes do CAC",
            )

            if pcons:
                planilha = update_cac_pcons(pcons)
                df_xlsx = to_excel([planilha])
                st.download_button(
                    label="📥 Baixar planilha: precos constantes",
                    data=df_xlsx,
                    file_name="cac_shweb_pcons.xlsx",
                    use_container_width=True,
                )

        with col2:
            pcorr = st.file_uploader(
                label="Planilha preços correntes",
                type="xlsx",
                key="pcorr",
                help="Selecione a planilha de preços correntes do CAC",
            )

            if pcorr:
                planilha = update_cac_pcorr(pcorr)
                df_xlsx = to_excel([planilha])
                st.download_button(
                    label="📥 Baixar planilha: precos correntes",
                    data=df_xlsx,
                    file_name="cac_shweb_pcorr.xlsx",
                    use_container_width=True,
                )

# Rodapé oficial Sistema Firjan
footer_firjan()
