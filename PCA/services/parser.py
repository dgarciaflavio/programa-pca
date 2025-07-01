# services/parser.py - ATUALIZADO

import pandas as pd
from .preferencias import carregar_preferencias

def load_all_years():
    """
    Carrega todos os arquivos CSV definidos nas preferências em DataFrames do Pandas.
    Retorna um dicionário onde a chave é o ano e o valor é o DataFrame.
    """
    preferencias = carregar_preferencias()
    anos = preferencias.get("data_sources", {}).keys()
    
    dataframes = {}
    for ano in anos:
        try:
            caminho_arquivo = f"data/pca_{ano}.csv"
            # CORREÇÃO: Adicionado dtype=str para evitar DtypeWarning
            df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', header=0, dtype=str)
            df.fillna('', inplace=True) # Garante que valores nulos sejam strings vazias
            dataframes[ano] = df
        except FileNotFoundError:
            print(f"Aviso: Arquivo {caminho_arquivo} não encontrado. Ele será ignorado.")
            dataframes[ano] = pd.DataFrame() 
        except Exception as e:
            print(f"Erro ao carregar o arquivo para o ano {ano}: {e}")
            dataframes[ano] = pd.DataFrame()
            
    return dataframes