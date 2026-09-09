"""Extrai metadados relevantes para controle de qualidade em impressão
offset: resolução (DPI) e modo de cor. Usa Pillow quando disponível;
se a imagem não puder ser lida (formato não suportado, arquivo corrompido),
o organizador não trava — apenas marca a informação como desconhecida.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from PIL import Image

    PILLOW_DISPONIVEL = True
except ImportError:  # Pillow é opcional: sem ela, só a organização por tipo funciona.
    PILLOW_DISPONIVEL = False


@dataclass
class InfoImagem:
    dpi: Optional[float]
    modo_cor: Optional[str]
    largura: Optional[int]
    altura: Optional[int]
    legivel: bool


def inspecionar_imagem(caminho: Path) -> InfoImagem:
    if not PILLOW_DISPONIVEL:
        return InfoImagem(dpi=None, modo_cor=None, largura=None, altura=None, legivel=False)

    try:
        with Image.open(caminho) as img:
            dpi_info = img.info.get("dpi")
            # Nem todo arquivo carrega DPI nos metadados (comum em PNG/print-screen);
            # nesse caso tratamos como resolução desconhecida, não como erro.
            dpi = float(dpi_info[0]) if dpi_info else None
            return InfoImagem(
                dpi=dpi,
                modo_cor=img.mode,
                largura=img.width,
                altura=img.height,
                legivel=True,
            )
    except Exception:
        return InfoImagem(dpi=None, modo_cor=None, largura=None, altura=None, legivel=False)
