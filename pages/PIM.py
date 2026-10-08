import os
import sys
from pathlib import Path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import json
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from func import (
    check_password,
    config_page,
    header_firjan,
    footer_firjan,
    set_y_min,
    set_y_max,
    to_excel2,
    card_destaque_html,
    obter_nome_curto_setor,
)

###### CONFIGURAÇÕES INICIAIS

# Configuração da página e identidade visual Firjan
config_page("PIM | Firjan - GEE")
header_firjan()

# Verificação de segurança por senha
if not check_password():
    footer_firjan()
    st.stop()

# Carregar formatações pt-BR para Altair caso existam no diretório
pt_format = None
pt_time_format = None
if os.path.exists("pt-BR-format.json"):
    try:
        with open("pt-BR-format.json", "rb") as f:
            pt_format = json.load(f)
    except Exception:
        pass

if os.path.exists("pt-BR-time-format.json"):
    try:
        with open("pt-BR-time-format.json", "rb") as f:
            pt_time_format = json.load(f)
    except Exception:
        pass


def calcular_offsets_anti_colisao(y_values, y_min, y_max, height=450, min_gap=30):
    """Calcula deslocamentos verticais (dy em pixels) para evitar sobreposição de rótulos terminais."""
    n = len(y_values)
    if n <= 1:
        return [0.0] * n
    span = y_max - y_min if y_max != y_min else 1.0
    px = [height * (1.0 - (v - y_min) / span) for v in y_values]
    idx_sorted = sorted(range(n), key=lambda i: px[i])
    target_px = [px[i] for i in idx_sorted]
    for _ in range(60):
        changed = False
        for k in range(n - 1):
            gap = target_px[k + 1] - target_px[k]
            if gap < min_gap:
                overlap = (min_gap - gap) / 2.0
                target_px[k] -= overlap
                target_px[k + 1] += overlap
                changed = True
        for k in range(n):
            target_px[k] = max(18.0, min(height - 18.0, target_px[k]))
        if not changed:
            break
    dy = [0.0] * n
    for orig_idx, final_p in zip(idx_sorted, target_px):
        dy[orig_idx] = round(final_p - px[orig_idx], 1)
    return dy


# Estilos CSS corporativos com paleta de azuis da Firjan e sem ícones
st.markdown(
    """
    <style>
    /* Estilização corporativa Firjan */
    .quadro-titulo-geral {
        font-size: 1.15rem;
        font-weight: 700;
        color: #002d62;
        padding-bottom: 6px;
        border-bottom: 2px solid #002d62;
        margin-bottom: 12px;
        letter-spacing: 0.2px;
    }
    .quadro-titulo-sub {
        margin-left: 20px;
        font-size: 0.98rem;
        font-weight: 600;
        color: #0050c8;
        border-left: 3px solid #0050c8;
        padding-left: 8px;
        margin-top: 14px;
        margin-bottom: 8px;
    }
    .divisor-quadro {
        border-top: 1px dashed #cbd5e1;
        margin: 14px 0 10px 0;
    }
    /* Valores das métricas em azul institucional Firjan */
    [data-testid="stMetricValue"] {
        color: #002d62 !important;
        font-weight: 700 !important;
    }
    /* Subsegmentos métricas */
    [data-testid="stHorizontalBlock"]:has(> div:nth-child(5)) [data-testid="stMetricValue"] {
        font-size: 1.30rem !important;
        color: #0050c8 !important;
    }
    [data-testid="stHorizontalBlock"]:has(> div:nth-child(5)) [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        color: #334155 !important;
        font-weight: 500;
    }
    /* Estilização refinada das abas */
    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        padding: 10px 20px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #002d62 !important;
        border-bottom-color: #002d62 !important;
        border-bottom-width: 3px !important;
    }
    /* Notas metodológicas institucionais discretas em fonte reduzida */
    .nota-metodologica {
        font-size: 0.80rem !important;
        line-height: 1.45 !important;
        color: #334155 !important;
        background-color: #f8fafc !important;
        border-left: 3px solid #0050c8 !important;
        padding: 7px 13px !important;
        border-radius: 0 4px 4px 0 !important;
        margin-top: 8px !important;
        margin-bottom: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título Principal e Apresentação Institucional
st.write("# Produção Física Industrial (PIM Regional e Brasil)")
st.markdown(
    """
    Monitoramento contínuo da **Produção Física Industrial** por Unidades da Federação e Brasil consolidado, 
    cobrindo seções e atividades econômicas (IBGE - Pesquisa Industrial Mensal), com análise e consolidação 
    da **Gerência de Estudos Econômicos (GEE) da Firjan**.
    """
)
st.write("---")


@st.cache_data(show_spinner=False)
def carregar_dados_pim(caminho_ou_arquivo):
    if isinstance(caminho_ou_arquivo, str):
        df = pd.read_parquet(caminho_ou_arquivo)
    else:
        df = pd.read_parquet(caminho_ou_arquivo)

    # Padronizar coluna temporal
    if "COMPETENCIA" in df.columns and "DATA" not in df.columns:
        df["DATA"] = df["COMPETENCIA"]

    df["Data"] = pd.to_datetime(df["DATA"])
    if df["Data"].dt.tz is not None:
        df["Data"] = df["Data"].dt.tz_localize(None)

    df["Data pt"] = df["Data"].dt.strftime("%m/%Y")
    df["Ano"] = df["Data"].dt.year
    df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce")

    if "LOCAL" not in df.columns:
        df["LOCAL"] = "Brasil"

    # Desduplicar registros garantindo unicidade por Local, Data, Variavel e Subgrupo
    df = df.drop_duplicates(subset=["LOCAL", "Data", "VARIAVEL", "SUBGRUPOS"], keep="last")
    return df


# Seção de Entrada e Upload de Arquivo Parquet (Padrão: pim_agregado.parquet, como no PIM-BR)
col_up1, col_up2 = st.columns([1, 1])

with col_up1:
    BD = st.file_uploader(
        label="Arquivo Parquet",
        type=["parquet"],
        key="pim_bd",
        help="Envie um arquivo Parquet com dados atualizados da PIM (IBGE) para substituir a base padrão e atualizar todos os indicadores, gráficos e tabelas.",
    )

default_parquet = "PIM_BR/pim_agregado.parquet"
if not os.path.exists(default_parquet):
    # Fallback para teste_pim se necessário
    if os.path.exists("PIM_BR/teste_pim.parquet"):
        default_parquet = "PIM_BR/teste_pim.parquet"

# Validação da existência do arquivo
if BD is None and not os.path.exists(default_parquet):
    st.error(
        f"Arquivo padrão `{default_parquet}` não encontrado. Por favor, faça o upload de um arquivo Parquet válido."
    )
    st.stop()

# Carregamento dos dados
try:
    if BD is not None:
        df_completo = carregar_dados_pim(BD)
        st.markdown(
            f'<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 16px; color: #15803d; font-size: 14px; margin: 8px 0 16px 0;">'
            f'✅ <strong>Base atualizada em memória:</strong> Utilizando arquivo Parquet enviado: <code>{BD.name}</code>. '
            f'Todos os indicadores, gráficos e tabelas foram recalculados.'
            f'</div>',
            unsafe_allow_html=True,
        )
        with col_up2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("💾 Salvar arquivo como base permanente padrão", help="Substitui permanentemente o arquivo pim_agregado.parquet no servidor para futuras sessões."):
                try:
                    with open("PIM_BR/pim_agregado.parquet", "wb") as f:
                        f.write(BD.getbuffer())
                    st.success("Base consolidada padrão atualizada com sucesso em `PIM_BR/pim_agregado.parquet`!")
                    st.cache_data.clear()
                except Exception as e_save:
                    st.warning(f"Não foi possível salvar em disco: {e_save}")
    else:
        df_completo = carregar_dados_pim(default_parquet)
        st.markdown(
            f'<div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 16px; color: #1e40af; font-size: 14px; margin: 8px 0 16px 0;">'
            f'ℹ️ Utilizando a base consolidada padrão (<code>{default_parquet}</code>).'
            f'</div>',
            unsafe_allow_html=True,
        )
except Exception as e:
    st.error(f"Erro ao ler o arquivo Parquet: {e}. Verifique o formato do arquivo e tente novamente.")
    st.stop()

# Validação das colunas mínimas
colunas_necessarias = ["DATA", "LOCAL", "VARIAVEL", "SUBGRUPOS", "VALOR"]
colunas_faltantes = [c for c in colunas_necessarias if c not in df_completo.columns]
if colunas_faltantes:
    st.error(f"O arquivo fornecido não possui as seguintes colunas obrigatórias: {colunas_faltantes}.")
    st.stop()

# Dicionário de variáveis oficiais IBGE
VARIAVEIS_DICT = {
    "Variação M/M-1 com ajuste sazonal (%)": "PIMPF - Variação mês/mês imediatamente anterior, com ajuste sazonal (M/M-1)",
    "Variação M/mesmo mês ano anterior - M/M-12 (%)": "PIMPF - Variação mês/mesmo mês do ano anterior (M/M-12)",
    "Variação acumulada no ano (%)": "PIMPF - Variação acumulada no ano (em relação ao mesmo período do ano anterior)",
    "Variação acumulada em 12 meses (%)": "PIMPF - Variação acumulada em 12 meses (em relação ao período anterior de 12 meses)",
    "Número-índice com ajuste sazonal (2022=100)": "PIMPF - Número-índice com ajuste sazonal (2022=100)",
    "Número-índice sem ajuste (2022=100)": "PIMPF - Número-índice (2022=100)",
    "Influência M/M-1 com ajuste sazonal (p.p.)": "PIMPF - Influência mês/mês imediatamente anterior, com ajuste sazonal (M/M-1)",
    "Influência M/M-12 (p.p.)": "PIMPF - Influência mês/mesmo mês do ano anterior (M/M-12)",
    "Influência no acumulado no ano (p.p.)": "PIMPF - Influência no acumulado no ano (em relação ao mesmo período do ano anterior",
    "Influência no acumulado em 12 meses (p.p.)": "PIMPF - Influência no acumulado em 12 meses (em relação ao período anterior de 12 meses)",
}

# Mapear variáveis de forma flexível a acentuações e encodings
vars_banco = df_completo["VARIAVEL"].dropna().unique().tolist()
opcoes_medidas = {}
for rotulo, var_oficial in VARIAVEIS_DICT.items():
    if var_oficial in vars_banco:
        opcoes_medidas[rotulo] = var_oficial
    else:
        # Correspondência tolerante a variações de encoding
        termo_busca = var_oficial.split("(")[0].strip()[:25]
        encontrados = [v for v in vars_banco if termo_busca.lower() in v.lower()]
        if encontrados:
            opcoes_medidas[rotulo] = encontrados[0]

for v in vars_banco:
    if v not in opcoes_medidas.values():
        opcoes_medidas[v] = v

# Mapeamento para nomes amigáveis e concisos dos ramos industriais (IBGE)
MAPA_NOMES_CURTOS_SETORES = {
    "1 Ind": "Indústria Geral",
    "2 Ind": "Indústrias extrativas",
    "3 Ind": "Indústrias de transformação",
    "3.10": "Produtos alimentícios",
    "3.11": "Bebidas",
    "3.12": "Produtos do fumo",
    "3.13": "Produtos têxteis",
    "3.14": "Artigos do vestuário",
    "3.15": "Couros e calçados",
    "3.16": "Produtos de madeira",
    "3.17": "Celulose e papel",
    "3.18": "Impressão e gravações",
    "3.19": "Coque e biocombustíveis",
    "3.20": "Produtos químicos",
    "3.21": "Farmacêuticos e farmoquímicos",
    "3.22": "Borracha e material plástico",
    "3.23": "Minerais não metálicos",
    "3.24": "Metalurgia",
    "3.25": "Produtos de metal",
    "3.26": "Informática e eletrônicos",
    "3.27": "Máquinas e aparelhos elétricos",
    "3.28": "Máquinas e equipamentos",
    "3.29": "Veículos automotores",
    "3.30": "Outros equipamentos de transporte",
    "3.31": "Fabricação de móveis",
    "3.32": "Produtos diversos",
    "3.33": "Manutenção e reparação de máquinas",
}


def obter_nome_curto_setor(nome_completo):
    """Retorna o rótulo conciso e padronizado do setor industrial."""
    for chave, nome_curto in MAPA_NOMES_CURTOS_SETORES.items():
        if nome_completo.startswith(chave):
            return nome_curto
    return nome_completo


# Locais disponíveis
locais_disponiveis = sorted(df_completo["LOCAL"].dropna().unique().tolist())


def render_dashboard_uf(df_uf, nome_local, prefixo):
    """Renderiza a estrutura completa de análise industrial para a localidade especificada."""

    # Seletor de Medida / Indicador com valor padrão inteligente por abrangência
    lista_medidas = list(opcoes_medidas.keys())
    if nome_local != "Brasil" and "Variação acumulada no ano (%)" in lista_medidas:
        idx_padrao_medida = lista_medidas.index("Variação acumulada no ano (%)")
    else:
        idx_padrao_medida = 0

    col_med1, _ = st.columns([2, 1])
    with col_med1:
        medida_label = st.selectbox(
            label="Medida / Indicador",
            options=lista_medidas,
            index=idx_padrao_medida,
            key=f"{prefixo}_medida",
            help=f"Selecione o indicador da PIM que deseja analisar para {nome_local}.",
        )
        var_escolhida = opcoes_medidas[medida_label]

    df_var = (
        df_uf[df_uf["VARIAVEL"] == var_escolhida]
        .drop_duplicates(subset=["Data", "SUBGRUPOS"], keep="last")
        .copy()
    )

    # ----------------------------------------------------
    # QUADRO INTEGRADO: PANORAMA DA INDÚSTRIA
    # ----------------------------------------------------
    # Determinar a data de referência oficial mais recente com dados consolidados da localidade
    # Prioriza as métricas principais da Indústria Geral (M/M-12, Acumulado no Ano ou Número-índice)
    sub_ref = df_uf[
        df_uf["SUBGRUPOS"].str.contains("1 Ind", case=False, na=False, regex=False)
        & df_uf["VARIAVEL"].str.contains("mesmo m|acumulada no ano|Número-índice|Numero-indice", case=False, na=False, regex=True)
        & ~df_uf["VARIAVEL"].str.contains("Influ", case=False, na=False, regex=False)
    ].dropna(subset=["VALOR"])

    if not sub_ref.empty:
        data_ref = sub_ref["Data"].max()
    else:
        data_ref = df_uf.dropna(subset=["VALOR"])["Data"].max()

    data_ref_label = data_ref.strftime("%m/%Y")

    def extrair_indicadores(subgrupo_termo, target_date):
        df_sub = df_uf[
            df_uf["SUBGRUPOS"].str.contains(subgrupo_termo, case=False, na=False, regex=False)
        ]
        if df_sub.empty:
            return {"mm1": (None, None), "m12": (None, None), "ano": (None, None), "12m": (None, None)}

        def extrair_metrica(termo):
            sub = df_sub[
                df_sub["VARIAVEL"].str.contains("Varia", case=False, na=False, regex=False)
                & df_sub["VARIAVEL"].str.contains(termo, case=False, na=False, regex=False)
                & ~df_sub["VARIAVEL"].str.contains("Influ", case=False, na=False, regex=False)
                & (df_sub["Data"] == target_date)
            ].dropna(subset=["VALOR"])
            if not sub.empty:
                ult = sub.iloc[-1]
                return ult["VALOR"], ult["Data pt"]
            return None, None

        return {
            "mm1": extrair_metrica("imediatamente anterior"),
            "m12": extrair_metrica("mesmo m"),
            "ano": extrair_metrica("acumulada no ano"),
            "12m": extrair_metrica("acumulada em 12 meses"),
        }

    dados_ig = extrair_indicadores("1 Ind", data_ref)
    dados_ext = extrair_indicadores("2 Ind", data_ref)
    dados_transf = extrair_indicadores("3 Ind", data_ref)

    with st.container(border=True):
        # 1. Indústria Geral
        st.markdown(
            f'<div class="quadro-titulo-geral">Panorama da Indústria Geral — {nome_local} ({data_ref_label})</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            val, d_ref = dados_ig["mm1"]
            st.metric(
                label=f"Variação M/M-1 (c/ ajuste){f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                value=f"{val:+.2f}%" if val is not None else "N/D",
                delta=f"{val:+.2f}%" if val is not None else None,
            )
        with c2:
            val, d_ref = dados_ig["m12"]
            st.metric(
                label=f"Variação M/M-12 (interanual){f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                value=f"{val:+.2f}%" if val is not None else "N/D",
                delta=f"{val:+.2f}%" if val is not None else None,
            )
        with c3:
            val, d_ref = dados_ig["ano"]
            st.metric(
                label=f"Acumulado no Ano{f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                value=f"{val:+.2f}%" if val is not None else "N/D",
                delta=f"{val:+.2f}%" if val is not None else None,
            )
        with c4:
            val, d_ref = dados_ig["12m"]
            st.metric(
                label=f"Acumulado em 12 Meses{f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                value=f"{val:+.2f}%" if val is not None else "N/D",
                delta=f"{val:+.2f}%" if val is not None else None,
            )

        # 2. Indústria Extrativa (se disponível)
        if any(v[0] is not None for v in dados_ext.values()):
            st.markdown('<div class="divisor-quadro"></div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="quadro-titulo-sub">Indústria Extrativa — {nome_local}</div>',
                unsafe_allow_html=True,
            )
            _, e1, e2, e3, e4 = st.columns([0.05, 1, 1, 1, 1])
            with e1:
                val, d_ref = dados_ext["mm1"]
                st.metric(
                    label=f"Variação M/M-1 (c/ ajuste){f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )
            with e2:
                val, d_ref = dados_ext["m12"]
                st.metric(
                    label=f"Variação M/M-12 (interanual){f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )
            with e3:
                val, d_ref = dados_ext["ano"]
                st.metric(
                    label=f"Acumulado no Ano{f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )
            with e4:
                val, d_ref = dados_ext["12m"]
                st.metric(
                    label=f"Acumulado em 12 Meses{f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )

        # 3. Indústria de Transformação (se disponível)
        if any(v[0] is not None for v in dados_transf.values()):
            st.markdown('<div class="divisor-quadro"></div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="quadro-titulo-sub">Indústria de Transformação — {nome_local}</div>',
                unsafe_allow_html=True,
            )
            _, t1, t2, t3, t4 = st.columns([0.05, 1, 1, 1, 1])
            with t1:
                val, d_ref = dados_transf["mm1"]
                st.metric(
                    label=f"Variação M/M-1 (c/ ajuste){f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )
            with t2:
                val, d_ref = dados_transf["m12"]
                st.metric(
                    label=f"Variação M/M-12 (interanual){f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )
            with t3:
                val, d_ref = dados_transf["ano"]
                st.metric(
                    label=f"Acumulado no Ano{f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )
            with t4:
                val, d_ref = dados_transf["12m"]
                st.metric(
                    label=f"Acumulado em 12 Meses{f' [{d_ref}]' if d_ref and d_ref != data_ref_label else ''}",
                    value=f"{val:+.2f}%" if val is not None else "N/D",
                    delta=f"{val:+.2f}%" if val is not None else None,
                )

    if nome_local != "Brasil":
        st.markdown(
            f'<div class="nota-metodologica">'
            f'<strong>Nota Metodológica (IBGE - PIM Regional):</strong> O IBGE calcula a série com ajuste sazonal (M/M-1) '
            f'exclusivamente para a <strong>Indústria Geral</strong> no âmbito regional ({nome_local}). '
            f'Para os setores específicos (<strong>Indústria Extrativa</strong> e <strong>Indústria de Transformação</strong>), '
            f'a pesquisa regional não dispõe de modelo de dessazonalização, razão pela qual a métrica consta como <strong>N/D</strong>. '
            f'O acompanhamento setorial nesses segmentos é realizado com base nos indicadores da <strong>série original</strong> '
            f'(<em>Variação interanual M/M-12</em>, <em>Acumulado no Ano</em> e <em>Acumulado em 12 Meses</em>), '
            f'nas quais a sazonalidade é naturalmente neutralizada pela comparação entre períodos homólogos.'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.write("---")

    # ----------------------------------------------------
    # 1. SEÇÃO: EVOLUÇÃO TEMPORAL DOS SETORES
    # ----------------------------------------------------
    st.write("#### Evolução dos setores industriais")

    # Apenas setores que efetivamente possuem observações divulgadas para esta localidade e variável
    setores_com_dados = (
        df_var.dropna(subset=["VALOR"])["SUBGRUPOS"]
        .unique()
        .tolist()
    )
    todos_os_setores = sorted([s for s in df_var["SUBGRUPOS"].dropna().unique() if s in setores_com_dados])

    # Lista de todos os setores investigados na PIM para esta variável no âmbito nacional
    todos_setores_pesquisa = sorted(
        df_completo[df_completo["VARIAVEL"] == var_escolhida]
        .dropna(subset=["VALOR"])["SUBGRUPOS"]
        .unique()
        .tolist()
    )
    if not todos_setores_pesquisa:
        todos_setores_pesquisa = sorted(df_completo["SUBGRUPOS"].dropna().unique().tolist())

    setores_sem_dados = [s for s in todos_setores_pesquisa if s not in todos_os_setores]

    # Identificar se a Indústria Geral é equivalente à Indústria de Transformação (UF sem extrativa no IBGE)
    tem_extrativa = any(s.startswith("2 Ind") for s in todos_os_setores)
    sub_1_presente = any(s.startswith("1 Ind") for s in todos_os_setores)
    sub_3_presente = any(s.startswith("3 Ind") for s in todos_os_setores)
    geral_equiv_transf = sub_1_presente and sub_3_presente and not tem_extrativa

    if geral_equiv_transf:
        # Em UFs sem extrativa, Geral == Transformação. Selecionamos por padrão a Indústria Geral e os ramos principais
        ramos_desagregados = [s for s in todos_os_setores if not any(s.startswith(p) for p in ["1 Ind", "2 Ind", "3 Ind"])]
        padrao_setores = [s for s in todos_os_setores if s.startswith("1 Ind")] + ramos_desagregados[:2]
    else:
        padrao_setores = [
            s for s in todos_os_setores if any(s.startswith(p) for p in ["1 Ind", "2 Ind", "3 Ind"])
        ]

    if not padrao_setores:
        padrao_setores = todos_os_setores[:3]

    setores_selecionados = st.multiselect(
        label="Setores / Atividades Industriais",
        options=todos_os_setores,
        default=padrao_setores,
        format_func=obter_nome_curto_setor,
        key=f"{prefixo}_setores_selecionados",
        help="Selecione um ou mais setores para visualizar e comparar as curvas temporais.",
    )

    if setores_sem_dados and nome_local != "Brasil":
        st.caption(
            f"ℹ️ Exibindo os **{len(todos_os_setores)} setores industriais** pesquisados pelo IBGE em {nome_local} "
            f"({len(setores_sem_dados)} ramos da indústria nacional não integram o plano amostral desta UF)."
        )

    if not setores_selecionados:
        st.warning("Selecione pelo menos um setor industrial para exibir a série temporal.")
    else:
        df_graf_valido = (
            df_var[df_var["SUBGRUPOS"].isin(setores_selecionados)]
            .dropna(subset=["VALOR"])
            .copy()
        )
        anos_totais = sorted(df_graf_valido["Ano"].dropna().unique().astype(int).tolist())

        if not anos_totais:
            st.info("Nenhum dado temporal disponível para os setores selecionados.")
        else:
            ano_inicio_default = min(anos_totais)

            ano_inicial, ano_final = st.select_slider(
                "Intervalo (Anos)",
                options=anos_totais,
                value=(ano_inicio_default, max(anos_totais)),
                key=f"{prefixo}_slider_anos",
            )

            df_graf_linha = df_graf_valido[
                (df_graf_valido["Ano"] >= ano_inicial) & (df_graf_valido["Ano"] <= ano_final)
            ].copy()
            df_graf_linha["Setor"] = df_graf_linha["SUBGRUPOS"].apply(obter_nome_curto_setor)

            if df_graf_linha.empty:
                st.info("Nenhum registro para o período e setores selecionados.")
            else:
                v_min = df_graf_linha["VALOR"].min()
                v_max = df_graf_linha["VALOR"].max()
                eixo_y_min = set_y_min(v_min) if pd.notna(v_min) else 0
                eixo_y_max = set_y_max(v_max) if pd.notna(v_max) else 100

                margem_y = (eixo_y_max - eixo_y_min) * 0.08
                eixo_y_min -= margem_y
                eixo_y_max += margem_y

                data_min_graf = df_graf_linha["Data"].min()
                data_max_graf = df_graf_linha["Data"].max()

                setores_cobertura_recente = []
                for s in setores_selecionados:
                    sub_s = df_graf_linha[df_graf_linha["SUBGRUPOS"] == s]
                    if not sub_s.empty:
                        min_s = sub_s["Data"].min()
                        if min_s > data_min_graf:
                            setores_cobertura_recente.append((s, min_s.strftime("%m/%Y")))

                nomes_curtos_selecionados = [obter_nome_curto_setor(s) for s in setores_selecionados]
                palette_setores = [
                    "#002d62", "#0072ce", "#e11d48", "#0d9488", "#d97706",
                    "#7c3aed", "#059669", "#ea580c", "#0891b2", "#4f46e5",
                    "#db2777", "#ca8a04", "#16a34a", "#2563eb", "#9333ea",
                ]
                cores_setores_map = {
                    nc: palette_setores[i % len(palette_setores)]
                    for i, nc in enumerate(nomes_curtos_selecionados)
                }

                grafico_linha = (
                    alt.Chart(df_graf_linha)
                    .mark_line(strokeWidth=2.8)
                    .encode(
                        x=alt.X(
                            "Data:T",
                            axis=alt.Axis(format="%m/%Y", labelAngle=-45, title="Mês/Ano"),
                            scale=alt.Scale(domain=[data_min_graf, data_max_graf]),
                        ),
                        y=alt.Y(
                            "VALOR:Q",
                            scale=alt.Scale(domain=[eixo_y_min, eixo_y_max]),
                            title=medida_label,
                        ),
                        color=alt.Color(
                            "Setor:N",
                            scale=alt.Scale(
                                domain=nomes_curtos_selecionados,
                                range=[cores_setores_map[nc] for nc in nomes_curtos_selecionados],
                            ),
                            legend=alt.Legend(title="Setor", orient="bottom"),
                        ),
                        tooltip=[
                            alt.Tooltip("Data:T", title="Data", format="%m/%Y"),
                            alt.Tooltip("Setor:N", title="Setor"),
                            alt.Tooltip("SUBGRUPOS:N", title="Descrição Técnica Oficial (IBGE)"),
                            alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                        ],
                    )
                )

                max_list = []
                min_list = []
                ult_list = []
                resumo_extremos = []
                is_infl = "(p.p.)" in medida_label
                is_pct = ("(%)" in medida_label or "Varia" in medida_label) and not is_infl

                def fmt_val(v):
                    if pd.isna(v):
                        return "N/D"
                    if is_infl:
                        return f"{v:+.2f} p.p."
                    if is_pct:
                        return f"{v:+.2f}%"
                    return f"{v:.2f}"

                def fmt_dif(d):
                    if pd.isna(d):
                        return "N/D"
                    unidade = "p.p." if (is_pct or is_infl) else "pts"
                    val = 0.0 if abs(d) < 1e-7 else d
                    return f"{val:+.2f} {unidade}"

                for s in setores_selecionados:
                    nome_curto_s = obter_nome_curto_setor(s)
                    sub_per = df_graf_linha[df_graf_linha["SUBGRUPOS"] == s].dropna(subset=["VALOR"])
                    sub_hist = df_var[df_var["SUBGRUPOS"] == s].dropna(subset=["VALOR"])

                    if not sub_per.empty:
                        idx_max_per = sub_per["VALOR"].idxmax()
                        idx_min_per = sub_per["VALOR"].idxmin()
                        r_max = sub_per.loc[idx_max_per].to_dict()
                        r_min = sub_per.loc[idx_min_per].to_dict()

                        sub_per_sorted = sub_per.sort_values("Data")
                        r_ult = sub_per_sorted.iloc[-1].to_dict()
                        idx_ult = sub_per_sorted.index[-1]

                        v_ult = r_ult["VALOR"]
                        v_max_per = r_max["VALOR"]
                        v_min_per = r_min["VALOR"]

                        dif_max_per = v_ult - v_max_per
                        dif_min_per = v_ult - v_min_per

                        if not sub_hist.empty:
                            idx_max_hist = sub_hist["VALOR"].idxmax()
                            idx_min_hist = sub_hist["VALOR"].idxmin()
                            r_max_hist = sub_hist.loc[idx_max_hist]
                            r_min_hist = sub_hist.loc[idx_min_hist]
                            v_max_hist = r_max_hist["VALOR"]
                            v_min_hist = r_min_hist["VALOR"]
                            dif_max_hist = v_ult - v_max_hist
                            dif_min_hist = v_ult - v_min_hist
                        else:
                            r_max_hist = r_max
                            r_min_hist = r_min
                            v_max_hist = v_max_per
                            v_min_hist = v_min_per
                            dif_max_hist = dif_max_per
                            dif_min_hist = dif_min_per

                        # Pontos históricos de Máximo e Mínimo (apenas se anteriores ao ponto final)
                        if idx_max_per != idx_ult:
                            r_max["Setor"] = nome_curto_s
                            r_max["Rotulo"] = f"Máx: {fmt_val(v_max_per)} ({r_max['Data pt']})"
                            max_list.append(r_max)
                        if idx_min_per != idx_ult:
                            r_min["Setor"] = nome_curto_s
                            r_min["Rotulo"] = f"Mín: {fmt_val(v_min_per)} ({r_min['Data pt']})"
                            min_list.append(r_min)

                        # Ponto terminal
                        r_ult_dict = dict(r_ult)
                        r_ult_dict["Setor"] = nome_curto_s
                        r_ult_dict["Dif_Max_Per"] = fmt_dif(dif_max_per)
                        r_ult_dict["Dif_Min_Per"] = fmt_dif(dif_min_per)
                        r_ult_dict["Dif_Max_Hist"] = fmt_dif(dif_max_hist)
                        r_ult_dict["Dif_Min_Hist"] = fmt_dif(dif_min_hist)
                        r_ult_dict["Val_Formatado"] = fmt_val(v_ult)
                        r_ult_dict["Rotulo"] = f"Últ: {fmt_val(v_ult)}"
                        ult_list.append(r_ult_dict)

                        resumo_extremos.append(
                            {
                                "Setor": nome_curto_s,
                                "Descrição Oficial (IBGE)": s,
                                "cor": cores_setores_map.get(nome_curto_s, "#002d62"),
                                "Último Registrado": f"{fmt_val(v_ult)} ({r_ult['Data pt']})",
                                "Dif. vs Máx (Período)": fmt_dif(dif_max_per),
                                "Dif. vs Mín (Período)": fmt_dif(dif_min_per),
                                "Máximo no Período": f"{fmt_val(v_max_per)} ({r_max['Data pt']})",
                                "Mínimo no Período": f"{fmt_val(v_min_per)} ({r_min['Data pt']})",
                                "Dif. vs Máx Histórico": fmt_dif(dif_max_hist),
                                "Dif. vs Mín Histórico": fmt_dif(dif_min_hist),
                                "Máximo Histórico Completo": f"{fmt_val(v_max_hist)} ({r_max_hist['Data pt']})",
                                "Mínimo Histórico Completo": f"{fmt_val(v_min_hist)} ({r_min_hist['Data pt']})",
                            }
                        )

                df_max = pd.DataFrame(max_list)
                df_min = pd.DataFrame(min_list)
                df_ult = pd.DataFrame(ult_list)

                camadas = [grafico_linha]

                if not df_max.empty:
                    pontos_max = (
                        alt.Chart(df_max)
                        .mark_point(size=90, filled=True, shape="circle")
                        .encode(
                            x="Data:T",
                            y="VALOR:Q",
                            color=alt.Color(
                                "Setor:N",
                                scale=alt.Scale(
                                    domain=nomes_curtos_selecionados,
                                    range=[cores_setores_map[nc] for nc in nomes_curtos_selecionados],
                                ),
                                legend=None,
                            ),
                            tooltip=[
                                alt.Tooltip("Setor:N", title="Setor"),
                                alt.Tooltip("SUBGRUPOS:N", title="Descrição Técnica Oficial (IBGE)"),
                                alt.Tooltip("Data:T", title="Data do Máximo", format="%m/%Y"),
                                alt.Tooltip("VALOR:Q", title="Valor Máximo", format="+.2f" if (is_pct or is_infl) else ".2f"),
                            ],
                        )
                    )
                    rotulos_max = (
                        alt.Chart(df_max)
                        .mark_text(fontSize=11, fontWeight="bold", dy=-12, align="center")
                        .encode(
                            x="Data:T",
                            y="VALOR:Q",
                            text="Rotulo:N",
                            color=alt.Color(
                                "Setor:N",
                                scale=alt.Scale(
                                    domain=nomes_curtos_selecionados,
                                    range=[cores_setores_map[nc] for nc in nomes_curtos_selecionados],
                                ),
                                legend=None,
                            ),
                        )
                    )
                    camadas.extend([pontos_max, rotulos_max])

                if not df_min.empty:
                    pontos_min = (
                        alt.Chart(df_min)
                        .mark_point(size=90, filled=True, shape="circle")
                        .encode(
                            x="Data:T",
                            y="VALOR:Q",
                            color=alt.Color(
                                "Setor:N",
                                scale=alt.Scale(
                                    domain=nomes_curtos_selecionados,
                                    range=[cores_setores_map[nc] for nc in nomes_curtos_selecionados],
                                ),
                                legend=None,
                            ),
                            tooltip=[
                                alt.Tooltip("Setor:N", title="Setor"),
                                alt.Tooltip("SUBGRUPOS:N", title="Descrição Técnica Oficial (IBGE)"),
                                alt.Tooltip("Data:T", title="Data do Mínimo", format="%m/%Y"),
                                alt.Tooltip("VALOR:Q", title="Valor Mínimo", format="+.2f" if (is_pct or is_infl) else ".2f"),
                            ],
                        )
                    )
                    rotulos_min = (
                        alt.Chart(df_min)
                        .mark_text(fontSize=11, fontWeight="bold", dy=14, align="center")
                        .encode(
                            x="Data:T",
                            y="VALOR:Q",
                            text="Rotulo:N",
                            color=alt.Color(
                                "Setor:N",
                                scale=alt.Scale(
                                    domain=nomes_curtos_selecionados,
                                    range=[cores_setores_map[nc] for nc in nomes_curtos_selecionados],
                                ),
                                legend=None,
                            ),
                        )
                    )
                    camadas.extend([pontos_min, rotulos_min])

                if not df_ult.empty:
                    pontos_ult = (
                        alt.Chart(df_ult)
                        .mark_point(size=110, filled=True, shape="diamond")
                        .encode(
                            x="Data:T",
                            y="VALOR:Q",
                            color=alt.Color(
                                "Setor:N",
                                scale=alt.Scale(
                                    domain=nomes_curtos_selecionados,
                                    range=[cores_setores_map[nc] for nc in nomes_curtos_selecionados],
                                ),
                                legend=None,
                            ),
                            tooltip=[
                                alt.Tooltip("Setor:N", title="Setor"),
                                alt.Tooltip("SUBGRUPOS:N", title="Descrição Técnica Oficial (IBGE)"),
                                alt.Tooltip("Data:T", title="Última Data", format="%m/%Y"),
                                alt.Tooltip("Val_Formatado:N", title="Último Valor"),
                                alt.Tooltip("Dif_Max_Per:N", title="Dif. vs Máx (Período)"),
                                alt.Tooltip("Dif_Min_Per:N", title="Dif. vs Mín (Período)"),
                                alt.Tooltip("Dif_Max_Hist:N", title="Dif. vs Máx Histórico"),
                                alt.Tooltip("Dif_Min_Hist:N", title="Dif. vs Mín Histórico"),
                            ],
                        )
                    )
                    camadas.append(pontos_ult)

                    if len(setores_selecionados) == 1:
                        rotulos_ult = (
                            alt.Chart(df_ult)
                            .mark_text(fontSize=11, fontWeight="bold", align="right", dx=-10, dy=-12)
                            .encode(
                                x="Data:T",
                                y="VALOR:Q",
                                text="Rotulo:N",
                                color=alt.Color(
                                    "Setor:N",
                                    scale=alt.Scale(
                                        domain=nomes_curtos_selecionados,
                                        range=[cores_setores_map[nc] for nc in nomes_curtos_selecionados],
                                    ),
                                    legend=None,
                                ),
                            )
                        )
                        camadas.append(rotulos_ult)

                if (is_pct or is_infl) and (v_min < 0 < v_max):
                    linha_zero = (
                        alt.Chart(pd.DataFrame({"y": [0]}))
                        .mark_rule(color="#94a3b8", strokeDash=[3, 3])
                        .encode(y="y:Q")
                    )
                    camadas.append(linha_zero)

                grafico_linha_final = alt.layer(*camadas).properties(height=450)
                if pt_format and pt_time_format:
                    grafico_linha_final["usermeta"] = {
                        "embedOptions": {
                            "formatLocale": pt_format,
                            "timeFormatLocale": pt_time_format,
                        }
                    }

                # Cards de Destaque: Último Registrado e Diferenciais no Período
                if resumo_extremos:
                    st.markdown("##### Destaques do Último Período e Diferenciais")
                    chunk_size = 4 if len(resumo_extremos) >= 4 else len(resumo_extremos)
                    for i in range(0, len(resumo_extremos), chunk_size):
                        chunk = resumo_extremos[i : i + chunk_size]
                        cols = st.columns(len(chunk))
                        for col, item in zip(cols, chunk):
                            nome = item["Setor"]
                            desc_oficial = item.get("Descrição Oficial (IBGE)", nome)
                            cor = item.get("cor", "#002d62")
                            ult = item["Último Registrado"]
                            dif_max = item["Dif. vs Máx (Período)"]
                            subtitulo_equivalencia = ""
                            if geral_equiv_transf and desc_oficial.startswith("3 Ind"):
                                subtitulo_equivalencia = "(100% da Indústria Geral)"

                            with col:
                                st.markdown(
                                    card_destaque_html(nome, cor, ult, dif_max, subtitulo_equivalencia, tooltip_desc=desc_oficial),
                                    unsafe_allow_html=True,
                                )

                st.altair_chart(grafico_linha_final, theme=None, use_container_width=True)

                if any(s.startswith("1 Ind") for s in setores_selecionados) and any(s.startswith("3 Ind") for s in setores_selecionados) and geral_equiv_transf:
                    st.markdown(
                        f'<div class="nota-metodologica">'
                        f'<strong>Nota Metodológica (IBGE - PIM Regional):</strong> Em {nome_local}, a <strong>Indústria Geral</strong> '
                        f'é composta integralmente pela <strong>Indústria de Transformação</strong> (peso de 100%), pois o IBGE não investiga a seção de '
                        f'Indústrias Extrativas no estado. Por essa razão estrutural da pesquisa, as duas séries possuem <strong>valores exatamente idênticos</strong> ao longo de todo o histórico.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                if setores_cobertura_recente:
                    detalhes_setores = "; ".join([f"<strong title='{s}'>{obter_nome_curto_setor(s)}</strong> (a partir de {dt})" for s, dt in setores_cobertura_recente])
                    st.markdown(
                        f'<div class="nota-metodologica">'
                        f'<strong>Nota de Cobertura Histórica (IBGE - PIM Regional):</strong> '
                        f'A série histórica exibida contempla todos os dados oficiais disponíveis desde {data_min_graf.strftime("%m/%Y")}. '
                        f'Para {nome_local}, os seguintes setores foram incorporados à pesquisa pelo IBGE em revisões posteriores: {detalhes_setores}.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                if setores_sem_dados and nome_local != "Brasil":
                    st.markdown(
                        f'<div class="nota-metodologica">'
                        f'<strong>Nota Metodológica Oficial (IBGE - Cobertura Amostral em {nome_local}):</strong> '
                        f'A Pesquisa Industrial Mensal Regional do IBGE investiga exclusivamente as atividades com relevância estatística '
                        f'mínima na estrutura produtiva do estado. Em <strong>{nome_local}</strong>, o IBGE <strong>não investiga ou não divulga '
                        f'{len(setores_sem_dados)} ramos da indústria nacional</strong>'
                        f'{" (incluindo a seção de <em>Indústrias Extrativas</em>, de modo que a Transformação representa 100% da Indústria Geral)" if not tem_extrativa else ""}. '
                        f'Para consultar esses setores no plano nacional consolidado, consulte a aba <strong>PIM-BR (Brasil)</strong>.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander(f"📋 Ramos industriais não investigados pelo IBGE em {nome_local} ({len(setores_sem_dados)})"):
                        st.markdown(
                            f'<div style="font-size: 0.83rem; color: #64748b; margin-bottom: 8px;">'
                            f'Atividades industriais sem amostragem na PIM Regional devido ao critério de representatividade estatística local:'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        num_cols = 3
                        cols_exp = st.columns(num_cols)
                        itens_por_col = (len(setores_sem_dados) + num_cols - 1) // num_cols

                        for col_idx, col in enumerate(cols_exp):
                            chunk = setores_sem_dados[col_idx * itens_por_col : (col_idx + 1) * itens_por_col]
                            if chunk:
                                html_itens = "".join([
                                    f'<li style="margin-bottom: 3px;" title="{s}"><strong>{obter_nome_curto_setor(s)}</strong></li>'
                                    for s in chunk
                                ])
                                with col:
                                    st.markdown(
                                        f'<ul style="margin: 0; padding-left: 16px; font-size: 0.83rem; color: #334155; line-height: 1.45;">'
                                        f'{html_itens}'
                                        f'</ul>',
                                        unsafe_allow_html=True,
                                    )

                if resumo_extremos:
                    st.markdown("##### Extremos da Série e Diferenciais do Último Registro por Setor")
                    df_tab_extremos = pd.DataFrame(resumo_extremos)
                    cols_tab = [c for c in df_tab_extremos.columns if c != "cor"]
                    st.dataframe(df_tab_extremos[cols_tab], use_container_width=True, hide_index=True)

    st.write("---")

    # ----------------------------------------------------
    # 2. SEÇÃO: COMPARAÇÃO SETORIAL (RANKING EM BARRAS)
    # ----------------------------------------------------
    st.write("#### Comparação setorial no período selecionado")

    df_var_valido = df_var.dropna(subset=["VALOR"])
    contagem_ramos_data = df_var_valido.groupby("Data")["SUBGRUPOS"].nunique()
    datas_com_multiplos = contagem_ramos_data[contagem_ramos_data > 1].index.sort_values(ascending=False).tolist()
    datas_todas_validas = sorted(df_var_valido["Data"].unique().tolist(), reverse=True)
    datas_ordenadas = datas_com_multiplos if datas_com_multiplos else datas_todas_validas
    if not datas_ordenadas:
        datas_ordenadas = sorted(df_var["Data"].dropna().unique().tolist(), reverse=True)
    mapa_datas = {d.strftime("%m/%Y"): d for d in pd.to_datetime(datas_ordenadas)}

    col_r1, col_r2 = st.columns([1, 1])
    with col_r1:
        mes_escolhido_str = st.selectbox(
            "Mês de Referência para Comparação",
            options=list(mapa_datas.keys()),
            index=0,
            key=f"{prefixo}_mes_ranking_{medida_label}",
        )
        mes_escolhido = mapa_datas[mes_escolhido_str]

    with col_r2:
        filtro_ramos = st.radio(
            "Escopo da Comparação",
            options=["Todos os setores", "Apenas ramos desagregados"],
            index=0,
            horizontal=True,
            key=f"{prefixo}_escopo_ranking",
        )

    df_ranking = df_var[df_var["Data"] == mes_escolhido].copy()

    if "Apenas ramos desagregados" in filtro_ramos:
        df_ranking = df_ranking[
            ~df_ranking["SUBGRUPOS"].str.contains(r"^(?:1|2|3)\s*Ind", regex=True, na=False)
        ]

    df_ranking = df_ranking.dropna(subset=["VALOR"]).sort_values("VALOR", ascending=False)

    if "ajuste sazonal" in medida_label.lower() and len(df_ranking) <= 1 and nome_local != "Brasil":
        st.markdown(
            f'<div class="nota-metodologica">'
            f'<strong>Nota Metodológica (IBGE - PIM Regional):</strong> O IBGE calcula a série com ajuste sazonal (M/M-1) '
            f'exclusivamente para a <strong>Indústria Geral</strong> nas pesquisas regionais ({nome_local}). '
            f'Para analisar a comparação detalhada entre os ramos de atividade da indústria, selecione indicadores da '
            f'<strong>série original</strong>, tais como a <strong>Variação acumulada no ano (%)</strong> ou a <strong>Variação M/M-12 (%)</strong>.'
            f'</div>',
            unsafe_allow_html=True,
        )

    if df_ranking.empty:
        st.info(
            f"Nenhum ramo de atividade com valor divulgado para {nome_local} no mês de {mes_escolhido_str}. "
            "Selecione um mês com dados disponíveis ou ajuste o escopo da comparação."
        )
    else:
        df_ranking = df_ranking.copy()
        df_ranking["Setor"] = df_ranking["SUBGRUPOS"].apply(obter_nome_curto_setor)
        df_ranking["Cor_Barra"] = df_ranking["VALOR"].apply(
            lambda v: "#002d62" if v >= 0 else "#b90e0c"
        )

        grafico_barras = (
            alt.Chart(df_ranking)
            .mark_bar()
            .encode(
                x=alt.X("VALOR:Q", title=medida_label),
                y=alt.Y(
                    "Setor:N",
                    sort=alt.EncodingSortField(field="VALOR", order="descending"),
                    title="",
                ),
                color=alt.Color("Cor_Barra:N", scale=None, legend=None),
                tooltip=[
                    alt.Tooltip("Setor:N", title="Setor"),
                    alt.Tooltip("SUBGRUPOS:N", title="Descrição Técnica Oficial (IBGE)"),
                    alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                ],
            )
            .properties(height=max(380, len(df_ranking) * 26))
        )

        rotulos_barras = (
            alt.Chart(df_ranking)
            .mark_text(
                align=alt.expr("datum.VALOR >= 0 ? 'left' : 'right'"),
                dx=alt.expr("datum.VALOR >= 0 ? 6 : -6"),
                fontSize=11,
            )
            .encode(
                x="VALOR:Q",
                y=alt.Y(
                    "Setor:N",
                    sort=alt.EncodingSortField(field="VALOR", order="descending"),
                ),
                text=alt.Text(
                    "VALOR:Q",
                    format="+.2f" if "%" in medida_label or "p.p." in medida_label else ".2f",
                ),
                color=alt.value("#1e293b"),
            )
        )

        grafico_barras_final = grafico_barras + rotulos_barras
        if pt_format and pt_time_format:
            grafico_barras_final["usermeta"] = {
                "embedOptions": {
                    "formatLocale": pt_format,
                    "timeFormatLocale": pt_time_format,
                }
            }

        st.altair_chart(grafico_barras_final, theme=None, use_container_width=True)

    st.write("---")

    # ----------------------------------------------------
    # 3. SEÇÃO: DADOS DETALHADOS E EXPORTAÇÃO
    # ----------------------------------------------------
    st.write("#### Dados detalhados")

    df_tab = df_var.copy()
    df_tab["Periodo"] = df_tab["Data"].dt.strftime("%Y-%m")

    anos_tabela = sorted(df_tab["Ano"].dropna().unique().astype(int).tolist())
    if anos_tabela:
        ano_tab_padrao = max(min(anos_tabela), max(anos_tabela) - 4)
        ano_corte = st.slider(
            "Exibir histórico na tabela a partir de:",
            min_value=min(anos_tabela),
            max_value=max(anos_tabela),
            value=ano_tab_padrao,
            key=f"{prefixo}_slider_tabela",
        )

        df_tab_filtrada = df_tab[df_tab["Ano"] >= ano_corte]
        df_pivot = df_tab_filtrada.pivot_table(
            index="SUBGRUPOS",
            columns="Periodo",
            values="VALOR",
            aggfunc="last",
        )

        setores_existentes = [s for s in todos_os_setores if s in df_pivot.index]
        df_pivot = df_pivot.loc[setores_existentes]

        st.dataframe(
            df_pivot.style.format("{:.2f}", na_rep="-"),
            use_container_width=True,
            height=450,
        )

        df_export_pivot = df_pivot.reset_index()
        colunas_exp = [c for c in ["Data", "SUBGRUPOS", "VARIAVEL", "VALOR", "UNIDADE_DE_MEDIDA"] if c in df_var.columns]
        df_export_serie = df_var[colunas_exp].sort_values(["Data", "SUBGRUPOS"], ascending=[False, True])

        try:
            dados_excel = to_excel2([df_export_pivot, df_export_serie])
            st.download_button(
                label=f"Baixar dados de {nome_local} em Excel",
                data=dados_excel,
                file_name=f"PIM_{nome_local.replace(' ', '_')}_{data_ref_label.replace('/', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"{prefixo}_download_xlsx",
            )
        except Exception as e:
            st.warning(f"Não foi possível gerar a planilha Excel: {e}")


# ==============================================================================
# ABAS LADO A LADO (ESTILO INDÚSTRIA NO MUNDO)
# ==============================================================================
tab_br, tab_rj, tab_reg, tab_comp = st.tabs(
    [
        "PIM-BR (BRASIL)",
        "PIM-RJ (RIO DE JANEIRO)",
        "PIM REGIONAL (DEMAIS ESTADOS)",
        "COMPARAÇÃO ENTRE UFs",
    ]
)

# ----------------------------------------------------
# ABA 1: PIM-BR (BRASIL)
# ----------------------------------------------------
with tab_br:
    df_brasil = df_completo[df_completo["LOCAL"] == "Brasil"]
    if df_brasil.empty:
        st.warning("Dados do Brasil não encontrados na base carregada.")
    else:
        render_dashboard_uf(df_brasil, "Brasil", "pim_br")

# ----------------------------------------------------
# ABA 2: PIM-RJ (RIO DE JANEIRO)
# ----------------------------------------------------
with tab_rj:
    df_rj = df_completo[df_completo["LOCAL"] == "Rio de Janeiro"]
    if df_rj.empty:
        st.warning("Dados do Rio de Janeiro não encontrados na base carregada.")
    else:
        render_dashboard_uf(df_rj, "Rio de Janeiro", "pim_rj")

# ----------------------------------------------------
# ABA 3: PIM REGIONAL (DEMAIS ESTADOS)
# ----------------------------------------------------
with tab_reg:
    demais_estados = [loc for loc in locais_disponiveis if loc not in ["Brasil", "Rio de Janeiro"]]
    if not demais_estados:
        st.info("Nenhuma outra UF encontrada na base carregada.")
    else:
        col_uf, _ = st.columns([2, 2])
        with col_uf:
            uf_selecionada = st.selectbox(
                label="Selecione o Estado (UF)",
                options=demais_estados,
                index=demais_estados.index("São Paulo") if "São Paulo" in demais_estados else 0,
                key="pim_reg_seletor_uf",
                help="Selecione o estado para carregar os indicadores industriais correspondentes.",
            )

        df_uf_sel = df_completo[df_completo["LOCAL"] == uf_selecionada]
        render_dashboard_uf(df_uf_sel, uf_selecionada, f"pim_reg_{uf_selecionada}")

# ----------------------------------------------------
# ABA 4: COMPARAÇÃO ENTRE UFs
# ----------------------------------------------------
with tab_comp:
    st.write("### Comparação entre Unidades da Federação")
    st.markdown(
        "Compare a dinâmica da produção física industrial entre o **Brasil**, **Rio de Janeiro** e demais estados para qualquer setor e métrica."
    )

    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        medida_comp_label = st.selectbox(
            "Medida / Indicador",
            options=list(opcoes_medidas.keys()),
            index=0,
            key="comp_medida",
        )
        var_comp = opcoes_medidas[medida_comp_label]

    df_comp_var = (
        df_completo[df_completo["VARIAVEL"] == var_comp]
        .drop_duplicates(subset=["LOCAL", "Data", "SUBGRUPOS"], keep="last")
        .copy()
    )

    # Setores comuns disponíveis
    setores_comp = sorted(df_comp_var["SUBGRUPOS"].dropna().unique().tolist())
    idx_setor_padrao = 0
    for i, s in enumerate(setores_comp):
        if "1 Ind" in s:
            idx_setor_padrao = i
            break

    with col_c2:
        setor_comp_escolhido = st.selectbox(
            "Setor / Atividade",
            options=setores_comp,
            index=idx_setor_padrao,
            format_func=obter_nome_curto_setor,
            key="comp_setor",
        )

    df_comp_filtrado = df_comp_var[df_comp_var["SUBGRUPOS"] == setor_comp_escolhido].copy()

    df_valido_comp = df_comp_filtrado.dropna(subset=["VALOR"])
    datas_validas = sorted(df_valido_comp["Data"].unique().tolist(), reverse=True)
    if not datas_validas:
        datas_validas = sorted(df_comp_filtrado["Data"].dropna().unique().tolist(), reverse=True)

    mapa_datas_comp = {d.strftime("%m/%Y"): d for d in pd.to_datetime(datas_validas)}
    opcoes_datas_comp = list(mapa_datas_comp.keys())

    # Selecionar inteligentemente como padrão o mês mais recente com divulgação regional (múltiplas UFs)
    contagem_por_data = df_valido_comp.groupby("Data")["LOCAL"].nunique()
    datas_com_multiplas_ufs = contagem_por_data[contagem_por_data > 1].index.sort_values(ascending=False)

    idx_mes_padrao = 0
    if not datas_com_multiplas_ufs.empty:
        data_pref_str = datas_com_multiplas_ufs[0].strftime("%m/%Y")
        if data_pref_str in opcoes_datas_comp:
            idx_mes_padrao = opcoes_datas_comp.index(data_pref_str)

    with col_c3:
        mes_comp_str = st.selectbox(
            "Mês de Referência para o Ranking",
            options=opcoes_datas_comp,
            index=idx_mes_padrao,
            key=f"comp_mes_ref_{medida_comp_label}_{setor_comp_escolhido}",
        )
        mes_comp = mapa_datas_comp[mes_comp_str] if mapa_datas_comp else None

    if "ajuste sazonal" in medida_comp_label.lower() and not setor_comp_escolhido.startswith("1 Ind"):
        st.markdown(
            f'<div class="nota-metodologica">'
            f'<strong>Nota Metodológica (IBGE - PIM Regional):</strong> O IBGE calcula a série com ajuste sazonal (M/M-1) '
            f'exclusivamente para a <strong>Indústria Geral</strong> no âmbito regional. Para setores específicos '
            f'(como <strong>{setor_comp_escolhido}</strong>), a série com ajuste sazonal é calculada exclusivamente para o '
            f'<strong>Brasil consolidado</strong>. Para comparar as UFs neste setor, utilize os indicadores da '
            f'<strong>série original</strong>, tais como a <strong>Variação acumulada no ano (%)</strong> ou a <strong>Variação M/M-12 (%)</strong>.'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Multiselect de UFs para a série temporal
    padrao_ufs_comp = [u for u in ["Brasil", "Rio de Janeiro", "São Paulo", "Minas Gerais"] if u in locais_disponiveis]
    ufs_selecionadas_comp = st.multiselect(
        "Selecione as UFs para comparação temporal:",
        options=locais_disponiveis,
        default=padrao_ufs_comp,
        key="comp_ufs_multiselect",
    )

    if not ufs_selecionadas_comp:
        st.warning("Selecione pelo menos uma UF para visualizar a série temporal comparativa.")
    else:
        df_serie_comp = (
            df_comp_filtrado[df_comp_filtrado["LOCAL"].isin(ufs_selecionadas_comp)]
            .dropna(subset=["VALOR"])
            .copy()
        )
        ufs_com_dados_comp = df_serie_comp["LOCAL"].unique().tolist()
        ufs_sem_dados_comp = [u for u in ufs_selecionadas_comp if u not in ufs_com_dados_comp]
        if ufs_sem_dados_comp:
            st.info(
                f"ℹ️ **Nota Metodológica (Cobertura Amostral):** O setor **{setor_comp_escolhido}** não é investigado "
                f"ou não possui dados divulgados pelo IBGE para: **{', '.join(ufs_sem_dados_comp)}**."
            )

        anos_comp = sorted(df_serie_comp["Ano"].dropna().unique().astype(int).tolist())

        if anos_comp:
            ano_ini_default_comp = min(anos_comp)
            ano_ini_comp, ano_fim_comp = st.select_slider(
                "Intervalo temporal (Anos)",
                options=anos_comp,
                value=(ano_ini_default_comp, max(anos_comp)),
                key="comp_slider_anos",
            )

            df_serie_comp = df_serie_comp[
                (df_serie_comp["Ano"] >= ano_ini_comp) & (df_serie_comp["Ano"] <= ano_fim_comp)
            ]

            # Paleta corporativa Firjan para as UFs com diferenciação clara
            cores_uf_map = {
                "Brasil": "#002d62",         # Azul Marinho Institucional Firjan
                "Rio de Janeiro": "#0072ce",  # Azul Firjan
                "São Paulo": "#e11d48",      # Carmesim
                "Minas Gerais": "#0d9488",   # Verde Petróleo / Teal
                "Paraná": "#7c3aed",         # Roxo
                "Rio Grande do Sul": "#d97706", # Âmbar
                "Santa Catarina": "#2563eb", # Azul Royal
                "Bahia": "#059669",          # Verde Esmeralda
                "Espírito Santo": "#4f46e5", # Índigo
                "Goiás": "#16a34a",          # Verde
                "Ceará": "#ea580c",          # Laranja
                "Pernambuco": "#db2777",     # Magenta
                "Amazonas": "#0891b2",       # Ciano
                "Pará": "#ca8a04",           # Dourado
                "Mato Grosso": "#9333ea",    # Violeta
                "Mato Grosso do Sul": "#0284c7", # Azul Claro
                "Maranhão": "#b45309",       # Marrom
                "Rio Grande do Norte": "#64748b", # Cinza Ardósia
            }
            palette_fallback = [
                "#002d62", "#0072ce", "#e11d48", "#0d9488", "#7c3aed",
                "#d97706", "#2563eb", "#059669", "#4f46e5", "#16a34a",
                "#ea580c", "#db2777", "#0891b2", "#ca8a04", "#9333ea"
            ]
            cores_selecionadas = [
                cores_uf_map.get(u, palette_fallback[i % len(palette_fallback)])
                for i, u in enumerate(ufs_selecionadas_comp)
            ]

            st.markdown("#### Evolução Temporal Comparativa")

            v_min_comp = df_serie_comp["VALOR"].min() if not df_serie_comp.empty else 0
            v_max_comp = df_serie_comp["VALOR"].max() if not df_serie_comp.empty else 100
            eixo_y_min_comp = set_y_min(v_min_comp) if pd.notna(v_min_comp) else 0
            eixo_y_max_comp = set_y_max(v_max_comp) if pd.notna(v_max_comp) else 100

            margem_y_comp = (eixo_y_max_comp - eixo_y_min_comp) * 0.08
            eixo_y_min_comp -= margem_y_comp
            eixo_y_max_comp += margem_y_comp

            data_min_comp = df_serie_comp["Data"].min()
            data_max_comp = df_serie_comp["Data"].max()

            graf_comp_linhas = (
                alt.Chart(df_serie_comp)
                .mark_line(strokeWidth=2.6)
                .encode(
                    x=alt.X(
                        "Data:T",
                        axis=alt.Axis(format="%m/%Y", labelAngle=-45, title="Mês/Ano"),
                        scale=alt.Scale(domain=[data_min_comp, data_max_comp]),
                    ),
                    y=alt.Y(
                        "VALOR:Q",
                        scale=alt.Scale(domain=[eixo_y_min_comp, eixo_y_max_comp]),
                        title=medida_comp_label,
                    ),
                    color=alt.Color(
                        "LOCAL:N",
                        scale=alt.Scale(
                            domain=ufs_selecionadas_comp,
                            range=cores_selecionadas,
                        ),
                        legend=alt.Legend(title="UF / Local", orient="bottom"),
                    ),
                    tooltip=[
                        alt.Tooltip("Data:T", title="Data", format="%m/%Y"),
                        alt.Tooltip("LOCAL:N", title="Local"),
                        alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                    ],
                )
            )

            max_uf_list = []
            min_uf_list = []
            ult_uf_list = []
            resumo_extremos_uf = []
            is_infl_comp = "(p.p.)" in medida_comp_label
            is_pct_comp = ("(%)" in medida_comp_label or "Varia" in medida_comp_label) and not is_infl_comp

            def fmt_val_comp(v):
                if pd.isna(v):
                    return "N/D"
                if is_infl_comp:
                    return f"{v:+.2f} p.p."
                if is_pct_comp:
                    return f"{v:+.2f}%"
                return f"{v:.2f}"

            def fmt_dif_comp(d):
                if pd.isna(d):
                    return "N/D"
                unidade = "p.p." if (is_pct_comp or is_infl_comp) else "pts"
                val = 0.0 if abs(d) < 1e-7 else d
                return f"{val:+.2f} {unidade}"

            for u in ufs_selecionadas_comp:
                sub_uf_per = df_serie_comp[df_serie_comp["LOCAL"] == u].dropna(subset=["VALOR"])
                sub_uf_hist = df_comp_filtrado[df_comp_filtrado["LOCAL"] == u].dropna(subset=["VALOR"])

                if not sub_uf_per.empty:
                    idx_max_uf = sub_uf_per["VALOR"].idxmax()
                    idx_min_uf = sub_uf_per["VALOR"].idxmin()
                    r_max = sub_uf_per.loc[idx_max_uf].to_dict()
                    r_min = sub_uf_per.loc[idx_min_uf].to_dict()

                    sub_uf_sorted = sub_uf_per.sort_values("Data")
                    r_ult = sub_uf_sorted.iloc[-1].to_dict()
                    idx_ult = sub_uf_sorted.index[-1]

                    v_ult = r_ult["VALOR"]
                    v_max_per = r_max["VALOR"]
                    v_min_per = r_min["VALOR"]

                    dif_max_per = v_ult - v_max_per
                    dif_min_per = v_ult - v_min_per

                    if not sub_uf_hist.empty:
                        idx_max_hist = sub_uf_hist["VALOR"].idxmax()
                        idx_min_hist = sub_uf_hist["VALOR"].idxmin()
                        r_max_hist = sub_uf_hist.loc[idx_max_hist]
                        r_min_hist = sub_uf_hist.loc[idx_min_hist]
                        v_max_hist = r_max_hist["VALOR"]
                        v_min_hist = r_min_hist["VALOR"]
                        dif_max_hist = v_ult - v_max_hist
                        dif_min_hist = v_ult - v_min_hist
                    else:
                        r_max_hist = r_max
                        r_min_hist = r_min
                        v_max_hist = v_max_per
                        v_min_hist = v_min_per
                        dif_max_hist = dif_max_per
                        dif_min_hist = dif_min_per

                    # Pontos históricos de Máximo e Mínimo (apenas se anteriores ao ponto final)
                    if idx_max_uf != idx_ult:
                        r_max["Rotulo"] = f"Máx: {fmt_val_comp(v_max_per)} ({r_max['Data pt']})"
                        max_uf_list.append(r_max)
                    if idx_min_uf != idx_ult:
                        r_min["Rotulo"] = f"Mín: {fmt_val_comp(v_min_per)} ({r_min['Data pt']})"
                        min_uf_list.append(r_min)

                    # Ponto terminal
                    r_ult_dict = dict(r_ult)
                    r_ult_dict["Dif_Max_Per"] = fmt_dif_comp(dif_max_per)
                    r_ult_dict["Dif_Min_Per"] = fmt_dif_comp(dif_min_per)
                    r_ult_dict["Dif_Max_Hist"] = fmt_dif_comp(dif_max_hist)
                    r_ult_dict["Dif_Min_Hist"] = fmt_dif_comp(dif_min_hist)
                    r_ult_dict["Val_Formatado"] = fmt_val_comp(v_ult)
                    r_ult_dict["Rotulo"] = f"Últ: {fmt_val_comp(v_ult)}"
                    ult_uf_list.append(r_ult_dict)

                    cor_uf_item = cores_uf_map.get(u, palette_fallback[len(resumo_extremos_uf) % len(palette_fallback)])
                    resumo_extremos_uf.append(
                        {
                            "UF / Local": u,
                            "cor": cor_uf_item,
                            "Último Registrado": f"{fmt_val_comp(v_ult)} ({r_ult['Data pt']})",
                            "Dif. vs Máx (Período)": fmt_dif_comp(dif_max_per),
                            "Dif. vs Mín (Período)": fmt_dif_comp(dif_min_per),
                            "Máximo no Período": f"{fmt_val_comp(v_max_per)} ({r_max['Data pt']})",
                            "Mínimo no Período": f"{fmt_val_comp(v_min_per)} ({r_min['Data pt']})",
                            "Dif. vs Máx Histórico": fmt_dif_comp(dif_max_hist),
                            "Dif. vs Mín Histórico": fmt_dif_comp(dif_min_hist),
                            "Máximo Histórico Completo": f"{fmt_val_comp(v_max_hist)} ({r_max_hist['Data pt']})",
                            "Mínimo Histórico Completo": f"{fmt_val_comp(v_min_hist)} ({r_min_hist['Data pt']})",
                        }
                    )

            df_max_uf = pd.DataFrame(max_uf_list)
            df_min_uf = pd.DataFrame(min_uf_list)
            df_ult_uf = pd.DataFrame(ult_uf_list)

            camadas_uf = [graf_comp_linhas]

            if not df_max_uf.empty:
                pontos_max_uf = (
                    alt.Chart(df_max_uf)
                    .mark_point(size=90, filled=True, shape="circle")
                    .encode(
                        x="Data:T",
                        y="VALOR:Q",
                        color=alt.Color(
                            "LOCAL:N",
                            scale=alt.Scale(domain=ufs_selecionadas_comp, range=cores_selecionadas),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("LOCAL:N", title="Local"),
                            alt.Tooltip("Data:T", title="Data do Máximo", format="%m/%Y"),
                            alt.Tooltip("VALOR:Q", title="Valor Máximo", format="+.2f" if (is_pct_comp or is_infl_comp) else ".2f"),
                        ],
                    )
                )
                rotulos_max_uf = (
                    alt.Chart(df_max_uf)
                    .mark_text(fontSize=11, fontWeight="bold", dy=-12, align="center")
                    .encode(
                        x="Data:T",
                        y="VALOR:Q",
                        text="Rotulo:N",
                        color=alt.Color(
                            "LOCAL:N",
                            scale=alt.Scale(domain=ufs_selecionadas_comp, range=cores_selecionadas),
                            legend=None,
                        ),
                    )
                )
                camadas_uf.extend([pontos_max_uf, rotulos_max_uf])

            if not df_min_uf.empty:
                pontos_min_uf = (
                    alt.Chart(df_min_uf)
                    .mark_point(size=90, filled=True, shape="circle")
                    .encode(
                        x="Data:T",
                        y="VALOR:Q",
                        color=alt.Color(
                            "LOCAL:N",
                            scale=alt.Scale(domain=ufs_selecionadas_comp, range=cores_selecionadas),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("LOCAL:N", title="Local"),
                            alt.Tooltip("Data:T", title="Data do Mínimo", format="%m/%Y"),
                            alt.Tooltip("VALOR:Q", title="Valor Mínimo", format="+.2f" if (is_pct_comp or is_infl_comp) else ".2f"),
                        ],
                    )
                )
                rotulos_min_uf = (
                    alt.Chart(df_min_uf)
                    .mark_text(fontSize=11, fontWeight="bold", dy=14, align="center")
                    .encode(
                        x="Data:T",
                        y="VALOR:Q",
                        text="Rotulo:N",
                        color=alt.Color(
                            "LOCAL:N",
                            scale=alt.Scale(domain=ufs_selecionadas_comp, range=cores_selecionadas),
                            legend=None,
                        ),
                    )
                )
                camadas_uf.extend([pontos_min_uf, rotulos_min_uf])

            if not df_ult_uf.empty:
                pontos_ult_uf = (
                    alt.Chart(df_ult_uf)
                    .mark_point(size=110, filled=True, shape="diamond")
                    .encode(
                        x="Data:T",
                        y="VALOR:Q",
                        color=alt.Color(
                            "LOCAL:N",
                            scale=alt.Scale(domain=ufs_selecionadas_comp, range=cores_selecionadas),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("LOCAL:N", title="UF / Local"),
                            alt.Tooltip("Data:T", title="Última Data", format="%m/%Y"),
                            alt.Tooltip("Val_Formatado:N", title="Último Valor"),
                            alt.Tooltip("Dif_Max_Per:N", title="Dif. vs Máx (Período)"),
                            alt.Tooltip("Dif_Min_Per:N", title="Dif. vs Mín (Período)"),
                            alt.Tooltip("Dif_Max_Hist:N", title="Dif. vs Máx Histórico"),
                            alt.Tooltip("Dif_Min_Hist:N", title="Dif. vs Mín Histórico"),
                        ],
                    )
                )
                camadas_uf.append(pontos_ult_uf)

                if len(ufs_selecionadas_comp) == 1:
                    rotulos_ult_uf = (
                        alt.Chart(df_ult_uf)
                        .mark_text(fontSize=11, fontWeight="bold", align="right", dx=-10, dy=-12)
                        .encode(
                            x="Data:T",
                            y="VALOR:Q",
                            text="Rotulo:N",
                            color=alt.Color(
                                "LOCAL:N",
                                scale=alt.Scale(domain=ufs_selecionadas_comp, range=cores_selecionadas),
                                legend=None,
                            ),
                        )
                    )
                    camadas_uf.append(rotulos_ult_uf)

            if (is_pct_comp or is_infl_comp) and (v_min_comp < 0 < v_max_comp):
                regra_zero = (
                    alt.Chart(pd.DataFrame({"y": [0]}))
                    .mark_rule(color="#94a3b8", strokeDash=[3, 3])
                    .encode(y="y:Q")
                )
                camadas_uf.append(regra_zero)

            graf_comp_linhas_final = alt.layer(*camadas_uf).properties(height=450)

            if pt_format and pt_time_format:
                graf_comp_linhas_final["usermeta"] = {
                    "embedOptions": {
                        "formatLocale": pt_format,
                        "timeFormatLocale": pt_time_format,
                    }
                }

            # Cards de Destaque: Último Registrado e Diferenciais no Período
            if resumo_extremos_uf:
                st.markdown("##### Destaques do Último Período e Diferenciais")
                chunk_size_comp = 4 if len(resumo_extremos_uf) >= 4 else len(resumo_extremos_uf)
                for i in range(0, len(resumo_extremos_uf), chunk_size_comp):
                    chunk = resumo_extremos_uf[i : i + chunk_size_comp]
                    cols = st.columns(len(chunk))
                    for col, item in zip(cols, chunk):
                        nome = item["UF / Local"]
                        cor = item.get("cor", "#002d62")
                        ult = item["Último Registrado"]
                        dif_max = item["Dif. vs Máx (Período)"]
                        with col:
                            st.markdown(
                                card_destaque_html(nome, cor, ult, dif_max),
                                unsafe_allow_html=True,
                            )

            st.altair_chart(graf_comp_linhas_final, theme=None, use_container_width=True)

            if resumo_extremos_uf:
                st.markdown("##### Extremos da Série e Diferenciais do Último Registro por UF")
                df_tab_extremos_uf = pd.DataFrame(resumo_extremos_uf)
                cols_tab_uf = [c for c in df_tab_extremos_uf.columns if c != "cor"]
                st.dataframe(df_tab_extremos_uf[cols_tab_uf], use_container_width=True, hide_index=True)

    # Ranking Nacional de todas as UFs para o mês selecionado
    if mes_comp:
        st.write("---")
        st.markdown(f"#### Ranking das UFs em {mes_comp_str} — {obter_nome_curto_setor(setor_comp_escolhido)}")
        if setor_comp_escolhido != obter_nome_curto_setor(setor_comp_escolhido):
            st.caption(f"ℹ️ **Descrição Oficial (IBGE):** {setor_comp_escolhido}")

        df_rank_uf = (
            df_comp_filtrado[df_comp_filtrado["Data"] == mes_comp]
            .dropna(subset=["VALOR"])
            .drop_duplicates(subset=["LOCAL"], keep="last")
            .sort_values("VALOR", ascending=False)
        )

        if len(df_rank_uf) <= 1 and not df_rank_uf.empty:
            st.markdown(
                f'<div class="nota-metodologica">'
                f'<strong>Aviso de Divulgação (IBGE):</strong> Para o mês de <strong>{mes_comp_str}</strong>, apenas o '
                f'<strong>Brasil consolidado</strong> possui dados divulgados até o momento. '
                f'Para comparar o ranking regional entre todos os estados (Rio de Janeiro, São Paulo, Minas Gerais, etc.), '
                f'selecione no campo <em>Mês de Referência para o Ranking</em> acima uma data com divulgação regional completa (ex.: 07/2026).'
                f'</div>',
                unsafe_allow_html=True,
            )

        if df_rank_uf.empty:
            st.info("Nenhum registro para o mês selecionado no ranking regional.")
        else:
            def definir_cor_uf(row):
                if row["LOCAL"] == "Rio de Janeiro":
                    return "#0050c8"
                elif row["LOCAL"] == "Brasil":
                    return "#002d62"
                elif row["VALOR"] >= 0:
                    return "#0072ce"
                else:
                    return "#b90e0c"

            df_rank_uf["Cor_Barra"] = df_rank_uf.apply(definir_cor_uf, axis=1)

            altura_grafico = max(130, len(df_rank_uf) * 28)
            chart_base = (
                alt.Chart(df_rank_uf).mark_bar(size=22)
                if len(df_rank_uf) <= 2
                else alt.Chart(df_rank_uf).mark_bar()
            )

            graf_barras_uf = (
                chart_base.encode(
                    x=alt.X("VALOR:Q", title=medida_comp_label),
                    y=alt.Y(
                        "LOCAL:N",
                        sort=alt.EncodingSortField(field="VALOR", order="descending"),
                        title="",
                    ),
                    color=alt.Color("Cor_Barra:N", scale=None),
                    tooltip=[
                        alt.Tooltip("LOCAL:N", title="Local"),
                        alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                    ],
                )
                .properties(height=altura_grafico)
            )

            rotulos_uf = (
                alt.Chart(df_rank_uf)
                .mark_text(
                    align=alt.expr("datum.VALOR >= 0 ? 'left' : 'right'"),
                    dx=alt.expr("datum.VALOR >= 0 ? 6 : -6"),
                    fontSize=11,
                )
                .encode(
                    x="VALOR:Q",
                    y=alt.Y(
                        "LOCAL:N",
                        sort=alt.EncodingSortField(field="VALOR", order="descending"),
                    ),
                    text=alt.Text(
                        "VALOR:Q",
                        format="+.2f" if "%" in medida_comp_label or "p.p." in medida_comp_label else ".2f",
                    ),
                    color=alt.value("#1e293b"),
                )
            )

            graf_barras_uf_final = graf_barras_uf + rotulos_uf
            if pt_format and pt_time_format:
                graf_barras_uf_final["usermeta"] = {
                    "embedOptions": {
                        "formatLocale": pt_format,
                        "timeFormatLocale": pt_time_format,
                    }
                }

            st.altair_chart(graf_barras_uf_final, theme=None, use_container_width=True)

            # Tabela resumida e exportação comparativa
            with st.expander("Ver dados do ranking regional em tabela"):
                df_tab_uf = df_rank_uf[["LOCAL", "VALOR", "Data pt"]].rename(
                    columns={"LOCAL": "UF / Localidade", "VALOR": medida_comp_label, "Data pt": "Mês/Ano"}
                )
                st.dataframe(df_tab_uf.reset_index(drop=True), use_container_width=True, hide_index=True)

                try:
                    excel_comp = to_excel2([df_tab_uf])
                    st.download_button(
                        label="Baixar ranking regional em Excel",
                        data=excel_comp,
                        file_name=f"PIM_Ranking_Regional_{mes_comp_str.replace('/', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="comp_download_ranking_xlsx",
                    )
                except Exception:
                    pass

# Rodapé oficial Sistema Firjan
footer_firjan()
