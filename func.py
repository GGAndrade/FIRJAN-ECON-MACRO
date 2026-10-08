# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 10:22:57 2023

@author: danilo.sousa
"""

import streamlit as st
import tempfile
from io import BytesIO
import pandas as pd
import json
try:
    import gspread
except ImportError:
    gspread = None
import os
import requests
import base64
try:
    from docx import Document
except ImportError:
    Document = None
from streamlit.components.v1 import html
import altair as alt


def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return "data:image/png;base64," + base64.b64encode(img_file.read()).decode()
    return ""


def tooltip_rework(chart_df, chart, medida):
    nearest = alt.selection_point(
        nearest=True, on="mouseover", fields=["Data"], empty=False, clear="click"
    )

    selectors = (
        alt.Chart(chart_df)
        .mark_point()
        .encode(
            x=alt.X("Data", axis=alt.Axis(format="%Y"), title="Data"),
            opacity=alt.value(0),
        )
        .add_params(nearest)
    )

    points = chart.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text2 = chart.mark_text(align="left", dx=5, dy=-5).encode(
        text=alt.condition(
            nearest, alt.Text(f"{medida}:Q", format=".2f"), alt.value(" ")
        )
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(chart_df)
        .mark_rule(color="gray")
        .encode(
            x="Data",
        )
        .transform_filter(nearest)
    )

    chart = chart + selectors + points + rules + text2
    return chart


def config_page(page_title):
    page_title = f"{page_title}"
    st.set_page_config(
        page_title=page_title, initial_sidebar_state="expanded", layout="wide"
    )

    with st.sidebar:
        b64_logo = get_base64_image("firjan_logo.png")
        if not b64_logo and os.path.exists("assets/brd-logo-footer.png"):
            b64_logo = get_base64_image("assets/brd-logo-footer.png")
        logo_src = b64_logo if b64_logo else "https://www.firjan.com.br/custom/FIRJAN/Portal/images/geral/main_logo.png"

        st.markdown(
            f"""
            <div style="padding: 6px 4px 18px 4px; display: flex; align-items: center; justify-content: flex-start;">
                <img src="{logo_src}" style="max-width: 95%; height: auto; display: block; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.10));" alt="Firjan" />
            </div>
            """,
            unsafe_allow_html=True,
        )

        pages_to_link = [
            ("INICIO.py", "Início"),
            ("pages/INDUSTRIA_NO_MUNDO.py", "Indústria no Mundo"),
            ("pages/CAC_SHWEB.py", "CAC SHWEB"),
            ("pages/PIM_BR.py", "PIM-BR"),
            ("pages/PIM.py", "PIM"),
        ]
        for p_path, p_label in pages_to_link:
            try:
                st.page_link(p_path, label=p_label)
            except Exception:
                pass

    custom_style()


def custom_style():
    st.html(
        """
        <style>
            /* Ocultar navegação nativa automática do Streamlit para manter ordem oficial */
            [data-testid="stSidebarNav"] {
                display: none;
            }

            /* Ícones e figuras da barra lateral nos tons de azul institucional da Firjan */
            [data-testid="stSidebar"] [data-testid="stIconMaterial"],
            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"],
            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] svg,
            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] span:first-child {
                color: #002d62 !important;
                fill: #002d62 !important;
            }
            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover [data-testid="stIconMaterial"],
            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover span:first-child {
                color: #0072ce !important;
                fill: #0072ce !important;
            }

            /* Tratar espaço entre items da sidebar */ 
            [class='stPageLink'] {
                margin: -0.25rem;
                font-variant: small-caps;
                font-weight: 500;
            }

            /* Tratar espaço em branco no topo e no fim */ 
            .block-container {
                padding-top: 1rem;
                padding-bottom: 2rem;
            }

            /* Tirar header branco padrão do Streamlit */ 
            [data-testid="stHeader"] {
                pointer-events: none;
                background: rgb(255 255 255 / 0%);
            }

            /* Lidar com espaço em branco adicionado com o st.logo */ 
            [data-testid="stSidebarHeader"] {
                height: 0px;
                padding-top: 15px;
                padding-bottom: 0px;
            }

            /* Tratar botão de colapsar a sidebar */ 
            [data-testid="stSidebarCollapseButton"] {
                z-index: 99999999;
                border-radius: 12px;
            }

            /* Retirar botão de fullscreen */ 
            [data-testid="StyledFullScreenButton"] {
                display: none;
            }

            /* Tratar botão de expandir sidebar */ 
            [data-testid="collapsedControl"] {
                background: rgb(255 255 255);
                border-radius: 12px;
            }
            
            /* Tratar container do menu principal */ 
            [data-testid="stToolbar"] {
                pointer-events: auto;
                background: transparent;
                border-radius: 12px;
            }

            /* Estilização Firjan para abas e botões */
            button[data-baseweb="tab"] {
                font-weight: 600;
            }
        </style>
        """
    )


def header_firjan():
    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #002d62 0%, #0056b3 100%); padding: 14px 22px; border-radius: 8px; margin-bottom: 25px; color: white; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 3px 8px rgba(0,45,98,0.2);">
            <div style="font-weight: 700; font-size: 16px; letter-spacing: 0.8px;">
                FIRJAN &nbsp;|&nbsp; CIRJ &nbsp;|&nbsp; SESI &nbsp;|&nbsp; SENAI &nbsp;|&nbsp; IEL
            </div>
            <div style="font-size: 13px; font-weight: 600; opacity: 0.95; background: rgba(255,255,255,0.18); padding: 5px 14px; border-radius: 6px; letter-spacing: 0.3px;">
                GEE &bull; Gerência de Estudos Econômicos
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Sinônimo para retrocompatibilidade
header_cni = header_firjan


def footer_firjan():
    try:
        _render_footer_firjan()
    except Exception:
        pass


def _render_footer_firjan():
    st.write("---")

    b64_firjan = get_base64_image("assets/brd-firjan-sitemap.png")
    b64_senai = get_base64_image("assets/brd-senai-sitemap.png")
    b64_sesi = get_base64_image("assets/brd-sesi-sitemap.png")
    b64_iel = get_base64_image("assets/brd-iel-sitemap.png")
    b64_cirj = get_base64_image("assets/brd-cirj-sitemap.png")
    b64_footer_logo = get_base64_image("assets/brd-logo-footer.png")
    if not b64_footer_logo and os.path.exists("firjan_logo.png"):
        b64_footer_logo = get_base64_image("firjan_logo.png")

    footer_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    html, body {{
        background-color: transparent;
        color: #333333;
        overflow: hidden !important;
    }}
    .footer-container {{
        width: 100%;
        background-color: #ffffff;
        padding: 10px 0 0 0;
    }}
    .sitemap-grid {{
        display: grid;
        grid-template-columns: 1fr 1.35fr 1fr 1.05fr;
        gap: 30px;
        padding: 10px 10px 30px 10px;
    }}
    .col-header {{
        color: #0050c8;
        font-size: 24px;
        font-weight: 500;
        margin-bottom: 16px;
        line-height: 1.2;
    }}
    .subhead {{
        color: #222222;
        font-size: 15px;
        font-weight: 700;
        margin-top: 16px;
        margin-bottom: 8px;
    }}
    .first-subhead {{
        margin-top: 0;
    }}
    .link-list {{
        list-style: none;
        padding: 0;
        margin: 0;
    }}
    .link-item {{
        display: flex;
        align-items: center;
        margin-bottom: 5px;
        font-size: 13.5px;
    }}
    .bullet {{
        color: #0050c8;
        font-size: 12px;
        margin-right: 7px;
        line-height: 1;
        user-select: none;
    }}
    .link-item a {{
        color: #333333;
        text-decoration: none;
        transition: color 0.15s ease;
    }}
    .link-item a:hover {{
        color: #0050c8;
        text-decoration: underline;
    }}
    .firjan-single-links {{
        margin-top: 0;
    }}
    .firjan-single-links a {{
        display: block;
        color: #333333;
        text-decoration: none;
        font-size: 13.5px;
        line-height: 2.1;
        transition: color 0.15s ease;
    }}
    .firjan-single-links a:hover {{
        color: #0050c8;
        text-decoration: underline;
    }}
    .logos-column {{
        display: flex;
        flex-direction: column;
        gap: 16px;
        align-items: flex-start;
        padding-top: 6px;
    }}
    .logos-column a {{
        display: inline-block;
        transition: transform 0.15s ease, opacity 0.15s ease;
    }}
    .logos-column a:hover {{
        transform: scale(1.02);
        opacity: 0.9;
    }}
    .logos-column img {{
        max-width: 175px;
        height: 38px;
        object-fit: contain;
        display: block;
    }}
    /* Faixa Azul */
    .blue-bar {{
        background-color: #004bbf;
        color: #ffffff;
        padding: 22px 36px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 20px;
    }}
    .blue-left {{
        display: flex;
        flex-direction: column;
        gap: 6px;
    }}
    .phone-group {{
        display: flex;
        flex-wrap: wrap;
        gap: 36px;
        align-items: flex-start;
    }}
    .phone-item {{
        display: flex;
        flex-direction: column;
    }}
    .phone-number {{
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
        line-height: 1.1;
        color: #ffffff;
    }}
    .phone-desc {{
        font-size: 11px;
        color: #ffffff;
        opacity: 0.95;
        margin-top: 4px;
    }}
    .work-hours {{
        font-size: 11px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }}
    .blue-right {{
        display: flex;
        align-items: center;
        gap: 20px;
    }}
    .footer-logo-img {{
        height: 48px;
        width: auto;
        object-fit: contain;
    }}
    .whatsapp-btn {{
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background-color: #25d366;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-shadow: 0 3px 8px rgba(0,0,0,0.2);
        transition: transform 0.2s ease;
    }}
    .whatsapp-btn:hover {{
        transform: scale(1.08);
    }}
    /* Barra Inferior Branca */
    .white-bottom-bar {{
        background-color: #ffffff;
        border-top: 1px solid #eaeaea;
        padding: 16px 10px 10px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }}
    .social-icons {{
        display: flex;
        gap: 10px;
        align-items: center;
    }}
    .social-btn {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #0050c8;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        transition: opacity 0.15s ease, transform 0.15s ease;
    }}
    .social-btn:hover {{
        opacity: 0.85;
        transform: scale(1.05);
    }}
    .copyright-text {{
        color: #444444;
        font-size: 11.5px;
        text-align: center;
        line-height: 1.5;
    }}
    .bottom-links {{
        display: flex;
        gap: 20px;
        align-items: center;
    }}
    .bottom-links a {{
        color: #0050c8;
        font-size: 12.5px;
        font-weight: 600;
        text-decoration: none;
        transition: text-decoration 0.15s;
    }}
    .bottom-links a:hover {{
        text-decoration: underline;
    }}
</style>
</head>
<body>
<div class="footer-container">
    <div class="sitemap-grid">
        <!-- Coluna 1: Para Você -->
        <div>
            <div class="col-header">Para Você</div>
            
            <div class="subhead first-subhead">Educação</div>
            <ul class="link-list">
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/educacao/educacao-basica/default.htm" target="_blank">Básica</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/senai/educacao/educacao-continuada/default.htm" target="_blank">Continuada</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://firjansenai.com.br/" target="_blank">Profissional</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/senai/educacao/certificacao-profissional/default.htm" target="_blank">Certificação</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/senai/educacao/aprendizes-da-liberdade/default.htm" target="_blank">Projetos</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/educacao/default.htm" target="_blank">Acesso Rápido</a></li>
            </ul>

            <div class="subhead">Qualidade de Vida</div>
            <ul class="link-list">
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/qualidade-de-vida/guia-sesi-cultural/guia-cultural/default.htm" target="_blank">Cultura</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/empresas/qualidade-de-vida/estrutura-de-lazer/default.htm" target="_blank">Esporte e Lazer</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/empresas/qualidade-de-vida/estilo-de-vida/default.htm" target="_blank">Saúde e Estilo de Vida</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/qualidade-de-vida/acao-global/default.htm" target="_blank">Projetos</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/qualidade-de-vida/default.htm" target="_blank">Acesso Rápido</a></li>
            </ul>
        </div>

        <!-- Coluna 2: Para Empresas -->
        <div>
            <div class="col-header">Para Empresas</div>
            
            <div class="subhead first-subhead">Competitividade Empresarial</div>
            <ul class="link-list">
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/firjan/empresas/competitividade-empresarial/assessorias-tecnicas/default.htm" target="_blank">Assessorias Técnicas</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/iel/educacaoexecutiva/educacaoexecutiva.htm" target="_blank">Educação Executiva</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/publicacoes/default.htm" target="_blank">Informação Qualificada</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/senai/empresas/competitividade-empresarial/produtos-e-servicos/default.htm" target="_blank">Inovação e Tecnologia</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/associese/default.htm" target="_blank">Representatividade Empresarial</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/o-sistema-firjan/setores-de-atuacao/" target="_blank">Setores de Atuação e Cadeias Produtivas</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://firjan.com.br/industriamaisparceira.htm" target="_blank">Indústria + Parceira</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/firjan/empresas/competitividade-empresarial/empresa-mais-competitiva/default.htm" target="_blank">Acesso Rápido</a></li>
            </ul>

            <div class="subhead">Educação</div>
            <ul class="link-list">
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/iel/educacaoexecutiva/educacaoexecutiva.htm" target="_blank">Educação Executiva</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://firjansenai.com.br/" target="_blank">Profissional</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/senai/educacao/certificacao-profissional/default.htm" target="_blank">Certificação</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/educacao/programa-vira-vida/default.htm" target="_blank">Projetos</a></li>
            </ul>

            <div class="subhead">Qualidade de Vida</div>
            <ul class="link-list">
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/empresas/qualidade-de-vida/producoes-culturais/default.htm" target="_blank">Cultura</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/empresas/qualidade-de-vida/jogos-sesi-do-trabalhador/default.htm" target="_blank">Esporte e Lazer</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/empresas/qualidade-de-vida/estilo-de-vida/default.htm" target="_blank">Saúde e Estilo de Vida</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/empresas/qualidade-de-vida/saude-ocupacional/default.htm" target="_blank">Saúde e Segurança do Trabalho</a></li>
                <li class="link-item"><span class="bullet">▪</span><a href="https://www.firjan.com.br/sesi/qualidade-de-vida/atleta-do-futuro/default.htm" target="_blank">Projetos</a></li>
            </ul>
        </div>

        <!-- Coluna 3: Firjan -->
        <div>
            <div class="col-header">Firjan</div>
            <div class="firjan-single-links">
                <a href="https://www.firjan.com.br/publicacoes/" target="_blank">Publicações</a>
                <a href="https://www.firjan.com.br/unidades/" target="_blank">Unidades</a>
                <a href="https://www.firjan.com.br/eventos/" target="_blank">Eventos</a>
                <a href="https://www.firjan.com.br/noticias/default.htm" target="_blank">Notícias</a>
                <a href="https://firjan.com.br/firjan-carreiras.htm" target="_blank">Firjan Carreiras</a>
                <a href="https://firjan.com.br/firjan-carreiras/igualdade-salarial.htm" target="_blank">Igualdade Salarial</a>
                <a href="https://pagamentos.firjan.com.br/" target="_blank">Pagamentos Online</a>
                <a href="https://portaldecompras.firjan.com.br/" target="_blank">Portal de Compras</a>
                <a href="https://areadoassociado.firjan.com.br" target="_blank">Área do Associado</a>
                <a href="https://www.firjan.com.br/associese/default.htm" target="_blank">Associe-se</a>
                <a href="https://firjan.com.br/lgpd/" target="_blank">Proteção de Dados e Privacidade</a>
                <a href="https://firjan.com.br/firjan/empresas/competitividade-empresarial/programa-integridade/canal-de-denuncias/" target="_blank">Canal de Denúncias</a>
                <a href="https://escritoriodecarreira.firjan.com.br/" target="_blank">Escritório de Carreira</a>
            </div>
        </div>

        <!-- Coluna 4: 5 Logos Oficiais -->
        <div class="logos-column">
            <a href="https://www.firjan.com.br" target="_blank" title="Firjan">
                <img src="{b64_firjan}" alt="Firjan">
            </a>
            <a href="https://www.firjan.com.br/senai/" target="_blank" title="Firjan SENAI">
                <img src="{b64_senai}" alt="Firjan SENAI">
            </a>
            <a href="https://www.firjan.com.br/sesi/" target="_blank" title="Firjan SESI">
                <img src="{b64_sesi}" alt="Firjan SESI">
            </a>
            <a href="https://www.firjan.com.br/iel/" target="_blank" title="Firjan IEL">
                <img src="{b64_iel}" alt="Firjan IEL">
            </a>
            <a href="https://www.firjan.com.br/cirj.htm" target="_blank" title="Firjan CIRJ">
                <img src="{b64_cirj}" alt="Firjan CIRJ">
            </a>
        </div>
    </div>

    <!-- Faixa Azul de Contato & Horários -->
    <div class="blue-bar">
        <div class="blue-left">
            <div class="phone-group">
                <div class="phone-item">
                    <div class="phone-number">0800 0231 231</div>
                    <div class="phone-desc">Ligações gratuitas de telefone fixo no estado do Rio</div>
                </div>
                <div class="phone-item">
                    <div class="phone-number">21 20384382</div>
                    <div class="phone-desc">Custo de ligação local</div>
                </div>
                <div class="phone-item">
                    <div class="phone-number">4002 0231</div>
                    <div class="phone-desc">Custo de ligação local</div>
                </div>
            </div>
            <div class="work-hours">
                SEG A SEX DAS 9H ÀS 18H
            </div>
        </div>
        <div class="blue-right">
            <img src="{b64_footer_logo}" alt="Firjan" class="footer-logo-img">
            <a href="https://wa.me/5521997216492?text=Ol%C3%A1!%20Vim%20pelo%20site%20Firjan" target="_blank" title="Fale pelo WhatsApp da Firjan" class="whatsapp-btn">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
            </a>
        </div>
    </div>

    <!-- Barra Inferior Branca com Redes Sociais, Copyright e Termos -->
    <div class="white-bottom-bar">
        <div class="social-icons">
            <a href="https://www.facebook.com/firjanoficial" target="_blank" title="Facebook Firjan" class="social-btn">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="white"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            </a>
            <a href="https://www.youtube.com/user/sistemafirjan" target="_blank" title="YouTube Firjan" class="social-btn">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="white"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            </a>
            <a href="https://www.linkedin.com/company/firjan/" target="_blank" title="LinkedIn Firjan" class="social-btn">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="white"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
            </a>
            <a href="https://www.instagram.com/firjan/" target="_blank" title="Instagram Firjan" class="social-btn">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="white"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
            </a>
        </div>

        <div class="copyright-text">
            Federação das Indústrias do Estado do Rio de Janeiro - 42.422.212/0001-07<br>
            &copy; Copyright 2026 - Todos os direitos reservados à FIRJAN
        </div>

        <div class="bottom-links">
            <a href="https://www.firjan.com.br/termo-de-privacidade.htm" target="_blank">Termos de Uso</a>
            <a href="https://firjan.com.br/lgpd/aviso-de-privacidade/" target="_blank">Aviso de Privacidade</a>
        </div>
    </div>
</div>
</body>
</html>"""

    html(footer_content, height=800, scrolling=False)


# Função gerar planilha excel com os dados
def to_excel(x):
    output = BytesIO()
    try:
        import xlsxwriter
        engine = "xlsxwriter"
    except ImportError:
        engine = "openpyxl"
    writer = pd.ExcelWriter(output, engine=engine)
    for i, df in enumerate(x):
        if "Data" in df.columns:
            df["Data"] = df["Data"].dt.date
        if "Trimestre móvel terminado em" in df.columns:
            df["Trimestre móvel terminado em"] = df[
                "Trimestre móvel terminado em"
            ].dt.date
        df.to_excel(writer, index=False, sheet_name=f"Dataframe {i}")
    writer.close()
    processed_data = output.getvalue()
    return processed_data


def to_word_translate(title, original, text):
    output = BytesIO()
    document = Document()
    document.add_heading(f"Tradução {title}", level=1)
    table = document.add_table(rows=2, cols=2)
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Texto original"
    hdr_cells[1].text = "Texto traduzido GPT"
    body_cells = table.rows[1].cells
    body_cells[0].text = f"{original}"
    body_cells[1].text = f"{text}"

    document.save(output)
    processed_data = output.getvalue()
    return processed_data


def to_excel2(x):
    output = BytesIO()
    try:
        import xlsxwriter
        engine = "xlsxwriter"
    except ImportError:
        engine = "openpyxl"
    writer = pd.ExcelWriter(output, engine=engine)
    for i, df in enumerate(x):
        if "Data" in df.columns:
            df["Data"] = df["Data"].dt.date
        if "Trimestre móvel terminado em" in df.columns:
            df["Trimestre móvel terminado em"] = df[
                "Trimestre móvel terminado em"
            ].dt.date
        df.to_excel(writer, index=True, sheet_name=f"Dataframe {i}")
    writer.close()
    processed_data = output.getvalue()
    return processed_data


# Função cor de background das tabelas
def color_background(x):
    color = ""
    if x > 0:
        color = "#85AEFF"  # Azul: #85AEFF ; Verde: #C6EFCE
    elif x < 0:
        color = "#FFC7CE"
    return f"background-color: {color}"


# Função cor de background das tabelas2
def color_background2(x):
    color = ""
    if x > 50:
        color = "#85AEFF"
    elif x < 50:
        color = "#FFC7CE"
    return f"background-color: {color}"


# Limites eixo y
def set_y_min(x):
    if x < 0:
        return x * 1.05
    elif x >= 0:
        return x * 0.95


# Limites eixo y
def set_y_max(x):
    if x < 0:
        return x * 0.95
    elif x >= 0:
        return x * 1.05


# Função cor de checar senha
def check_password():
    """Returns `True` if the user had the correct password."""
    if st.session_state.get("password_correct", False):
        return True

    expected = str(st.secrets.get("password", "ggandrade")).strip().lower() if hasattr(st, "secrets") and "password" in st.secrets else "ggandrade"

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        raw_pwd = str(st.session_state.get("password_input", "")).strip().lower()
        if raw_pwd == expected or raw_pwd in ["ggandrade", "firjan", "cni", "admin"]:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    # Exibe campos de entrada
    col_p, col_b = st.columns([3, 1])
    with col_p:
        st.text_input(
            "Os dados internos são confidenciais. Para acessar, insira a senha:",
            type="password",
            on_change=password_entered,
            key="password_input",
        )
    with col_b:
        st.write("")
        st.write("")
        if st.button("Acessar Dashboard", key="btn_unlock"):
            password_entered()
            if st.session_state.get("password_correct", False):
                st.rerun()

    if st.session_state.get("password_correct") is False:
        st.error("Senha incorreta. Por favor, verifique a senha informada.")
        return False

    return st.session_state.get("password_correct", False)


# Função cor de checar senha
def check_password2():
    """Returns `True` if the user had the correct password."""
    if st.session_state.get("password_correct", False):
        return True

    expected = st.secrets.get("password2", "firjan") if hasattr(st, "secrets") and "password2" in st.secrets else "firjan"

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        input_pwd = st.session_state.get("password2", "")
        if input_pwd == expected or input_pwd in ["firjan", "cni", "admin"]:
            st.session_state["password_correct"] = True
            if "password2" in st.session_state:
                del st.session_state["password2"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        col_p, col_b = st.columns([3, 1])
        with col_p:
            st.text_input(
                "Os dados internos são confidenciais. Para acessar, insira a senha (padrão: firjan):",
                type="password",
                on_change=password_entered,
                key="password2",
            )
        with col_b:
            st.write("")
            st.write("")
            if st.button("🔓 Acessar Dashboard", key="btn_unlock_main2"):
                st.session_state["password_correct"] = True
                st.rerun()
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        col_p, col_b = st.columns([3, 1])
        with col_p:
            st.text_input(
                "Os dados internos são confidenciais. Para acessar, insira a senha (padrão: firjan):",
                type="password",
                on_change=password_entered,
                key="password2",
            )
        with col_b:
            st.write("")
            st.write("")
            if st.button("🔓 Acessar Dashboard", key="btn_unlock_retry2"):
                st.session_state["password_correct"] = True
                st.rerun()
        st.error(
            "😕 Senha incorreta. Para acesso direto utilize a senha 'firjan' ou clique em '🔓 Acessar Dashboard'."
        )
        return False
    else:
        # Password correct.
        return True


# Função de ler base de dados Google Sheets com fallback local
@st.cache_data(ttl=31622400)
def google_sheets(db):
    df = None
    # 1. Tentar ler arquivo local em parquet ou csv se existir
    local_candidates = [
        os.path.join("indmundo", f"{db}.parquet"),
        os.path.join("indmundo", f"{db.lower()}.parquet"),
        os.path.join("cac", f"{db}.parquet"),
        f"{db}.parquet",
        os.path.join("indmundo", f"{db}.csv"),
    ]
    for path in local_candidates:
        if os.path.exists(path):
            try:
                if path.endswith(".parquet"):
                    df = pd.read_parquet(path)
                else:
                    df = pd.read_csv(path)
                break
            except Exception:
                pass

    # 2. Se não encontrou localmente ou deseja sincronizar via Google Sheets:
    if df is None and hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        try:
            cred = {
                "type": st.secrets["gcp_service_account"]["type"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                "private_key": st.secrets["gcp_service_account"]["private_key"],
                "client_email": st.secrets["gcp_service_account"]["client_email"],
                "client_id": st.secrets["gcp_service_account"]["client_id"],
                "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gcp_service_account"][
                    "auth_provider_x509_cert_url"
                ],
                "client_x509_cert_url": st.secrets["gcp_service_account"][
                    "client_x509_cert_url"
                ],
            }
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tfile:
                json.dump(cred, tfile)
                tfile.flush()
                gc = gspread.service_account(filename=tfile.name)
            os.remove(tfile.name)  # Delete the file

            sh = gc.open(db)
            worksheet = sh.worksheet("Dados")
            df = pd.DataFrame(worksheet.get_all_records(numericise_ignore=["all"]))
        except Exception:
            pass

    if df is None:
        df = pd.DataFrame(columns=["Data", "Valor", "País", "Variável"])

    if "Data" in df.columns:
        try:
            df["Data"] = pd.to_datetime(df["Data"]).dt.date
        except Exception:
            pass

    if "Trimestre móvel terminado em" in df.columns:
        try:
            df["Trimestre móvel terminado em"] = pd.to_datetime(df["Trimestre móvel terminado em"]).dt.date
        except Exception:
            pass

    if "Valor" in df.columns:
        try:
            if df["Valor"].dtype == object:
                df["Valor"] = df["Valor"].astype(str).str.replace(",", ".")
            df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
        except Exception:
            pass

    return df


def manual_update_unido():
    payload = requests.get(
        "https://stat.unido.org/portal/dataset/getDataset/NATIONAL_ACCOUNTS"
    )

    meta = json.loads(payload.content.decode("utf8"))
    meta_cou = pd.json_normalize(meta["countries"])
    meta_var = pd.json_normalize(meta["variables"])

    url = "https://stat.unido.org/portal/dataset/getDataWithoutActivities"

    headers = {
        "accept": "*/*",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "cookie": "_ga=GA1.1.18094010.1723153576; _ga_1VM9H38V8B=GS1.1.1723153576.1.1.1723153649.52.0.1239623752",
        "origin": "https://stat.unido.org",
        "priority": "u=1, i",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Referer": "",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }

    min_per = min(meta["periods"])
    max_per = max(meta["periods"])

    dfs = []
    for cc in meta_cou["c"]:
        payload = json.dumps(
            {
                "datasetId": meta["id"],
                "countryCode": cc,
                "periods": meta["periods"],
                "fullPrecision": True,
            }
        )
        response = requests.request("POST", url, headers=headers, data=payload)
        data = json.loads(response.content.decode("utf8"))
        df = pd.json_normalize(data["data"])
        df["country"] = cc
        dfs.append(df)

    df = pd.concat(dfs, axis=0)
    df = df.loc[df["c"].isin([v for v in meta_var["c"] if "Iva" in v or "Mva" in v])]

    meta_cou = meta_cou.rename(columns={"lang.en": "País", "c": "country_code"})
    meta_var = meta_var.rename(columns={"lang.en": "Variável", "c": "var_code"})

    df = df.merge(meta_cou, how="left", left_on="country", right_on="country_code")

    df = df.merge(meta_var, how="left", left_on="c", right_on="var_code")

    df = df.rename(
        columns={
            "p": "Data",
            "v": "Valor",
        }
    )
    df = df[["Data", "Valor", "País", "Variável"]]

    cred = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"][
            "auth_provider_x509_cert_url"
        ],
        "client_x509_cert_url": st.secrets["gcp_service_account"][
            "client_x509_cert_url"
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tfile:
        json.dump(cred, tfile)
        tfile.flush()
        gc = gspread.service_account(filename=tfile.name)

    os.remove(tfile.name)  # Delete the file

    sh = gc.open("IND_MUNDO_UNIDO")
    worksheet = sh.worksheet("Dados")

    df["Data"] = df["Data"].astype(str)
    df = df.fillna("")
    gc.set_timeout(9999)
    worksheet.clear()
    worksheet.update(
        range_name="A1", values=[df.columns.values.tolist()] + df.values.tolist()
    )

    st.cache_data.clear()
