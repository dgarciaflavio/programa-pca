# PCA/main.py (Versão Final)

import os
import sys

# Garante que o Python encontre os nossos módulos de serviço e UI
# (Esta parte é opcional dependendo do ambiente, mas ajuda a evitar erros)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# As importações dos seus módulos de serviço
from services.downloader import download_csv_files
from services.parser import load_all_years

# A importação da sua janela principal
from ui.main_window import iniciar_interface

# Importação do novo componente, com o caminho completo
from ui.ui_components import MultiSelectDialog


def main():
    """
    Função principal que orquestra a execução do programa.
    """
    # Garante que o diretório 'data' exista
    if not os.path.exists('data'):
        os.makedirs('data')

    # Inicia a interface gráfica do usuário
    iniciar_interface()


if __name__ == "__main__":
    main()