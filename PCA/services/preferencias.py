# services/preferencias.py - ATUALIZADO

import json
import os

PREFERENCIAS_PATH = 'preferencias.json'

def get_default_preferences():
    """Retorna a estrutura padrão de preferências com os dados iniciais."""
    # URLs PADRÃO ATUALIZADAS
    return {
        "data_sources": {
            "2024": "https://pncp.gov.br/api/pncp/v1/orgaos/250106/planos-de-contratacao/2024/itens?pagina=1&tamanhoPagina=10000",
            "2025": "https://pncp.gov.br/api/pncp/v1/orgaos/250106/planos-de-contratacao/2025/itens?pagina=1&tamanhoPagina=10000",
            "2026": "https://pncp.gov.br/api/pncp/v1/orgaos/250106/planos-de-contratacao/2026/itens?pagina=1&tamanhoPagina=10000"
        },
        "filters": {},
        "ultima_verificacao_semanal": "2000-01-01"
    }

def carregar_preferencias():
    """Carrega as preferências do usuário do arquivo JSON."""
    if not os.path.exists(PREFERENCIAS_PATH):
        default_prefs = get_default_preferences()
        salvar_preferencias(default_prefs)
        return default_prefs
    try:
        with open(PREFERENCIAS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return get_default_preferences()

def salvar_preferencias(preferencias):
    """Salva as preferências do usuário no arquivo JSON."""
    try:
        with open(PREFERENCIAS_PATH, 'w', encoding='utf-8') as f:
            json.dump(preferencias, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar preferências: {e}")