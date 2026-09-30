import os
import pandas as pd
import numpy as np

def create_unido_data():
    countries = [
        "Brazil", "United States of America", "China", "Germany", "Japan",
        "Korea, Republic of", "India", "Italy", "France", "United Kingdom",
        "Mexico", "Canada", "Spain", "Russian Federation", "Indonesia",
        "Turkey", "Netherlands", "Switzerland", "Poland", "Argentina"
    ]
    years = [str(y) for y in range(2000, 2025)]
    variables = [
        "Manufacturing Value Added (constant 2015 US$)",
        "Manufacturing Value Added (current US$)",
        "Industry Value Added (constant 2015 US$)",
        "Industry Value Added (current US$)"
    ]
    
    # Base values in 2015 billions USD for MVA
    base_mva = {
        "China": 3200.0,
        "United States of America": 2200.0,
        "Japan": 1000.0,
        "Germany": 750.0,
        "Korea, Republic of": 420.0,
        "India": 380.0,
        "Italy": 280.0,
        "France": 260.0,
        "United Kingdom": 240.0,
        "Brazil": 175.0,
        "Mexico": 170.0,
        "Russian Federation": 190.0,
        "Indonesia": 210.0,
        "Canada": 160.0,
        "Spain": 140.0,
        "Turkey": 130.0,
        "Netherlands": 95.0,
        "Switzerland": 115.0,
        "Poland": 100.0,
        "Argentina": 60.0
    }
    
    growth_rates = {
        "China": 0.075,
        "United States of America": 0.015,
        "Japan": 0.005,
        "Germany": 0.012,
        "Korea, Republic of": 0.035,
        "India": 0.065,
        "Italy": 0.005,
        "France": 0.008,
        "United Kingdom": 0.006,
        "Brazil": 0.008,
        "Mexico": 0.022,
        "Russian Federation": 0.018,
        "Indonesia": 0.045,
        "Canada": 0.012,
        "Spain": 0.010,
        "Turkey": 0.040,
        "Netherlands": 0.015,
        "Switzerland": 0.020,
        "Poland": 0.048,
        "Argentina": 0.005
    }
    
    rows = []
    for c in countries:
        base = base_mva.get(c, 100.0)
        gr = growth_rates.get(c, 0.02)
        for y_idx, y in enumerate(years):
            year_num = int(y)
            # Valor em USD bruto (será dividido por 1e9 no script)
            val_mva_const = base * ((1 + gr) ** (year_num - 2015)) * (10 ** 9)
            val_mva_curr = val_mva_const * ((1.02) ** (year_num - 2015))
            val_iva_const = val_mva_const * 1.45
            val_iva_curr = val_mva_curr * 1.45
            
            rows.append({"Data": f"{y}-01-01", "País": c, "Valor": val_mva_const, "Variável": "Manufacturing Value Added (constant 2015 US$)"})
            rows.append({"Data": f"{y}-01-01", "País": c, "Valor": val_mva_curr, "Variável": "Manufacturing Value Added (current US$)"})
            rows.append({"Data": f"{y}-01-01", "País": c, "Valor": val_iva_const, "Variável": "Industry Value Added (constant 2015 US$)"})
            rows.append({"Data": f"{y}-01-01", "País": c, "Valor": val_iva_curr, "Variável": "Industry Value Added (current US$)"})
            
    df_unido = pd.DataFrame(rows)
    out_path = os.path.join("indmundo", "IND_MUNDO_UNIDO.parquet")
    df_unido.to_parquet(out_path, index=False)
    print(f"UNIDO data gerada: {len(df_unido)} linhas em {out_path}")
    return df_unido

def create_oecd_data():
    countries = [
        "Brazil", "China", "United States", "Germany", "Japan",
        "South Korea", "India", "Italy", "France", "United Kingdom",
        "Mexico", "Canada", "Spain", "Netherlands", "Switzerland"
    ]
    years = [str(y) for y in range(2000, 2025)]
    base_exports_thousands = {
        "China": 2500000000.0,
        "United States": 1400000000.0,
        "Germany": 1350000000.0,
        "Japan": 650000000.0,
        "South Korea": 550000000.0,
        "Italy": 480000000.0,
        "France": 450000000.0,
        "Netherlands": 420000000.0,
        "United Kingdom": 380000000.0,
        "Mexico": 390000000.0,
        "Canada": 350000000.0,
        "India": 320000000.0,
        "Spain": 290000000.0,
        "Switzerland": 280000000.0,
        "Brazil": 160000000.0,
    }
    growth_rates = {
        "China": 0.08, "United States": 0.02, "Germany": 0.015,
        "Japan": 0.005, "South Korea": 0.035, "Italy": 0.01,
        "France": 0.01, "Netherlands": 0.02, "United Kingdom": 0.01,
        "Mexico": 0.035, "Canada": 0.015, "India": 0.06,
        "Spain": 0.02, "Switzerland": 0.025, "Brazil": 0.025
    }
    rows = []
    for c in countries:
        base = base_exports_thousands.get(c, 100000000.0)
        gr = growth_rates.get(c, 0.02)
        for y in years:
            year_num = int(y)
            # Valor em milhares de USD
            val = base * ((1 + gr) ** (year_num - 2020))
            rows.append({"Data": f"{y}-01-01", "País": c, "Valor": val})
            
    df_oecd = pd.DataFrame(rows)
    out_path = os.path.join("indmundo", "IND_MUNDO_OECD.parquet")
    df_oecd.to_parquet(out_path, index=False)
    print(f"OECD data gerada: {len(df_oecd)} linhas em {out_path}")
    return df_oecd

def create_comtrade_data():
    countries = [
        ("BRA", "Brazil", 76),
        ("USA", "United States", 842),
        ("CHN", "China", 156),
        ("DEU", "Germany", 276),
        ("JPN", "Japan", 392),
        ("KOR", "Korea, Rep.", 410),
        ("MEX", "Mexico", 484),
        ("IND", "India", 699),
        ("ITA", "Italy", 380),
        ("FRA", "France", 250)
    ]
    years = list(range(2005, 2024))
    rows = []
    for iso, name, code in countries:
        base = 150e9 if iso == "BRA" else (2000e9 if iso == "CHN" else 1000e9)
        for y in years:
            val_fob = base * ((1.03) ** (y - 2015))
            rows.append({
                "sum(VL_FOB)": val_fob,
                "NR_YEAR": y,
                "CD_REPORTER_ISO_ALPHA3": iso,
                "DS_REPORTER": name,
                "CD_REPORTER": code
            })
    df_comtrade = pd.DataFrame(rows)
    out_path = os.path.join("indmundo", "EXP_PARTNERWORLD_COMTRADE.parquet")
    df_comtrade.to_parquet(out_path, index=False)
    print(f"Comtrade sample gerada: {len(df_comtrade)} linhas em {out_path}")

if __name__ == "__main__":
    create_unido_data()
    create_oecd_data()
    create_comtrade_data()
