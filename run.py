"""Atalho para rodar sem usar `python -m organizador.main`.

Exemplo:
    python run.py --origem ./entrada --destino ./saida
"""

from organizador.main import main

if __name__ == "__main__":
    raise SystemExit(main())
