# services/downloader.py - ATUALIZADO

import requests
import pandas as pd
import io # Necessário para ler o conteúdo do download em memória
from .preferencias import carregar_preferencias

# A UASG padrão que será usada para filtrar todos os dados
UASG_PADRAO = '250052'

def download_csv_files():
    """
    Baixa os arquivos CSV, filtra pela UASG padrão em memória e salva
    apenas os dados relevantes no disco.
    """
    preferencias = carregar_preferencias()
    urls = preferencias.get("data_sources", {})

    if not urls:
        print("Nenhuma fonte de dados encontrada nas preferências.")
        return

    for ano, url in urls.items():
        print(f"📥 Baixando dados de {ano}...")
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            caminho_arquivo = f"data/pca_{ano}.csv"

            # Carrega o conteúdo baixado em um DataFrame do pandas
            # Usamos io.StringIO para tratar o texto como se fosse um arquivo
            df = pd.read_csv(io.StringIO(response.text), sep=';', dtype=str)

            print(f"📄 Original com {len(df)} linhas. Filtrando pela UASG {UASG_PADRAO}...")

            # Filtra o DataFrame para manter apenas as linhas da UASG desejada
            if 'UASG' in df.columns:
                df_filtrado = df[df['UASG'] == UASG_PADRAO].copy()
                print(f" फिल्टर Feito. {len(df_filtrado)} linhas salvas.")
            else:
                print("Aviso: Coluna 'UASG' não encontrada no arquivo. Salvando dados originais.")
                df_filtrado = df

            # Salva o DataFrame já filtrado no arquivo CSV
            df_filtrado.to_csv(caminho_arquivo, sep=';', index=False, encoding='utf-8')
            
            print(f"✅ Arquivo otimizado salvo: {caminho_arquivo}")

        except requests.RequestException as e:
            print(f"❌ Erro ao baixar dados de {ano}: {e}")