import json
import os
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_country(session, url, dataset_id, country_code, periods):
    payload = {
        "datasetId": dataset_id,
        "countryCode": country_code,
        "periods": periods,
        "fullPrecision": True
    }
    headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        r = session.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                df = pd.DataFrame(data)
                df["country_code"] = country_code
                return df
    except Exception:
        pass
    return None

def main():
    print("Obtendo metadados da UNIDO...")
    r = requests.get("https://stat.unido.org/portal/dataset/getDataset/NATIONAL_ACCOUNTS", timeout=15)
    meta = r.json()
    dataset_id = meta["id"]
    periods = meta["periods"] # 1990 a 2025
    
    meta_cou = pd.json_normalize(meta["countries"])
    meta_var = pd.json_normalize(meta["variables"])
    
    url = "https://stat.unido.org/portal/dataset/getDataWithoutActivities"
    
    # Selecionar os 40 maiores países industriais pelo código UNIDO
    # Brazil = 076, USA = 840, China = 156, Germany = 276, Japan = 392, etc.
    priority_isos = [
        "BRA", "USA", "CHN", "DEU", "JPN", "KOR", "IND", "ITA", "FRA", "GBR",
        "MEX", "CAN", "ESP", "RUS", "IDN", "TUR", "NLD", "CHE", "POL", "ARG",
        "AUS", "BEL", "SWE", "AUT", "SAU", "IRL", "THA", "VNM", "MYS", "ZAF",
        "COL", "CHL", "PER", "EGY", "PHL", "PRT", "NOR", "DNK", "FIN", "GRC"
    ]
    
    target_cou = meta_cou[meta_cou["iso3"].isin(priority_isos)]
    if len(target_cou) < 20:
        target_cou = meta_cou.head(50)
        
    print(f"Buscando dados reais para {len(target_cou)} países na API oficial da UNIDO...")
    
    dfs = []
    session = requests.Session()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_country, session, url, dataset_id, row["c"], periods): row["lang.en"]
            for _, row in target_cou.iterrows()
        }
        for future in as_completed(futures):
            res = future.result()
            if res is not None and not res.empty:
                dfs.append(res)
                
    if not dfs:
        print("Nenhum dado retornado.")
        return
        
    df = pd.concat(dfs, axis=0, ignore_index=True)
    
    # Filtrar variáveis de interesse: Iva e Mva
    df = df[df["c"].isin([v for v in meta_var["c"] if "Iva" in v or "Mva" in v])]
    
    meta_cou_clean = meta_cou.rename(columns={"lang.en": "País", "c": "c_code"})
    meta_var_clean = meta_var.rename(columns={"lang.en": "Variável", "c": "var_code"})
    
    df = df.merge(meta_cou_clean[["c_code", "País"]], how="left", left_on="country_code", right_on="c_code")
    df = df.merge(meta_var_clean[["var_code", "Variável"]], how="left", left_on="c", right_on="var_code")
    
    df = df.rename(columns={"p": "Data", "v": "Valor"})
    df = df[["Data", "Valor", "País", "Variável"]]
    df["Data"] = df["Data"].astype(str)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "País"])
    
    out_path = os.path.join("indmundo", "IND_MUNDO_UNIDO.parquet")
    df.to_parquet(out_path, index=False)
    print(f"Sucesso! {len(df)} registros reais salvos em {out_path}")

if __name__ == "__main__":
    main()
