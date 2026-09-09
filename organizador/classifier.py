"""Decide para qual pasta cada arquivo deve ir, com base no tipo (vetor,
documento ou imagem) e, no caso de imagens, na resolução e no modo de cor —
os dois pontos que mais geram retrabalho em oficinas de impressão offset
quando o arquivo chega errado do cliente.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .inspector import InfoImagem, inspecionar_imagem


@dataclass
class Classificacao:
    categoria: str
    pasta_destino: str
    motivo: str
    dpi: Optional[float]
    modo_cor: Optional[str]


def _grupo_da_extensao(ext: str, grupos_extensao: Dict[str, list]) -> Optional[str]:
    ext = ext.lower()
    for grupo, extensoes in grupos_extensao.items():
        if ext in extensoes:
            return grupo
    return None


def classificar_arquivo(caminho: Path, config: Dict[str, Any]) -> Classificacao:
    ext = caminho.suffix.lower()
    grupo = _grupo_da_extensao(ext, config["grupos_extensao"])
    pastas = config["pastas_destino"]

    if grupo == "vetores":
        return Classificacao(
            categoria="vetor",
            pasta_destino=pastas["vetores"],
            motivo="Arquivo vetorial (não requer checagem de DPI/cor).",
            dpi=None,
            modo_cor=None,
        )

    if grupo == "documentos":
        return Classificacao(
            categoria="documento",
            pasta_destino=pastas["documentos"],
            motivo="PDF/INDD — checagem de DPI não é feita neste script (ver README).",
            dpi=None,
            modo_cor=None,
        )

    if grupo == "imagens":
        info: InfoImagem = inspecionar_imagem(caminho)
        regras = config["regras_qualidade"]

        if not info.legivel:
            return Classificacao(
                categoria="imagem",
                pasta_destino=pastas["revisar_dpi"],
                motivo="Não foi possível ler os metadados da imagem.",
                dpi=None,
                modo_cor=None,
            )

        dpi_ok = info.dpi is not None and info.dpi >= regras["dpi_minimo"]
        cor_ok = info.modo_cor in regras["modos_cor_aceitos"]

        if not dpi_ok:
            motivo = (
                f"Resolução abaixo de {regras['dpi_minimo']} DPI"
                if info.dpi
                else "Resolução não informada no arquivo (assumir revisão manual)."
            )
            return Classificacao(
                categoria="imagem",
                pasta_destino=pastas["revisar_dpi"],
                motivo=motivo,
                dpi=info.dpi,
                modo_cor=info.modo_cor,
            )

        if not cor_ok:
            return Classificacao(
                categoria="imagem",
                pasta_destino=pastas["revisar_cor"],
                motivo=f"Modo de cor '{info.modo_cor}' fora do padrão CMYK.",
                dpi=info.dpi,
                modo_cor=info.modo_cor,
            )

        return Classificacao(
            categoria="imagem",
            pasta_destino=pastas["prontos"],
            motivo="DPI e modo de cor dentro do padrão de impressão.",
            dpi=info.dpi,
            modo_cor=info.modo_cor,
        )

    return Classificacao(
        categoria="outro",
        pasta_destino=pastas["outros"],
        motivo="Tipo de arquivo não reconhecido pelas regras configuradas.",
        dpi=None,
        modo_cor=None,
    )
