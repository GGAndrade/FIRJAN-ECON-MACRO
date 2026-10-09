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
config_page("PIM-BR | Firjan - GEE")
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


# Título Principal e Apresentação Institucional
st.write("# Produção Física Industrial (PIM-PF Brasil)")
st.markdown(
    """
    Monitoramento contínuo da **Produção Física Industrial brasileira** por seções e atividades industriais 
    (IBGE - Tabela 8888), com análise e consolidação da **Gerência de Estudos Econômicos (GEE) da Firjan**.
    """
)
st.write("---")

# Seção de Entrada e Seleção de Parâmetros
col1, col2 = st.columns([1, 1])

with col1:
    BD = st.file_uploader(
        label="Arquivo Parquet",
        type="parquet",
        key="pim_bd",
        help="Envie um arquivo Parquet com dados atualizados da PIM-PF (IBGE) para substituir a base padrão.",
    )

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
        df = pd.read_parquet(BD)
        st.markdown(
            f'<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 16px; color: #15803d; font-size: 14px; margin: 10px 0 18px 0;">Utilizando arquivo Parquet enviado: <code>{BD.name}</code>.</div>',
            unsafe_allow_html=True,
        )
    else:
        df = pd.read_parquet(default_parquet)
        st.markdown(
            '<div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 16px; color: #1e40af; font-size: 14px; margin: 10px 0 18px 0;">Utilizando a base consolidada padrão (<code>PIM_BR/teste_pim.parquet</code>).</div>',
            unsafe_allow_html=True,
        )
except Exception as e:
    st.error(f"Erro ao ler o arquivo Parquet: {e}. Verifique o formato do arquivo e tente novamente.")
    st.stop()

# Validação das colunas mínimas esperadas
colunas_necessarias = ["DATA", "VARIAVEL", "SUBGRUPOS", "VALOR"]
colunas_faltantes = [c for c in colunas_necessarias if c not in df.columns]
if colunas_faltantes:
    st.error(
        f"O arquivo fornecido não possui as seguintes colunas obrigatórias: {colunas_faltantes}."
    )
    st.stop()

# Tratamento de tipos de dados
df["Data"] = pd.to_datetime(df["DATA"])
if df["Data"].dt.tz is not None:
    df["Data"] = df["Data"].dt.tz_localize(None)
df["Data pt"] = df["Data"].dt.strftime("%m/%Y")
df["Ano"] = df["Data"].dt.year.astype("int16")
df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce").astype("float32")

# Dicionário de variáveis com rótulos amigáveis para o usuário
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

vars_no_df = df["VARIAVEL"].unique()
opcoes_medidas = {rotulo: var for rotulo, var in VARIAVEIS_DICT.items() if var in vars_no_df}

# Caso o arquivo tenha alguma variável nova não mapeada previamente
for v in vars_no_df:
    if v not in VARIAVEIS_DICT.values():
        opcoes_medidas[v] = v

with col2:
    medida_label = st.selectbox(
        label="Medida / Indicador",
        options=list(opcoes_medidas.keys()),
        index=0,
        key="pim_medida",
        help="Selecione o indicador da PIM-PF que deseja analisar nos gráficos e tabelas abaixo.",
    )
    var_escolhida = opcoes_medidas[medida_label]

# Data mais recente disponível
data_maxima = df["Data"].max()
data_maxima_pt = data_maxima.strftime("%m/%Y")

# Quadro Integrado: Panorama da Indústria Geral e seus Segmentos
with st.container(border=True):
    st.markdown(
        """
        <style>
        .quadro-titulo-geral {
            font-size: 1.18rem;
            font-weight: 700;
            color: #002d62;
            padding-bottom: 6px;
            border-bottom: 2px solid #002d62;
            margin-bottom: 12px;
            letter-spacing: 0.2px;
        }
        .quadro-titulo-sub {
            margin-left: 28px;
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
            margin: 16px 0 12px 0;
        }
        /* Cor azul institucional nos valores das métricas */
        [data-testid="stMetricValue"] {
            color: #002d62 !important;
        }
        /* Segmentos com recuo (5 colunas): fontes menores e azul em destaque */
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(5)) [data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
            color: #0050c8 !important;
        }
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(5)) [data-testid="stMetricLabel"] {
            font-size: 0.82rem !important;
            color: #334155 !important;
            font-weight: 500;
        }
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(5)) [data-testid="stMetricDelta"] {
            font-size: 0.82rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    def extrair_indicadores(subgrupo_nome):
        df_recente_sub = df[(df["Data"] == data_maxima) & (df["SUBGRUPOS"] == subgrupo_nome)]

        def extrair_metrica(termo):
            sub = df_recente_sub[df_recente_sub["VARIAVEL"].str.contains(termo, case=False, na=False, regex=False)]
            if not sub.empty and pd.notna(sub["VALOR"].iloc[0]):
                return sub["VALOR"].iloc[0]
            return None

        return {
            "mm1": extrair_metrica("imediatamente anterior, com ajuste sazonal (M/M-1)"),
            "m12": extrair_metrica("mesmo mês do ano anterior (M/M-12)"),
            "ano": extrair_metrica("acumulada no ano"),
            "12m": extrair_metrica("acumulada em 12 meses"),
        }

    # 1. Indústria Geral
    dados_ig = extrair_indicadores("1 Indústria geral")
    st.markdown(
        f'<div class="quadro-titulo-geral">Panorama da Indústria Geral ({data_maxima_pt})</div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Variação M/M-1 (c/ ajuste)",
            value=f"{dados_ig['mm1']:+.2f}%" if dados_ig["mm1"] is not None else "N/D",
            delta=f"{dados_ig['mm1']:+.2f}%" if dados_ig["mm1"] is not None else None,
        )
    with col2:
        st.metric(
            label="Variação M/M-12 (interanual)",
            value=f"{dados_ig['m12']:+.2f}%" if dados_ig["m12"] is not None else "N/D",
            delta=f"{dados_ig['m12']:+.2f}%" if dados_ig["m12"] is not None else None,
        )
    with col3:
        st.metric(
            label="Acumulado no Ano",
            value=f"{dados_ig['ano']:+.2f}%" if dados_ig["ano"] is not None else "N/D",
            delta=f"{dados_ig['ano']:+.2f}%" if dados_ig["ano"] is not None else None,
        )
    with col4:
        st.metric(
            label="Acumulado em 12 Meses",
            value=f"{dados_ig['12m']:+.2f}%" if dados_ig["12m"] is not None else "N/D",
            delta=f"{dados_ig['12m']:+.2f}%" if dados_ig["12m"] is not None else None,
        )

    st.markdown('<div class="divisor-quadro"></div>', unsafe_allow_html=True)

    # 2. Indústria Extrativa (no singular e com recuo à direita)
    dados_ext = extrair_indicadores("2 Indústrias extrativas")
    st.markdown(
        f'<div class="quadro-titulo-sub">Indústria Extrativa ({data_maxima_pt})</div>',
        unsafe_allow_html=True,
    )
    _, e1, e2, e3, e4 = st.columns([0.05, 1, 1, 1, 1])
    with e1:
        st.metric(
            label="Variação M/M-1 (c/ ajuste)",
            value=f"{dados_ext['mm1']:+.2f}%" if dados_ext["mm1"] is not None else "N/D",
            delta=f"{dados_ext['mm1']:+.2f}%" if dados_ext["mm1"] is not None else None,
        )
    with e2:
        st.metric(
            label="Variação M/M-12 (interanual)",
            value=f"{dados_ext['m12']:+.2f}%" if dados_ext["m12"] is not None else "N/D",
            delta=f"{dados_ext['m12']:+.2f}%" if dados_ext["m12"] is not None else None,
        )
    with e3:
        st.metric(
            label="Acumulado no Ano",
            value=f"{dados_ext['ano']:+.2f}%" if dados_ext["ano"] is not None else "N/D",
            delta=f"{dados_ext['ano']:+.2f}%" if dados_ext["ano"] is not None else None,
        )
    with e4:
        st.metric(
            label="Acumulado em 12 Meses",
            value=f"{dados_ext['12m']:+.2f}%" if dados_ext["12m"] is not None else "N/D",
            delta=f"{dados_ext['12m']:+.2f}%" if dados_ext["12m"] is not None else None,
        )

    st.markdown('<div class="divisor-quadro"></div>', unsafe_allow_html=True)

    # 3. Indústria de Transformação (no singular e com recuo à direita)
    dados_transf = extrair_indicadores("3 Indústrias de transformação")
    st.markdown(
        f'<div class="quadro-titulo-sub">Indústria de Transformação ({data_maxima_pt})</div>',
        unsafe_allow_html=True,
    )
    _, t1, t2, t3, t4 = st.columns([0.05, 1, 1, 1, 1])
    with t1:
        st.metric(
            label="Variação M/M-1 (c/ ajuste)",
            value=f"{dados_transf['mm1']:+.2f}%" if dados_transf["mm1"] is not None else "N/D",
            delta=f"{dados_transf['mm1']:+.2f}%" if dados_transf["mm1"] is not None else None,
        )
    with t2:
        st.metric(
            label="Variação M/M-12 (interanual)",
            value=f"{dados_transf['m12']:+.2f}%" if dados_transf["m12"] is not None else "N/D",
            delta=f"{dados_transf['m12']:+.2f}%" if dados_transf["m12"] is not None else None,
        )
    with t3:
        st.metric(
            label="Acumulado no Ano",
            value=f"{dados_transf['ano']:+.2f}%" if dados_transf["ano"] is not None else "N/D",
            delta=f"{dados_transf['ano']:+.2f}%" if dados_transf["ano"] is not None else None,
        )
    with t4:
        st.metric(
            label="Acumulado em 12 Meses",
            value=f"{dados_transf['12m']:+.2f}%" if dados_transf["12m"] is not None else "N/D",
            delta=f"{dados_transf['12m']:+.2f}%" if dados_transf["12m"] is not None else None,
        )

st.write("---")

# ----------------------------------------------------
# 1. SEÇÃO: EVOLUÇÃO TEMPORAL DOS SETORES
# ----------------------------------------------------
st.write("#### Evolução dos setores industriais")

df_var = df[df["VARIAVEL"] == var_escolhida].copy()
todos_os_setores = sorted(df_var["SUBGRUPOS"].unique().tolist())

# Padrão: 3 grandes agregados
padrao_setores = [s for s in ["1 Indústria geral", "2 Indústrias extrativas", "3 Indústrias de transformação"] if s in todos_os_setores]
if not padrao_setores:
    padrao_setores = todos_os_setores[:3]

setores_selecionados = st.multiselect(
    label="Setores / Atividades Industriais",
    options=todos_os_setores,
    default=padrao_setores,
    format_func=obter_nome_curto_setor,
    key="pim_setores_selecionados",
    help="Selecione um ou mais setores para visualizar e comparar as curvas temporais.",
)

if not setores_selecionados:
    st.warning("Selecione pelo menos um setor industrial para exibir a série temporal.")
else:
    df_graf_valido = (
        df_var[df_var["SUBGRUPOS"].isin(setores_selecionados)]
        .dropna(subset=["VALOR"])
        .copy()
    )
    
    anos_totais = sorted(df_graf_valido["Ano"].unique().tolist())
    ano_inicio_default = min(anos_totais)
    
    ano_inicial, ano_final = st.select_slider(
        "Intervalo (Anos)",
        options=anos_totais,
        value=(ano_inicio_default, max(anos_totais)),
        key="pim_slider_anos",
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

        # Margem vertical para dar respiro aos rótulos de máximo e mínimo
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
                y=alt.Y("VALOR:Q", scale=alt.Scale(domain=[eixo_y_min, eixo_y_max]), title=medida_label),
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

        # Identificar pontos de Máximo e Mínimo para cada setor
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

        # Camada de pontos e rótulos de Máximo
        if not df_max.empty:
            pontos_max = (
                alt.Chart(df_max)
                .mark_point(size=95, filled=True, shape="circle")
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

        # Camada de pontos e rótulos de Mínimo
        if not df_min.empty:
            pontos_min = (
                alt.Chart(df_min)
                .mark_point(size=95, filled=True, shape="circle")
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

        # Camada de pontos e rótulos do Último Registrado
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

        # Linha pontilhada no zero para variações ou influências
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
                    with col:
                        st.markdown(
                            card_destaque_html(nome, cor, ult, dif_max, tooltip_desc=desc_oficial),
                            unsafe_allow_html=True,
                        )

        st.altair_chart(grafico_linha_final, theme=None, use_container_width=True)

        if setores_cobertura_recente:
            detalhes_setores = "; ".join([f"<strong title='{s}'>{obter_nome_curto_setor(s)}</strong> (a partir de {dt})" for s, dt in setores_cobertura_recente])
            st.markdown(
                f'<div class="nota-metodologica">'
                f'<strong>Nota de Cobertura Histórica (IBGE - PIM-PF):</strong> '
                f'A série histórica exibida contempla todos os dados oficiais disponíveis desde {data_min_graf.strftime("%m/%Y")}. '
                f'Os seguintes setores foram incorporados à pesquisa pelo IBGE em revisões posteriores: {detalhes_setores}.'
                f'</div>',
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

datas_unicas = sorted(df_var["Data"].unique().tolist(), reverse=True)
mapa_datas = {d.strftime("%m/%Y"): d for d in pd.to_datetime(datas_unicas)}

col_r1, col_r2 = st.columns([1, 1])

with col_r1:
    mes_escolhido_str = st.selectbox(
        "Mês de Referência para Comparação",
        options=list(mapa_datas.keys()),
        index=0,
        key="pim_mes_ranking",
    )
    mes_escolhido = mapa_datas[mes_escolhido_str]

with col_r2:
    filtro_ramos = st.radio(
        "Escopo da Comparação",
        options=["Todos os setores (27)", "Apenas ramos desagregados (24 atividades)"],
        index=0,
        horizontal=True,
        key="pim_escopo_ranking",
    )

df_ranking = df_var[df_var["Data"] == mes_escolhido].copy()

if "Apenas ramos desagregados" in filtro_ramos:
    df_ranking = df_ranking[
        ~df_ranking["SUBGRUPOS"].isin(["1 Indústria geral", "2 Indústrias extrativas", "3 Indústrias de transformação"])
    ]

df_ranking = df_ranking.dropna(subset=["VALOR"]).sort_values("VALOR", ascending=False)

if df_ranking.empty:
    st.info("Nenhum dado encontrado para o mês selecionado.")
else:
    df_ranking = df_ranking.copy()
    df_ranking["Setor"] = df_ranking["SUBGRUPOS"].apply(obter_nome_curto_setor)
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
            color=alt.condition(
                alt.datum.VALOR >= 0,
                alt.value("#376092"),  # Azul padrão Firjan
                alt.value("#b90e0c"),  # Vermelho para variações negativas
            ),
            tooltip=[
                alt.Tooltip("Setor:N", title="Setor"),
                alt.Tooltip("SUBGRUPOS:N", title="Descrição Técnica Oficial (IBGE)"),
                alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
            ],
        )
        .properties(height=max(400, len(df_ranking) * 26))
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
            text=alt.Text("VALOR:Q", format="+.2f" if "%" in medida_label or "p.p." in medida_label else ".2f"),
            color=alt.value("#222222"),
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

anos_tabela = sorted(df_tab["Ano"].unique().tolist())
ano_tab_padrao = max(min(anos_tabela), max(anos_tabela) - 4)

ano_corte = st.slider(
    "Exibir histórico na tabela a partir de:",
    min_value=min(anos_tabela),
    max_value=max(anos_tabela),
    value=ano_tab_padrao,
    key="pim_slider_tabela",
)

df_tab_filtrada = df_tab[df_tab["Ano"] >= ano_corte]

df_pivot = df_tab_filtrada.pivot(
    index="SUBGRUPOS",
    columns="Periodo",
    values="VALOR",
)

# Garantir ordenação correta dos setores
setores_existentes = [s for s in todos_os_setores if s in df_pivot.index]
df_pivot = df_pivot.loc[setores_existentes]

st.dataframe(
    df_pivot.style.format("{:.2f}", na_rep="-"),
    use_container_width=True,
    height=480,
)

# Preparação de planilhas para exportação em Excel (.xlsx)
df_export_pivot = df_pivot.reset_index()
df_export_serie = df_var[["Data", "SUBGRUPOS", "VARIAVEL", "VALOR", "UNIDADE_DE_MEDIDA"]].sort_values(
    ["Data", "SUBGRUPOS"], ascending=[False, True]
)

try:
    dados_excel = to_excel2([df_export_pivot, df_export_serie])
    st.download_button(
        label="Baixar dados em Excel",
        data=dados_excel,
        file_name=f"PIM_BR_{data_maxima_pt.replace('/', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="pim_download_xlsx",
    )
except Exception as e:
    st.warning(f"Não foi possível gerar a planilha Excel: {e}")

# Rodapé oficial Sistema Firjan
footer_firjan()
