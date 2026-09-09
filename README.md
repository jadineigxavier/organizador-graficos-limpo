# Organizador de Arquivos Gráficos

Script em Python para **renomear e organizar em lote arquivos de um fluxo de pré-impressão offset**, aplicando na automação as verificações que normalmente são feitas manualmente ao receber arquivos de clientes: resolução, modo de cor e padronização de nomes para não quebrar RIP/software de imposição.

Projeto de portfólio construído a partir da experiência prática em análise de arquivos para impressão offset.

## O que ele resolve

Em uma gráfica, é comum receber lotes de arquivos de clientes fora do padrão: fotos em RGB quando deveriam estar em CMYK, imagens em baixa resolução, nomes de arquivo com acento/espaço que dão problema no RIP, e nenhuma rastreabilidade de qual arquivo pertence a qual Ordem de Serviço (OS). Este script automatiza a primeira triagem desse lote.

## O que o script faz

Para cada arquivo de uma pasta de entrada, o script:

1. **Classifica** o arquivo por tipo: vetor (`.ai .eps .cdr .svg`), documento (`.pdf .indd`) ou imagem (`.tif .tiff .jpg .jpeg .png .psd`).
2. **Para imagens**, verifica a resolução (DPI) e o modo de cor com Pillow, e decide o destino:
   - `Prontos_Para_Chapa` — DPI ≥ 300 e modo CMYK (padrão pronto para impressão)
   - `Revisar_Baixa_Resolucao` — abaixo do DPI mínimo configurado
   - `Revisar_Perfil_Cor` — fora do modo de cor esperado (ex. RGB)
3. **Renomeia** cada arquivo com um padrão rastreável, extraindo automaticamente o número da OS do nome original quando existe (ex. `OS1023_foto.jpg` → `20260908_OS1023_imagem_001.jpg`), e remove acentos/espaços/caracteres especiais do nome final.
4. **Copia (ou move)** o arquivo para a subpasta de destino, preservando a origem por padrão.
5. **Gera um relatório em CSV** com tudo que foi processado: nome original, nome novo, categoria, DPI, modo de cor e o motivo da decisão — útil para auditoria depois.

Todas as regras (DPI mínimo, modos de cor aceitos, nomes das pastas, padrão de nome) são configuráveis por um arquivo JSON, sem precisar editar o código.

## Tecnologias

- Python 3.10+
- Pillow (leitura de DPI e modo de cor)
- tkinter para a interface gráfica opcional (já vem com o Python no Windows)
- Apenas biblioteca padrão para o resto (argparse, pathlib, shutil, csv, threading)

## Estrutura do projeto

```
organizador-graficos/
├── organizador/
│   ├── main.py         # CLI: varre a pasta, orquestra tudo
│   ├── gui.py           # interface gráfica (tkinter), opcional
│   ├── config.py        # regras padrão + carregamento de config.json
│   ├── inspector.py      # leitura de DPI e modo de cor via Pillow
│   ├── classifier.py     # decide a pasta de destino de cada arquivo
│   ├── renamer.py        # gera o novo nome (extrai OS, remove acentos)
│   └── report.py         # grava o relatório CSV
├── run.py                # atalho de execução via terminal (python run.py ...)
├── run_gui.py             # atalho para abrir a interface gráfica (python run_gui.py)
├── config.example.json   # exemplo de configuração customizada
├── requirements.txt
└── README.md
```

## Como rodar

```bash
git clone https://github.com/jadineigxavier/Automa-o-de-Organiza-o-de-Arquivos
cd organizador-graficos

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

**Simular antes de mexer em qualquer arquivo (recomendado na primeira vez):**

```bash
python run.py --origem ./entrada --destino ./saida --simular
```

**Copiar os arquivos organizados (não mexe na pasta de origem):**

```bash
python run.py --origem ./entrada --destino ./saida
```

**Mover em vez de copiar:**

```bash
python run.py --origem ./entrada --destino ./saida --mover
```

## Interface gráfica (opcional)

Para quem prefere não usar o terminal, existe uma tela simples feita com `tkinter` (já vem instalado junto com o Python no Windows, não precisa instalar nada a mais):

```bash
python run_gui.py
```

Nela dá para escolher a pasta de origem e de destino pelo explorador de arquivos, marcar "Simular" ou "Mover em vez de copiar", e acompanhar o processamento em um log na tela, sem digitar nenhum comando. É a mesma lógica da CLI por trás — qualquer regra de classificação continua vindo de `organizador/config.py` ou de um `config.json` customizado.

**Usando uma configuração customizada** (por exemplo, mudando o DPI mínimo para 250):

```bash
python run.py --origem ./entrada --destino ./saida --config config.example.json
```

## Exemplo de saída no terminal

```
[Prontos_Para_Chapa] OS1023_capa_revista.tif  ->  20260908_OS1023_imagem_001.tif  (DPI e modo de cor dentro do padrão de impressão.)
[Revisar_Perfil_Cor] OS1023_foto_produto.jpg  ->  20260908_OS1023_imagem_001.jpg  (Modo de cor 'RGB' fora do padrão CMYK.)
[Revisar_Baixa_Resolucao] logo_cliente_baixa.tif  ->  20260908_OS0000_imagem_001.tif  (Resolução abaixo de 300 DPI)
[Vetores] OS1023_logo_vetor.ai  ->  20260908_OS1023_vetor_001.ai  (Arquivo vetorial (não requer checagem de DPI/cor).)

Relatório salvo em: saida/relatorio_20260908_235900.csv
Total processado: 7 arquivo(s).
```

## Limitações conhecidas

- A checagem de DPI/cor funciona para os formatos que o Pillow lê nativamente (TIFF, JPEG, PNG). Arquivos `.psd` com camadas complexas podem não ser lidos corretamente pelo Pillow.
- PDF e INDD são apenas separados por tipo — a leitura de DPI dentro de um PDF exigiria uma biblioteca adicional (fora do escopo deste script).
- A extração do número de OS depende de o nome do arquivo conter um padrão como `OS1023`, `os_1023` ou `OS-1023`; sem isso, é usado o código padrão configurável (`--os-padrao`).

## Possíveis evoluções

- Suporte a leitura de DPI dentro de PDFs (ex. com `pypdf` + rasterização)
- Interface gráfica simples (ex. com `tkinter`) para quem não usa terminal
- Modo "watch" para organizar automaticamente uma pasta monitorada

## Licença

Criado por Jadinei G Xavier

MIT — sinta-se livre para usar como base para o seu próprio portfólio.
