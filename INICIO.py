import streamlit as st
from func import config_page, header_firjan, footer_firjan, check_password

# Configuração da página e logo Firjan
config_page("Início: Firjan - Dados MACRO")
header_firjan()

# Verificação de segurança por senha para todo o dashboard
if not check_password():
    footer_firjan()
    st.stop()

# Título Principal solicitado
st.write("# **📈 Dados MACRO 📊**")
st.markdown("### **Gerência Executiva de Economia (GEE) — Firjan**")

st.markdown(
    """
    Esse é o app de dados gerais e análises macroeconômicas da **Gerência Executiva de Economia (GEE) da Firjan**. 
    Sua proposta é oferecer entregas digitais de dashboards, indicadores e aplicações analíticas para áreas internas da 
    **Firjan, CIRJ, SESI, SENAI e IEL**, empresas associadas e o público externo.
    """
)

st.write("---")

# Seção Responsável Técnica
col_resp1, col_resp2 = st.columns([1, 2])
with col_resp1:
    st.markdown(
        """
        <div style="background-color: #f0f4f8; padding: 18px; border-radius: 10px; border-left: 5px solid #002d62;">
            <div style="font-size: 14px; text-transform: uppercase; color: #555; font-weight: 600;">Responsabilidade Técnica</div>
            <div style="font-size: 18px; font-weight: 700; color: #002d62; margin-top: 5px;">Gerlane Andrade</div>
            <div style="font-size: 14px; color: #333; margin-top: 2px;">Especialista em Estudos de Competitividade</div>
            <div style="font-size: 13px; color: #666; margin-top: 6px;">Gerência Executiva de Economia — Firjan</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_resp2:
    st.markdown(
        """
        <div style="background-color: #fdfdfd; padding: 18px; border-radius: 10px; border: 1px solid #e1e8ed;">
            <div style="font-size: 14px; text-transform: uppercase; color: #555; font-weight: 600;">Acesso Rápido aos Dashboards</div>
            <div style="margin-top: 8px; font-size: 14px; line-height: 1.6;">
                &bull; <b>Indústria no Mundo:</b> Desempenho e participação da indústria brasileira na produção mundial (UNIDO) e exportações globais (OCDE / Comtrade).<br>
                &bull; <b>CAC SHWEB:</b> Coeficientes de Abertura Comercial (CEX, CPI, CII, CEL) e integração internacional da indústria brasileira.<br>
                &bull; <b>PIM-BR:</b> Produção Física Industrial (IBGE) por seções e atividades econômicas, números-índices e variações setoriais.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# Seção de Notícias e Estudos da Firjan
st.markdown("### 📰 Informações e Estudos da Firjan")
st.markdown(
    """
    Acompanhe os estudos econômicos, notas técnicas, posicionamentos e o panorama da indústria fluminense e brasileira:
    
    👉 **[Notícias | Firjan](https://firjan.com.br/noticias/default.htm)**
    """
)

col_n1, col_n2, col_n3 = st.columns(3)
with col_n1:
    st.markdown(
        """
        <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; height: 100%;">
            <b>Competitividade Empresarial</b><br>
            <span style="font-size: 13px; color: #555;">Análises de ambiente de negócios, infraestrutura e custos da indústria fluminense.</span><br>
            <a href="https://firjan.com.br/noticias/default.htm" target="_blank" style="font-size: 13px;">Saiba mais &rarr;</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_n2:
    st.markdown(
        """
        <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; height: 100%;">
            <b>Comércio Exterior & Mercados</b><br>
            <span style="font-size: 13px; color: #555;">Exportações, importações e coeficientes de abertura comercial do Brasil e do Rio de Janeiro.</span><br>
            <a href="https://firjan.com.br/noticias/default.htm" target="_blank" style="font-size: 13px;">Saiba mais &rarr;</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_n3:
    st.markdown(
        """
        <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; height: 100%;">
            <b>Panorama Macroeconômico</b><br>
            <span style="font-size: 13px; color: #555;">Indicadores de produção, emprego, inflação e investimentos industriais.</span><br>
            <a href="https://firjan.com.br/noticias/default.htm" target="_blank" style="font-size: 13px;">Saiba mais &rarr;</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("---")

# Seção Fale Conosco
st.markdown("### 💬 A Firjan quer ouvir você!")
st.markdown(
    """
    Suas dúvidas, elogios e sugestões ajudam a Firjan a melhorar continuamente esse serviço. 
    Registre sua manifestação no formulário disponível no seguinte link:
    """
)

st.markdown(
    '<a href="https://firjan.com.br/fale-conosco/" target="_blank"><span style="font-size: 22px; font-weight: 700; color: #002d62;">✉️ Fale com a GEE</span></a>',
    unsafe_allow_html=True,
)

st.write("")

# Aviso com as instruções exatas solicitadas
st.info(
    'Para uma resposta mais rápida, inclua "Fale com a GEE" e "[Firjan - Economia - GEE-MACRO]" no início da sua mensagem. '
    'Responsável Técnica: Gerlane Andrade - Especialista em Estudos de Competitividade.',
    icon="📮",
)

# Rodapé oficial Sistema Firjan
footer_firjan()

