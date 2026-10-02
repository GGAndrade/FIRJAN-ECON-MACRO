import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from func import (
    config_page,
    header_firjan,
    footer_firjan,
    set_y_min,
    set_y_max,
    to_excel2,
)

###### CONFIGURAÇÕES INICIAIS

# Configuração da página e identidade visual Firjan
config_page("PIM-BR | Firjan - GEE")
header_firjan()

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

# Título Principal e Apresentação Institucional
st.write("# Produção Física Industrial (PIM-PF Brasil)")
st.markdown(
    """
    Monitoramento contínuo da **Produção Física Industrial brasileira** por seções e atividades industriais 
    (IBGE - Tabela 8888), com análise e consolidação da **Gerência Executiva de Economia (GEE) da Firjan**.
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
df["Data pt"] = df["Data"].dt.strftime("%m/%Y")
df["Ano"] = df["Data"].dt.year
df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce")

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
    key="pim_setores_selecionados",
    help="Selecione um ou mais setores para visualizar e comparar as curvas temporais.",
)

if not setores_selecionados:
    st.warning("Selecione pelo menos um setor industrial para exibir a série temporal.")
else:
    df_graf_linha = df_var[df_var["SUBGRUPOS"].isin(setores_selecionados)].copy()
    
    anos_totais = sorted(df_graf_linha["Ano"].unique().tolist())
    ano_inicio_default = max(min(anos_totais), max(anos_totais) - 8)
    
    ano_inicial, ano_final = st.select_slider(
        "Intervalo (Anos)",
        options=anos_totais,
        value=(ano_inicio_default, max(anos_totais)),
        key="pim_slider_anos",
    )
    
    df_graf_linha = df_graf_linha[
        (df_graf_linha["Ano"] >= ano_inicial) & (df_graf_linha["Ano"] <= ano_final)
    ]
    
    if df_graf_linha.empty:
        st.info("Nenhum registro para o período e setores selecionados.")
    else:
        v_min = df_graf_linha["VALOR"].min()
        v_max = df_graf_linha["VALOR"].max()
        eixo_y_min = set_y_min(v_min) if pd.notna(v_min) else 0
        eixo_y_max = set_y_max(v_max) if pd.notna(v_max) else 100
        
        grafico_linha = (
            alt.Chart(df_graf_linha)
            .mark_line(strokeWidth=2.8)
            .encode(
                x=alt.X("Data:T", axis=alt.Axis(format="%m/%Y", labelAngle=-45, title="Mês/Ano")),
                y=alt.Y("VALOR:Q", scale=alt.Scale(domain=[eixo_y_min, eixo_y_max]), title=medida_label),
                color=alt.Color("SUBGRUPOS:N", legend=alt.Legend(title="Setor", orient="bottom")),
                tooltip=[
                    alt.Tooltip("Data:T", title="Data", format="%m/%Y"),
                    alt.Tooltip("SUBGRUPOS:N", title="Setor"),
                    alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                ],
            )
        )
        
        # Linha pontilhada no zero para variações ou influências
        if ("(%)" in medida_label or "(p.p.)" in medida_label) and (v_min < 0 < v_max):
            linha_zero = (
                alt.Chart(pd.DataFrame({"y": [0]}))
                .mark_rule(color="#888888", strokeDash=[3, 3])
                .encode(y="y:Q")
            )
            grafico_linha_final = (grafico_linha + linha_zero).properties(height=420)
        else:
            grafico_linha_final = grafico_linha.properties(height=420)
            
        if pt_format and pt_time_format:
            grafico_linha_final["usermeta"] = {
                "embedOptions": {
                    "formatLocale": pt_format,
                    "timeFormatLocale": pt_time_format,
                }
            }
            
        st.altair_chart(grafico_linha_final, theme=None, use_container_width=True)

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
    grafico_barras = (
        alt.Chart(df_ranking)
        .mark_bar()
        .encode(
            x=alt.X("VALOR:Q", title=medida_label),
            y=alt.Y(
                "SUBGRUPOS:N",
                sort=alt.EncodingSortField(field="VALOR", order="descending"),
                title="",
            ),
            color=alt.condition(
                alt.datum.VALOR >= 0,
                alt.value("#376092"),  # Azul padrão Firjan
                alt.value("#b90e0c"),  # Vermelho para variações negativas
            ),
            tooltip=[
                alt.Tooltip("SUBGRUPOS:N", title="Setor"),
                alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
            ],
        )
        .properties(height=max(400, len(df_ranking) * 26))
    )

    rotulos_barras = grafico_barras.mark_text(
        align=alt.expr("datum.VALOR >= 0 ? 'left' : 'right'"),
        dx=alt.expr("datum.VALOR >= 0 ? 6 : -6"),
        fontSize=11,
    ).encode(
        text=alt.Text("VALOR:Q", format="+.2f" if "%" in medida_label or "p.p." in medida_label else ".2f"),
        color=alt.value("#222222"),
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
