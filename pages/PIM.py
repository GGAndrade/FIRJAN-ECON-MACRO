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

    # Desduplicar registros garantindo unicidade por Local, Data, Variavel e Subgrupo
    df = df.drop_duplicates(subset=["LOCAL", "Data", "VARIAVEL", "SUBGRUPOS"], keep="last")
    return df


# Gestão do Arquivo Parquet (Padrão: pim_agregado.parquet, com opção de upload)
default_parquet = "PIM_BR/pim_agregado.parquet"
if not os.path.exists(default_parquet):
    # Fallback para teste_pim se necessário
    if os.path.exists("PIM_BR/teste_pim.parquet"):
        default_parquet = "PIM_BR/teste_pim.parquet"

with st.expander("Base de dados e upload de atualização (opcional)"):
    arquivo_upload = st.file_uploader(
        label="Substituir base com novo arquivo Parquet",
        type=["parquet"],
        key="pim_agregado_upload",
        help="Envie um arquivo Parquet atualizado da PIM-PF caso deseje sobrepor a base padrão.",
    )

fonte_arquivo = arquivo_upload if arquivo_upload is not None else default_parquet

try:
    df_completo = carregar_dados_pim(fonte_arquivo)
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}. Verifique o arquivo Parquet.")
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

# Locais disponíveis
locais_disponiveis = sorted(df_completo["LOCAL"].dropna().unique().tolist())


def render_dashboard_uf(df_uf, nome_local, prefixo):
    """Renderiza a estrutura completa de análise industrial para a localidade especificada."""

    # Seletor de Medida / Indicador
    col_med1, _ = st.columns([2, 1])
    with col_med1:
        medida_label = st.selectbox(
            label="Medida / Indicador",
            options=list(opcoes_medidas.keys()),
            index=0,
            key=f"{prefixo}_medida",
            help=f"Selecione o indicador da PIM que deseja analisar para {nome_local}.",
        )
        var_escolhida = opcoes_medidas[medida_label]

    df_var = df_uf[df_uf["VARIAVEL"] == var_escolhida].copy()

    # ----------------------------------------------------
    # QUADRO INTEGRADO: PANORAMA DA INDÚSTRIA
    # ----------------------------------------------------
    def extrair_indicadores(subgrupo_termo):
        df_sub = df_uf[
            df_uf["SUBGRUPOS"].str.contains(subgrupo_termo, case=False, na=False, regex=False)
        ]
        if df_sub.empty:
            return {"mm1": (None, None), "m12": (None, None), "ano": (None, None), "12m": (None, None)}

        def extrair_metrica(termo):
            sub = df_sub[
                df_sub["VARIAVEL"].str.contains(termo, case=False, na=False, regex=False)
            ].dropna(subset=["VALOR"])
            if not sub.empty:
                ult = sub.sort_values("Data").iloc[-1]
                return ult["VALOR"], ult["Data pt"]
            return None, None

        return {
            "mm1": extrair_metrica("imediatamente anterior, com ajuste sazonal (M/M-1)"),
            "m12": extrair_metrica("mesmo m"),
            "ano": extrair_metrica("acumulada no ano"),
            "12m": extrair_metrica("acumulada em 12 meses"),
        }

    dados_ig = extrair_indicadores("1 Ind")
    dados_ext = extrair_indicadores("2 Ind")
    dados_transf = extrair_indicadores("3 Ind")

    # Data de referência de referência mais recente encontrada para a Indústria Geral
    datas_ref = [d[1] for d in dados_ig.values() if d[1] is not None]
    data_ref_label = datas_ref[0] if datas_ref else df_uf["Data pt"].max()

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

    st.write("---")

    # ----------------------------------------------------
    # 1. SEÇÃO: EVOLUÇÃO TEMPORAL DOS SETORES
    # ----------------------------------------------------
    st.write("#### Evolução dos setores industriais")

    todos_os_setores = sorted(df_var["SUBGRUPOS"].dropna().unique().tolist())
    padrao_setores = [
        s for s in todos_os_setores if any(s.startswith(p) for p in ["1 Ind", "2 Ind", "3 Ind"])
    ]
    if not padrao_setores:
        padrao_setores = todos_os_setores[:3]

    setores_selecionados = st.multiselect(
        label="Setores / Atividades Industriais",
        options=todos_os_setores,
        default=padrao_setores,
        key=f"{prefixo}_setores_selecionados",
        help="Selecione um ou mais setores para visualizar e comparar as curvas temporais.",
    )

    if not setores_selecionados:
        st.warning("Selecione pelo menos um setor industrial para exibir a série temporal.")
    else:
        df_graf_linha = df_var[df_var["SUBGRUPOS"].isin(setores_selecionados)].copy()
        anos_totais = sorted(df_graf_linha["Ano"].dropna().unique().astype(int).tolist())

        if not anos_totais:
            st.info("Nenhum dado temporal disponível para os setores selecionados.")
        else:
            ano_inicio_default = max(min(anos_totais), max(anos_totais) - 8)

            ano_inicial, ano_final = st.select_slider(
                "Intervalo (Anos)",
                options=anos_totais,
                value=(ano_inicio_default, max(anos_totais)),
                key=f"{prefixo}_slider_anos",
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

                margem_y = (eixo_y_max - eixo_y_min) * 0.08
                eixo_y_min -= margem_y
                eixo_y_max += margem_y

                grafico_linha = (
                    alt.Chart(df_graf_linha)
                    .mark_line(strokeWidth=2.8)
                    .encode(
                        x=alt.X(
                            "Data:T",
                            axis=alt.Axis(format="%m/%Y", labelAngle=-45, title="Mês/Ano"),
                        ),
                        y=alt.Y(
                            "VALOR:Q",
                            scale=alt.Scale(domain=[eixo_y_min, eixo_y_max]),
                            title=medida_label,
                        ),
                        color=alt.Color(
                            "SUBGRUPOS:N",
                            legend=alt.Legend(title="Setor", orient="bottom"),
                        ),
                        tooltip=[
                            alt.Tooltip("Data:T", title="Data", format="%m/%Y"),
                            alt.Tooltip("SUBGRUPOS:N", title="Setor"),
                            alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                        ],
                    )
                )

                max_list = []
                min_list = []
                resumo_extremos = []
                is_pct = ("(%)" in medida_label) or ("(p.p.)" in medida_label)
                fmt_val = (lambda v: f"{v:+.2f}%") if is_pct else (lambda v: f"{v:.2f}")

                for s in setores_selecionados:
                    sub_per = df_graf_linha[df_graf_linha["SUBGRUPOS"] == s].dropna(subset=["VALOR"])
                    sub_hist = df_var[df_var["SUBGRUPOS"] == s].dropna(subset=["VALOR"])

                    if not sub_per.empty:
                        idx_max_per = sub_per["VALOR"].idxmax()
                        idx_min_per = sub_per["VALOR"].idxmin()

                        r_max = sub_per.loc[idx_max_per].to_dict()
                        r_max["Rotulo"] = f"Máx: {fmt_val(r_max['VALOR'])} ({r_max['Data pt']})"
                        max_list.append(r_max)

                        r_min = sub_per.loc[idx_min_per].to_dict()
                        r_min["Rotulo"] = f"Mín: {fmt_val(r_min['VALOR'])} ({r_min['Data pt']})"
                        min_list.append(r_min)

                        if not sub_hist.empty:
                            idx_max_hist = sub_hist["VALOR"].idxmax()
                            idx_min_hist = sub_hist["VALOR"].idxmin()
                            r_max_hist = sub_hist.loc[idx_max_hist]
                            r_min_hist = sub_hist.loc[idx_min_hist]
                            r_ult = sub_per.sort_values("Data").iloc[-1]

                            resumo_extremos.append(
                                {
                                    "Setor": s,
                                    "Mínimo no Período": f"{fmt_val(r_min['VALOR'])} ({r_min['Data pt']})",
                                    "Máximo no Período": f"{fmt_val(r_max['VALOR'])} ({r_max['Data pt']})",
                                    "Mínimo Histórico Completo": f"{fmt_val(r_min_hist['VALOR'])} ({r_min_hist['Data pt']})",
                                    "Máximo Histórico Completo": f"{fmt_val(r_max_hist['VALOR'])} ({r_max_hist['Data pt']})",
                                    "Último Registrado": f"{fmt_val(r_ult['VALOR'])} ({r_ult['Data pt']})",
                                }
                            )

                df_max = pd.DataFrame(max_list)
                df_min = pd.DataFrame(min_list)
                camadas = [grafico_linha]

                if not df_max.empty:
                    pontos_max = (
                        alt.Chart(df_max)
                        .mark_point(size=90, filled=True, shape="circle")
                        .encode(
                            x="Data:T",
                            y="VALOR:Q",
                            color=alt.Color("SUBGRUPOS:N", legend=None),
                            tooltip=[
                                alt.Tooltip("SUBGRUPOS:N", title="Setor"),
                                alt.Tooltip("Data:T", title="Data do Máximo", format="%m/%Y"),
                                alt.Tooltip("VALOR:Q", title="Valor Máximo", format="+.2f" if is_pct else ".2f"),
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
                            color=alt.Color("SUBGRUPOS:N", legend=None),
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
                            color=alt.Color("SUBGRUPOS:N", legend=None),
                            tooltip=[
                                alt.Tooltip("SUBGRUPOS:N", title="Setor"),
                                alt.Tooltip("Data:T", title="Data do Mínimo", format="%m/%Y"),
                                alt.Tooltip("VALOR:Q", title="Valor Mínimo", format="+.2f" if is_pct else ".2f"),
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
                            color=alt.Color("SUBGRUPOS:N", legend=None),
                        )
                    )
                    camadas.extend([pontos_min, rotulos_min])

                if ("(%)" in medida_label or "(p.p.)" in medida_label) and (v_min < 0 < v_max):
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

                st.altair_chart(grafico_linha_final, theme=None, use_container_width=True)

                if resumo_extremos:
                    st.markdown("##### Máximos e Mínimos da Série Histórica por Setor")
                    df_tab_extremos = pd.DataFrame(resumo_extremos)
                    st.dataframe(df_tab_extremos, use_container_width=True, hide_index=True)

    st.write("---")

    # ----------------------------------------------------
    # 2. SEÇÃO: COMPARAÇÃO SETORIAL (RANKING EM BARRAS)
    # ----------------------------------------------------
    st.write("#### Comparação setorial no período selecionado")

    datas_unicas = sorted(df_var["Data"].dropna().unique().tolist(), reverse=True)
    mapa_datas = {d.strftime("%m/%Y"): d for d in pd.to_datetime(datas_unicas)}

    col_r1, col_r2 = st.columns([1, 1])
    with col_r1:
        mes_escolhido_str = st.selectbox(
            "Mês de Referência para Comparação",
            options=list(mapa_datas.keys()),
            index=0,
            key=f"{prefixo}_mes_ranking",
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
            ~df_ranking["SUBGRUPOS"].str.contains("^(1|2|3) Ind", regex=True, na=False)
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
                    alt.value("#002d62"),  # Azul Firjan Institucional
                    alt.value("#b90e0c"),  # Vermelho para variações negativas
                ),
                tooltip=[
                    alt.Tooltip("SUBGRUPOS:N", title="Setor"),
                    alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                ],
            )
            .properties(height=max(380, len(df_ranking) * 25))
        )

        rotulos_barras = grafico_barras.mark_text(
            align=alt.expr("datum.VALOR >= 0 ? 'left' : 'right'"),
            dx=alt.expr("datum.VALOR >= 0 ? 6 : -6"),
            fontSize=11,
        ).encode(
            text=alt.Text(
                "VALOR:Q",
                format="+.2f" if "%" in medida_label or "p.p." in medida_label else ".2f",
            ),
            color=alt.value("#1e293b"),
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

    df_comp_var = df_completo[df_completo["VARIAVEL"] == var_comp].copy()

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
            key="comp_setor",
        )

    df_comp_filtrado = df_comp_var[df_comp_var["SUBGRUPOS"] == setor_comp_escolhido].copy()

    datas_comp = sorted(df_comp_filtrado["Data"].dropna().unique().tolist(), reverse=True)
    mapa_datas_comp = {d.strftime("%m/%Y"): d for d in pd.to_datetime(datas_comp)}

    with col_c3:
        mes_comp_str = st.selectbox(
            "Mês de Referência para o Ranking",
            options=list(mapa_datas_comp.keys()),
            index=0,
            key="comp_mes_ref",
        )
        mes_comp = mapa_datas_comp[mes_comp_str] if mapa_datas_comp else None

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
        df_serie_comp = df_comp_filtrado[df_comp_filtrado["LOCAL"].isin(ufs_selecionadas_comp)].copy()
        anos_comp = sorted(df_serie_comp["Ano"].dropna().unique().astype(int).tolist())

        if anos_comp:
            ano_ini_default_comp = max(min(anos_comp), max(anos_comp) - 6)
            ano_ini_comp, ano_fim_comp = st.select_slider(
                "Intervalo temporal (Anos)",
                options=anos_comp,
                value=(ano_ini_default_comp, max(anos_comp)),
                key="comp_slider_anos",
            )

            df_serie_comp = df_serie_comp[
                (df_serie_comp["Ano"] >= ano_ini_comp) & (df_serie_comp["Ano"] <= ano_fim_comp)
            ]

            st.markdown("#### Evolução Temporal Comparativa")
            graf_comp_linhas = (
                alt.Chart(df_serie_comp)
                .mark_line(strokeWidth=2.6)
                .encode(
                    x=alt.X("Data:T", axis=alt.Axis(format="%m/%Y", labelAngle=-45, title="Mês/Ano")),
                    y=alt.Y("VALOR:Q", title=medida_comp_label),
                    color=alt.Color(
                        "LOCAL:N",
                        scale=alt.Scale(
                            domain=["Brasil", "Rio de Janeiro"],
                            range=["#002d62", "#0072ce"],
                        ),
                        legend=alt.Legend(title="UF / Local", orient="bottom"),
                    ),
                    tooltip=[
                        alt.Tooltip("Data:T", title="Data", format="%m/%Y"),
                        alt.Tooltip("LOCAL:N", title="Local"),
                        alt.Tooltip("VALOR:Q", title="Valor", format=".2f"),
                    ],
                )
                .properties(height=420)
            )

            if ("(%)" in medida_comp_label or "(p.p.)" in medida_comp_label):
                regra_zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#94a3b8", strokeDash=[3, 3]).encode(y="y:Q")
                graf_comp_linhas = graf_comp_linhas + regra_zero

            if pt_format and pt_time_format:
                graf_comp_linhas["usermeta"] = {
                    "embedOptions": {
                        "formatLocale": pt_format,
                        "timeFormatLocale": pt_time_format,
                    }
                }

            st.altair_chart(graf_comp_linhas, theme=None, use_container_width=True)

    # Ranking Nacional de todas as UFs para o mês selecionado
    if mes_comp:
        st.write("---")
        st.markdown(f"#### Ranking das UFs em {mes_comp_str} — {setor_comp_escolhido}")

        df_rank_uf = df_comp_filtrado[df_comp_filtrado["Data"] == mes_comp].dropna(subset=["VALOR"]).sort_values("VALOR", ascending=False)

        if df_rank_uf.empty:
            st.info("Nenhum registro para o mês selecionado no ranking regional.")
        else:
            def definir_cor_uf(row):
                if row["LOCAL"] == "Rio de Janeiro":
                    return "#0050c8"
                elif row["LOCAL"] == "Brasil":
                    return "#002d62"
                elif row["VALOR"] >= 0:
                    return "#38bdf8"
                else:
                    return "#b90e0c"

            df_rank_uf["Cor_Barra"] = df_rank_uf.apply(definir_cor_uf, axis=1)

            graf_barras_uf = (
                alt.Chart(df_rank_uf)
                .mark_bar()
                .encode(
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
                .properties(height=max(360, len(df_rank_uf) * 24))
            )

            rotulos_uf = graf_barras_uf.mark_text(
                align=alt.expr("datum.VALOR >= 0 ? 'left' : 'right'"),
                dx=alt.expr("datum.VALOR >= 0 ? 6 : -6"),
                fontSize=11,
            ).encode(
                text=alt.Text(
                    "VALOR:Q",
                    format="+.2f" if "%" in medida_comp_label or "p.p." in medida_comp_label else ".2f",
                ),
                color=alt.value("#1e293b"),
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
