"""Registra em CSV tudo que o organizador fez — essencial numa gráfica para
auditar depois "por que esse arquivo foi parar em Revisar_Baixa_Resolucao"
ou confirmar que todos os arquivos de uma OS foram processados.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List


CAMPOS = [
    "nome_original",
    "nome_novo",
    "categoria",
    "pasta_destino",
    "dpi",
    "modo_cor",
    "motivo",
    "acao",
]


def gravar_relatorio(caminho_csv: Path, linhas: List[Dict[str, Any]]) -> None:
    caminho_csv.parent.mkdir(parents=True, exist_ok=True)
    with caminho_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        for linha in linhas:
            writer.writerow({campo: linha.get(campo, "") for campo in CAMPOS})
