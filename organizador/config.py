"""Configurações do organizador: grupos de extensão, limites de qualidade
para impressão offset e o padrão de renomeação.

Todas essas regras podem ser sobrescritas por um arquivo JSON externo
(veja config.example.json), sem precisar tocar no código.
"""

import json
from pathlib import Path
from typing import Any, Dict

# Extensões típicas de um fluxo de pré-impressão, agrupadas por natureza.
GRUPOS_EXTENSAO: Dict[str, list] = {
    "vetores": [".ai", ".eps", ".cdr", ".svg"],
    "documentos": [".pdf", ".indd"],
    "imagens": [".tif", ".tiff", ".jpg", ".jpeg", ".png", ".psd"],
}

# Regras de qualidade para arquivos que forem para chapa/offset.
# Baseado no padrão de mercado: 300 DPI e modo CMYK na resolução final.
REGRAS_QUALIDADE = {
    "dpi_minimo": 300,
    "modos_cor_aceitos": ["CMYK"],
    "modos_cor_alerta": ["RGB", "L", "P"],
}

# Nomes das pastas de destino.
PASTAS_DESTINO = {
    "prontos": "Prontos_Para_Chapa",
    "revisar_dpi": "Revisar_Baixa_Resolucao",
    "revisar_cor": "Revisar_Perfil_Cor",
    "vetores": "Vetores",
    "documentos": "Documentos",
    "outros": "Outros",
}

# Padrão de nome final. Campos disponíveis: {data} {os} {categoria}
# {indice} {nome_original} {ext}
PADRAO_NOME = "{data}_OS{os}_{categoria}_{indice:03d}{ext}"

# Formato da data usado em {data}
FORMATO_DATA = "%Y%m%d"


def carregar_config(caminho_config: str | None) -> Dict[str, Any]:
    """Monta a configuração final, aplicando overrides de um JSON externo
    (se informado) sobre os valores padrão deste módulo."""
    config = {
        "grupos_extensao": GRUPOS_EXTENSAO,
        "regras_qualidade": REGRAS_QUALIDADE,
        "pastas_destino": PASTAS_DESTINO,
        "padrao_nome": PADRAO_NOME,
        "formato_data": FORMATO_DATA,
    }

    if not caminho_config:
        return config

    caminho = Path(caminho_config)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {caminho}")

    with caminho.open("r", encoding="utf-8") as f:
        overrides = json.load(f)

    for chave, valor in overrides.items():
        if isinstance(valor, dict) and isinstance(config.get(chave), dict):
            config[chave].update(valor)
        else:
            config[chave] = valor

    return config
