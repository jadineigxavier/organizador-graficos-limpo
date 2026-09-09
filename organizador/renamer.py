"""Monta o novo nome de cada arquivo.

Duas preocupações vêm direto da rotina de pré-impressão:

1. Extrair o número da Ordem de Serviço (OS) do nome original, quando o
   cliente já manda o arquivo com essa referência, para manter
   rastreabilidade do job na pasta organizada.
2. Remover acentos, espaços e caracteres especiais do nome final — muitos
   RIPs e softwares de imposição de chapa ainda travam ou corrompem o
   caminho do arquivo com nomes fora do padrão ASCII.
"""

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional

PADRAO_OS = re.compile(r"os[_\-\s]?(\d{3,6})", re.IGNORECASE)


def extrair_os(nome_original: str) -> Optional[str]:
    match = PADRAO_OS.search(nome_original)
    return match.group(1) if match else None


def slugificar(texto: str) -> str:
    """Remove acentos e troca qualquer caractere fora de [a-z0-9-] por '-'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    sem_acento = sem_acento.lower().strip()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento).strip("-") or "arquivo"


def gerar_novo_nome(
    caminho_original: Path,
    categoria: str,
    indice: int,
    data_str: str,
    config: Dict[str, Any],
    os_padrao: str = "0000",
) -> str:
    numero_os = extrair_os(caminho_original.stem) or os_padrao
    nome_slug = slugificar(caminho_original.stem)

    novo_nome = config["padrao_nome"].format(
        data=data_str,
        os=numero_os,
        categoria=categoria,
        indice=indice,
        nome_original=nome_slug,
        ext=caminho_original.suffix.lower(),
    )
    return novo_nome
