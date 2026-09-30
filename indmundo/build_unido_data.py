import json
import os
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_unido_country(session, url, dataset_id, country_code, periods):
    payload = {
        "datasetId": dataset_id,
        "countryCode": country_code,
        "periods": periods,
        "fullPrecision": True
    }
    try:
        res = session.post(url, json=payload, headers={'content-type': 'application/json', 'user-agent': 'Mozilla/5.0'}, timeout=12)
        if res.status_code == 200:
            data = res.json().get('data', [])
            if data:
                df = pd.DataFrame(data)
                df['country'] = country_code
                return df
    except Exception as e:
        pass
    return None

def build_unido():
    print("Obtendo metadados da UNIDO...")
    meta_res = requests.get("https://stat.unido.org/portal/dataset/getDataset/NATIONAL_ACCOUNTS", timeout=15)
    meta = meta_res.json()
    meta_cou = pd.json_normalize(meta["countries"])
    meta_var = pd.json_normalize(meta["variables"])
    
    url = "https://stat.unido.org/portal/dataset/getDataWithoutActivities"
    dataset_id = meta["id"]
    periods = meta["periods"]
    
    # Filtrar apenas variáveis de interesse (Iva e Mva)
    target_vars = [v for v in meta_var["c"] if "Iva" in v or "Mva" in v]
    
    print(f"Buscando dados para {len(meta_cou)} países da UNIDO...")
    dfs = []
    session = requests.Session()
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(fetch_unido_country, session, url, dataset_id, cc, periods): cc
            for cc in meta_cou["c"]
        }
        for future in as_completed(futures):
            res_df = future.result()
            if res_df is not None and not res_df.empty:
                dfs.append(res_df)
                
    if not dfs:
        print("Nenhum dado retornado da UNIDO.")
        return
        
    df = pd.concat(dfs, axis=0, ignore_index=True)
    df = df.loc[df["c"].isin(target_vars)]
    
    meta_cou = meta_cou.rename(columns={"lang.en": "País", "c": "country_code"})
    meta_var = meta_var.rename(columns={"lang.en": "Variável", "c": "var_code"})
    
    df = df.merge(meta_cou[["country_code", "País"]], how="left", left_on="country", right_on="country_code")
    df = df.merge(meta_var[["var_code", "Variável"]], how="left", left_on="c", right_on="var_code")
    
    df = df.rename(columns={"p": "Data", "v": "Valor"})
    df = df[["Data", "Valor", "País", "Variável"]]
    df["Data"] = df["Data"].astype(str)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "País"])
    
    out_parquet = os.path.join("indmundo", "IND_MUNDO_UNIDO.parquet")
    df.to_parquet(out_parquet, index=False)
    print(f"Salvo {len(df)} registros em {out_parquet}")

if __name__ == "__main__":
    build_unido()
