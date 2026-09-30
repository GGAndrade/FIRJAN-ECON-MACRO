import streamlit as st
import pandas as pd
import altair as alt
from func import google_sheets, set_y_max, set_y_min, to_excel2, tooltip_rework
from indmundo.utils import bar_chart_race, medida_desempenho
import json

with open("pt-BR-format.json", "rb") as f:
    pt_format = json.load(f)
with open("pt-BR-time-format.json", "rb") as f:
    pt_time_format = json.load(f)


def unido_fragment(prefix=""):
    df = google_sheets("IND_MUNDO_UNIDO")

    # Timezone data (necessário para os gráficos do pacote Altair trabalharem com data corretamente)
    df["Data"] = pd.to_datetime(df["Data"])
    if df["Data"].dt.tz is None:
        df["Data"] = df["Data"].dt.tz_localize("America/Sao_Paulo")

    # Outra maneira de ler a variável data
    df["Data pt"] = df["Data"].dt.strftime("%Y")

    # Mudar unidade para bilhões
    df["Valor"] = df["Valor"] / 1000000000

    col1, col2 = st.columns([7, 3])

    with col1:
        var = st.selectbox(
            label="Variável",
            options=df["Variável"].unique(),
            index=2,
            key=f"{prefix}var",
        )

    with col2:
        medida = st.radio(
            label="Medida",
            options=["Valor (bilhões US$)", "Participação (%)"],
            index=1,
            key=f"{prefix}medida1",
        )

    st.markdown(
        """
    #### Evolução país
    """
    )
    cou = st.multiselect(
        label="País",
        options=df["País"].unique(),
        default=["Brazil"],
        key=f"{prefix}cou1",
    )

    g1 = df.loc[df["Variável"] == var]
    g1["Participação no mundo (%)"] = (
        g1["Valor"] / g1.groupby("Data")["Valor"].transform("sum")
    ) * 100
    g1 = g1.loc[g1["País"].isin(cou)]

    if "current" in var:
        g1 = g1.loc[g1["Data"] != g1["Data"].unique().max()]

    # Criar intervalo para gráfico de linha
    ano_inicial, ano_final = st.select_slider(
        "Intervalo",
        options=g1["Data pt"].unique(),
        value=(
            (g1["Data"].min()).strftime("%Y"),
            (g1["Data"].max()).strftime("%Y"),
        ),
        key=f"{prefix}intervalo_cnae",
    )

    g1 = g1.loc[
        (g1["Data"] >= g1["Data"].loc[g1["Data pt"] == ano_inicial].min())
        & (g1["Data"] <= g1["Data"].loc[g1["Data pt"] == ano_final].min())
    ]

    # Definir mínimos e máximos do eixo y
    y_min = set_y_min(g1[medida_desempenho(medida)].min())
    y_max = set_y_max(g1[medida_desempenho(medida)].max())

    # Criar gráfico de linha
    line_chart = (
        alt.Chart(g1)
        .mark_line(strokeWidth=3, point=True)
        .encode(
            x=alt.X("Data", axis=alt.Axis(format="%Y", labelAngle=-90)),
            y=alt.Y(
                medida_desempenho(medida),
                scale=alt.Scale(domain=[y_min, y_max], zero=False),
            ),
            color="País",
        )
    )

    # Renderizar gráfico de linha

    line_chart = tooltip_rework(g1, line_chart, medida_desempenho(medida))

    line_chart["usermeta"] = {
        "embedOptions": {
            "formatLocale": pt_format,
            "timeFormatLocale": pt_time_format,
        }
    }
    st.altair_chart(line_chart, theme=None, use_container_width=True)

    st.markdown(
        """
    #### Variação anual: 15 maiores e 15 menores
    """
    )

    g4 = df.loc[df["Variável"] == var]
    g4["Participação no mundo (%)"] = (
        g4["Valor"] / g4.groupby("Data")["Valor"].transform("sum")
    ) * 100

    g4["Variação anual"] = g4.groupby(["País"])[medida_desempenho(medida)].diff()

    ano = st.select_slider(
        "Ano variações",
        options=g4["Data pt"].unique(),
        value=(g4["Data"].max()).strftime("%Y"),
        key=f"{prefix}ano_var1",
    )

    g4 = g4.loc[g4["Data pt"] == ano]

    g4 = g4.sort_values("Variação anual", ascending=False)

    g4 = g4.loc[~g4["Variação anual"].isna()]

    g4 = pd.concat([g4.head(15), g4.tail(15)], axis=0)

    chart = (
        alt.Chart(g4)
        .mark_bar()
        .encode(
            x="Variação anual:Q",
            y=alt.Y(
                "País:N",
                sort=alt.EncodingSortField(field="Variação anual:Q"),
            ),
            color=alt.condition(
                alt.datum["Variação anual"] > 0,  # condition
                alt.value("#376092"),  # color for positive values
                alt.value("#b90e0c"),  # color for negative values
            ),
        )
        .properties(height=800)
    )

    # Add text labels on top of the bars
    text1 = chart.mark_text(align="center", dx=15).encode(
        text=alt.Text("Variação anual:Q", format=".3f"),
        y=alt.Y(
            "País:N",
            sort=alt.EncodingSortField(field="Variação anual:Q"),
            axis=None,
        ),
        color=alt.value("#000000"),
    )

    chart = (chart + text1).resolve_scale(y="independent")

    # Renderizar
    st.altair_chart(chart, theme=None, use_container_width=True)

    st.markdown(
        """
    #### Evolução ranking países
    """
    )

    g2 = df.loc[df["Variável"] == var]
    g2["Participação no mundo (%)"] = (
        g2["Valor"] / g2.groupby("Data")["Valor"].transform("sum")
    ) * 100

    if "current" in var:
        g2 = g2.loc[g2["Data"] != g2["Data"].max()]

    g2s = []
    for ano in g2["Data pt"].unique():
        gw = g2.loc[g2["Data pt"] == ano]
        gw = gw.sort_values(medida_desempenho(medida), ascending=False)
        gw = gw.head(20)
        g2s.append(gw)

    g2 = pd.concat(g2s, axis=0)

    g2[medida_desempenho(medida)] = g2[medida_desempenho(medida)].apply(
        lambda x: round(x, 2)
    )

    g2 = g2.rename(columns={"Data pt": "Ano"})

    # Convert 'Ano' to numeric type
    g2["Ano"] = pd.to_numeric(g2["Ano"])

    bar_chart_race(g2, medida, 20)

    st.markdown(
        """
    #### Dados detalhados
    """
    )

    g3 = df.loc[df["Variável"] == var]
    g3["Participação no mundo (%)"] = (
        g3["Valor"] / g3.groupby("Data")["Valor"].transform("sum")
    ) * 100

    g3 = g3.drop(columns=["Data", "Variável"])
    g3 = g3.pivot(columns="Data pt", index="País", values=medida_desempenho(medida))

    g3 = g3.sort_values(g3.columns.max(), ascending=False)

    st.dataframe(g3)

    df_xlsx = to_excel2([g1, g3, g4])
    st.download_button(
        label="📥 Baixar dados",
        data=df_xlsx,
        file_name="Dados.xlsx",
        use_container_width=True,
        key=f"{prefix}unido_download",
    )
