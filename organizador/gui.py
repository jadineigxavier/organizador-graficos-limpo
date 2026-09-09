"""Interface gráfica simples (tkinter) para o organizador de arquivos
gráficos, para quem prefere não usar o terminal.

Ela não substitui a CLI: só chama as mesmas funções de
`organizador.main`, `organizador.config` e `organizador.report`,
então qualquer correção feita ali vale para os dois jeitos de usar.

Como rodar:
    python run_gui.py
"""

import queue
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .config import carregar_config
from .main import processar
from .report import gravar_relatorio


class OrganizadorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador de Arquivos Gráficos")
        self.geometry("760x560")
        self.minsize(640, 480)

        # Fila usada para o thread de processamento avisar a interface
        # sobre novas linhas de log, sem mexer direto em widgets tkinter
        # de fora da thread principal (o que trava ou corrompe a UI).
        self._fila_log = queue.Queue()
        self._processando = False

        self._montar_layout()
        self.after(100, self._checar_fila_log)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _montar_layout(self):
        pad = {"padx": 10, "pady": 6}

        frame_campos = ttk.Frame(self)
        frame_campos.pack(fill="x", **pad)
        frame_campos.columnconfigure(1, weight=1)

        self.var_origem = tk.StringVar()
        self.var_destino = tk.StringVar()
        self.var_config = tk.StringVar()
        self.var_os_padrao = tk.StringVar(value="0000")
        self.var_mover = tk.BooleanVar(value=False)
        self.var_simular = tk.BooleanVar(value=True)

        self._linha_pasta(frame_campos, 0, "Pasta de origem:", self.var_origem, self._escolher_origem)
        self._linha_pasta(frame_campos, 1, "Pasta de destino:", self.var_destino, self._escolher_destino)
        self._linha_pasta(
            frame_campos,
            2,
            "Config (opcional):",
            self.var_config,
            self._escolher_config,
            tipo="arquivo",
        )

        ttk.Label(frame_campos, text="Código padrão de OS:").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frame_campos, textvariable=self.var_os_padrao, width=12).grid(
            row=3, column=1, sticky="w", pady=4
        )

        frame_opcoes = ttk.Frame(self)
        frame_opcoes.pack(fill="x", padx=10)
        ttk.Checkbutton(
            frame_opcoes, text="Simular (não mexe em nenhum arquivo)", variable=self.var_simular
        ).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(
            frame_opcoes, text="Mover em vez de copiar", variable=self.var_mover
        ).pack(side="left")

        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(fill="x", **pad)
        self.btn_processar = ttk.Button(frame_botoes, text="Processar", command=self._iniciar_processamento)
        self.btn_processar.pack(side="left")
        ttk.Button(frame_botoes, text="Limpar log", command=self._limpar_log).pack(side="left", padx=8)

        self.barra_progresso = ttk.Progressbar(frame_botoes, mode="indeterminate", length=180)
        self.barra_progresso.pack(side="right")

        ttk.Label(self, text="Log:").pack(anchor="w", padx=10)
        self.texto_log = scrolledtext.ScrolledText(self, height=20, state="disabled", wrap="word")
        self.texto_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _linha_pasta(self, parent, row, rotulo, variavel, comando_escolher, tipo="pasta"):
        ttk.Label(parent, text=rotulo).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variavel).grid(row=row, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(parent, text="Escolher...", command=comando_escolher).grid(row=row, column=2, pady=4)

    # ------------------------------------------------------------------
    # Seleção de pastas/arquivo
    # ------------------------------------------------------------------
    def _escolher_origem(self):
        caminho = filedialog.askdirectory(title="Escolha a pasta de origem")
        if caminho:
            self.var_origem.set(caminho)

    def _escolher_destino(self):
        caminho = filedialog.askdirectory(title="Escolha a pasta de destino")
        if caminho:
            self.var_destino.set(caminho)

    def _escolher_config(self):
        caminho = filedialog.askopenfilename(
            title="Escolha um arquivo de configuração (JSON)",
            filetypes=[("JSON", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            self.var_config.set(caminho)

    # ------------------------------------------------------------------
    # Log
    # ------------------------------------------------------------------
    def _log(self, mensagem: str):
        # Chamado a partir do thread de processamento: só enfileira,
        # quem escreve no widget é o loop principal (_checar_fila_log).
        self._fila_log.put(mensagem)

    def _checar_fila_log(self):
        # Além de despejar as linhas de log no widget, este loop também
        # detecta o marcador especial "__FIM__" (enviado pelo thread de
        # processamento) para reabilitar o botão e parar a barra de progresso.
        try:
            while True:
                mensagem = self._fila_log.get_nowait()
                if mensagem == "__FIM__":
                    self._processando = False
                    self.btn_processar.configure(state="normal")
                    self.barra_progresso.stop()
                    continue
                self.texto_log.configure(state="normal")
                self.texto_log.insert("end", mensagem + "\n")
                self.texto_log.see("end")
                self.texto_log.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._checar_fila_log)

    def _limpar_log(self):
        self.texto_log.configure(state="normal")
        self.texto_log.delete("1.0", "end")
        self.texto_log.configure(state="disabled")

    # ------------------------------------------------------------------
    # Processamento
    # ------------------------------------------------------------------
    def _iniciar_processamento(self):
        if self._processando:
            return

        origem = Path(self.var_origem.get().strip())
        destino_texto = self.var_destino.get().strip()
        config_texto = self.var_config.get().strip()
        os_padrao = self.var_os_padrao.get().strip() or "0000"

        if not self.var_origem.get().strip():
            messagebox.showwarning("Campo obrigatório", "Escolha a pasta de origem.")
            return
        if not destino_texto:
            messagebox.showwarning("Campo obrigatório", "Escolha a pasta de destino.")
            return
        if not origem.is_dir():
            messagebox.showerror("Pasta não encontrada", f"Pasta de origem não encontrada:\n{origem}")
            return

        try:
            config = carregar_config(config_texto or None)
        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("Erro na configuração", str(exc))
            return

        destino = Path(destino_texto)
        mover = self.var_mover.get()
        simular = self.var_simular.get()

        self._processando = True
        self.btn_processar.configure(state="disabled")
        self.barra_progresso.start(12)
        self._log(f"--- Iniciando processamento em {datetime.now().strftime('%H:%M:%S')} ---")

        thread = threading.Thread(
            target=self._processar_em_thread,
            args=(origem, destino, config, mover, simular, os_padrao),
            daemon=True,
        )
        thread.start()

    def _processar_em_thread(self, origem, destino, config, mover, simular, os_padrao):
        try:
            linhas = processar(
                origem=origem,
                destino=destino,
                config=config,
                mover=mover,
                simular=simular,
                os_padrao=os_padrao,
                log=self._log,
            )

            if not simular and linhas:
                caminho_relatorio = destino / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                gravar_relatorio(caminho_relatorio, linhas)
                self._log(f"\nRelatório salvo em: {caminho_relatorio}")

            self._log(f"\nTotal processado: {len(linhas)} arquivo(s).")
        except Exception as exc:  # mostra qualquer erro inesperado no log, sem travar a GUI
            self._log(f"\nErro inesperado: {exc}")
        finally:
            self._fila_log.put("__FIM__")


def main():
    app = OrganizadorGUI()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
