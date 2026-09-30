import pandas as pd
import streamlit as st
import re

aux_pcons = pd.read_excel("cac/CAC_PRECOS_CONSTANTES.xls", dtype=str)
aux_pcorr = pd.read_excel("cac/CAC_PRECOS_CORRENTES.xls", dtype=str)

aux_dict1 = pd.read_excel("cac/CAC_SEGMENTACOES.xlsx", dtype=str)

aux_dict2 = [
    {"Vari\u00e1vel": "Coeficiente de exporta\u00e7\u00e3o", "Var": "CEX"},
    {
        "Vari\u00e1vel": "Coeficiente de exporta\u00e7\u00f5es l\u00edquidas",
        "Var": "CEL",
    },
    {"Vari\u00e1vel": "Coeficiente de insumos industriais importados", "Var": "CII"},
    {
        "Vari\u00e1vel": "Coeficiente de penetra\u00e7\u00e3o das importa\u00e7\u00f5es",
        "Var": "CPI",
    },
]
aux_dict2 = pd.json_normalize(aux_dict2)


def update_cac_pcons(xl_pcons):
    try:
        dfs = pd.read_excel(xl_pcons, sheet_name=None)

        # Unir daframes das diferentes abas da planilha
        for key, df in dfs.items():
            df[key] = key

        for key, df in dfs.items():
            dfs[key] = df.dropna(subset=[df.columns[4]])

        for key, df in dfs.items():
            df.columns = df.iloc[0]
            df.drop(df.index[0], inplace=True)

        dfs = [df.loc[:, df.columns.notna()] for df in dfs.values()]
        # Iterate over the dictionary of dataframes
        for df in dfs:
            # Iterate over each column in the dataframe
            for column in df.columns:
                if isinstance(column, str) and any(
                    substring in column for substring in ["CPI", "CEL", "CII", "CEX"]
                ):
                    new_column_name = "Variável"  # Create a new column name
                    df.rename(
                        columns={column: new_column_name}, inplace=True
                    )  # Rename the column

        df = pd.concat(dfs, axis=0)
        if "Setores1 da Indústria de Transformação" in df.columns:
            df["Setores1"] = df["Setores1"].fillna(
                df["Setores1 da Indústria de Transformação"]
            )
            df = df.drop(columns="Setores1 da Indústria de Transformação")
        if "Destinos" in df.columns:
            df["Setores1"] = df["Setores1"].fillna(df["Destinos"])
            df = df.drop(columns="Destinos")

        df = df.melt(
            id_vars=[
                var
                for var in df.columns
                if "Setor" in str(var) or str(var) == "Variável"
            ],
            value_vars=[
                var
                for var in df.columns
                if "Setor" not in str(var) and str(var) != "Variável"
            ],
            var_name="Ano",
            value_name="Valor",
        )

        df["Ano"] = df["Ano"].apply(
            lambda x: int(float(x)) if isinstance(x, float) else x
        )
        df["Ano"] = df["Ano"].astype(str).apply(lambda x: re.sub(r"\D", "", x))

        df = df.merge(
            aux_dict1,
            how="left",
            left_on=[var for var in df.columns if "Setor" in var][0],
            right_on="Setor",
        )

        df = df.loc[~df["Valor"].isna()]
        df["Var"] = df["Variável"].str[0:3]

        df = df.merge(aux_dict2, how="left", left_on="Var", right_on="Var")

        df1 = df.loc[~df["Variável_x"].str.contains("3D")]
        df2 = df.loc[df["Variável_x"].str.contains("3D")]

        df2["ISIC Grupo"] = df2[[col for col in df2.columns if "Setores" in col]].sum(
            axis=1
        )
        df2["ISIC Grupo"] = df2["ISIC Grupo"].astype(str)

        df1 = df1.merge(
            aux_pcons,
            how="left",
            left_on=["Variável_y", "Segmentação 1"],
            right_on=["Variável", "Segmentação 1"],
        )

        aux_pcons["Segmentação 1"] = aux_pcons["Segmentação 1"].str[0:3]

        df2 = df2.merge(
            aux_pcons,
            how="left",
            left_on=["Variável_y", "ISIC Grupo"],
            right_on=["Variável", "Segmentação 1"],
        )

        df = pd.concat([df1, df2], axis=0)

        df["v3"] = ""

        df = df[["Código da Carga", "Ano", "v3", "Valor"]]

        df = df.rename(columns={"Código da Carga": "v1", "Ano": "v2", "Valor": "v4"})

        df["v2"] = df["v2"].astype("datetime64[ns]")
        df["v2"] = df["v2"].dt.date

        df = df.dropna(subset=["v1"])

        # Salvar
        return df
    except Exception as e:
        return st.error(f"Error: {e}")


def update_cac_pcorr(xl_pcorr):
    try:
        # Get the element to make updating easier
        dfs = pd.read_excel(xl_pcorr, sheet_name=None)

        # Unir daframes das diferentes abas da planilha
        for key, df in dfs.items():
            df[key] = key

        for key, df in dfs.items():
            dfs[key] = df.dropna(subset=[df.columns[4]])

        for key, df in dfs.items():
            df.columns = df.iloc[0]
            df.drop(df.index[0], inplace=True)

        # Iterate over the dictionary of dataframes
        for key, df in dfs.items():
            # Iterate over each column in the dataframe
            for column in df.columns:
                unique_values = df[column].unique()
                # Check if the column has a single unique value and it is equal to the column name
                if len(unique_values) == 1 and unique_values[0] == column:
                    new_column_name = "Variável"  # Create a new column name
                    df.rename(
                        columns={column: new_column_name}, inplace=True
                    )  # Rename the column

        df = pd.concat(dfs, axis=0)
        df = df.loc[:, df.columns.notna()]
        df = df.reset_index(drop=True)

        df = df.melt(
            id_vars=[
                var
                for var in df.columns
                if "Setor" in str(var) or str(var) == "Variável"
            ],
            value_vars=[
                var
                for var in df.columns
                if "Setor" not in str(var) and str(var) != "Variável"
            ],
            var_name="Ano",
            value_name="Valor",
        )

        df["Ano"] = df["Ano"].apply(
            lambda x: int(float(x)) if isinstance(x, float) else x
        )
        df["Ano"] = df["Ano"].astype(str).apply(lambda x: re.sub(r"\D", "", x))

        df = df.merge(
            aux_dict1,
            how="left",
            left_on=[var for var in df.columns if "Setor" in var][0],
            right_on="Setor",
        )

        df = df.loc[~df["Valor"].isna()]
        df["Var"] = df["Variável"].str[0:3]

        df = df.merge(aux_dict2, how="left", left_on="Var", right_on="Var")

        df1 = df.loc[~df["Variável_x"].str.contains("3D")]
        df2 = df.loc[df["Variável_x"].str.contains("3D")]

        df2["ISIC Grupo"] = df2[[col for col in df2.columns if "Setores" in col]].sum(
            axis=1
        )
        df2["ISIC Grupo"] = df2["ISIC Grupo"].astype(str)

        df1 = df1.merge(
            aux_pcorr,
            how="left",
            left_on=["Variável_y", "Segmentação 1"],
            right_on=["Variável", "Segmentação 1"],
        )

        aux_pcorr["Segmentação 1"] = aux_pcorr["Segmentação 1"].str[0:3]

        df2 = df2.merge(
            aux_pcorr,
            how="left",
            left_on=["Variável_y", "ISIC Grupo"],
            right_on=["Variável", "Segmentação 1"],
        )

        df = pd.concat([df1, df2], axis=0)

        df["v3"] = ""

        df = df[["Código da Carga", "Ano", "v3", "Valor"]]

        df = df.rename(columns={"Código da Carga": "v1", "Ano": "v2", "Valor": "v4"})

        df["v2"] = df["v2"].astype("datetime64[ns]")
        df["v2"] = df["v2"].dt.date

        df = df.dropna(subset=["v1"])

        # Salvar
        return df

    except Exception as e:
        return st.error(f"Error: {e}")
