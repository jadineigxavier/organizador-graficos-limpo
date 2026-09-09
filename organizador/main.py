"""CLI do organizador de arquivos gráficos.

Fluxo:
    origem/  ->  para cada arquivo:
                   1. classifica (vetor / documento / imagem apta / imagem
                      para revisar DPI / imagem para revisar cor / outro)
                   2. gera um novo nome rastreável (com nº de OS quando existe)
                   3. copia (ou move) para a subpasta de destino
                 -> grava um relatório CSV com tudo que foi feito

Exemplo de uso:
    python -m organizador.main --origem ./entrada --destino ./saida
    python -m organizador.main --origem ./entrada --destino ./saida --mover
    python -m organizador.main --origem ./entrada --destino ./saida --simular
"""

import argparse
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .classifier import classificar_arquivo
from .config import carregar_config
from .renamer import gerar_novo_nome
from .report import gravar_relatorio

EXTENSOES_IGNORADAS = {".ds_store", ".ini", ".tmp"}


def montar_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Organiza e renomeia em lote arquivos de um fluxo de pré-impressão offset."
    )
    parser.add_argument("--origem", required=True, help="Pasta com os arquivos a processar.")
    parser.add_argument("--destino", required=True, help="Pasta onde a estrutura organizada será criada.")
    parser.add_argument("--config", help="Caminho para um JSON de configuração customizado.")
    parser.add_argument(
        "--mover",
        action="store_true",
        help="Move os arquivos em vez de copiar (padrão é copiar, preservando a origem).",
    )
    parser.add_argument(
        "--simular",
        action="store_true",
        help="Mostra o que seria feito, sem copiar/mover nenhum arquivo (dry-run).",
    )
    parser.add_argument(
        "--os-padrao",
        default="0000",
        help="Código usado quando o nome do arquivo não traz um número de OS (padrão: 0000).",
    )
    return parser


def processar(
    origem: Path,
    destino: Path,
    config: dict,
    mover: bool,
    simular: bool,
    os_padrao: str,
    log=print,
) -> list:
    """Processa a pasta de origem.

    `log` recebe uma linha de texto por vez (por padrão, imprime no terminal).
    A GUI passa sua própria função aqui para mostrar o progresso na tela,
    sem precisar duplicar nada da lógica de classificação/renomeação.
    """
    linhas_relatorio = []
    contadores = defaultdict(int)
    data_str = datetime.now().strftime(config["formato_data"])

    arquivos = sorted(p for p in origem.iterdir() if p.is_file() and p.suffix.lower() not in EXTENSOES_IGNORADAS)

    if not arquivos:
        log(f"Nenhum arquivo encontrado em {origem}")
        return linhas_relatorio

    for caminho in arquivos:
        classificacao = classificar_arquivo(caminho, config)
        contadores[classificacao.pasta_destino] += 1
        indice = contadores[classificacao.pasta_destino]

        novo_nome = gerar_novo_nome(
            caminho, classificacao.categoria, indice, data_str, config, os_padrao=os_padrao
        )
        pasta_final = destino / classificacao.pasta_destino
        caminho_final = pasta_final / novo_nome

        acao = "simulado"
        if not simular:
            pasta_final.mkdir(parents=True, exist_ok=True)
            if mover:
                shutil.move(str(caminho), str(caminho_final))
                acao = "movido"
            else:
                shutil.copy2(str(caminho), str(caminho_final))
                acao = "copiado"

        log(f"[{classificacao.pasta_destino}] {caminho.name}  ->  {novo_nome}  ({classificacao.motivo})")

        linhas_relatorio.append(
            {
                "nome_original": caminho.name,
                "nome_novo": novo_nome,
                "categoria": classificacao.categoria,
                "pasta_destino": classificacao.pasta_destino,
                "dpi": classificacao.dpi or "",
                "modo_cor": classificacao.modo_cor or "",
                "motivo": classificacao.motivo,
                "acao": acao,
            }
        )

    return linhas_relatorio


def main(argv=None) -> int:
    args = montar_argparser().parse_args(argv)

    origem = Path(args.origem)
    destino = Path(args.destino)

    if not origem.is_dir():
        print(f"Pasta de origem não encontrada: {origem}", file=sys.stderr)
        return 1

    config = carregar_config(args.config)

    linhas = processar(
        origem=origem,
        destino=destino,
        config=config,
        mover=args.mover,
        simular=args.simular,
        os_padrao=args.os_padrao,
    )

    if not args.simular and linhas:
        caminho_relatorio = destino / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        gravar_relatorio(caminho_relatorio, linhas)
        print(f"\nRelatório salvo em: {caminho_relatorio}")

    print(f"\nTotal processado: {len(linhas)} arquivo(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
