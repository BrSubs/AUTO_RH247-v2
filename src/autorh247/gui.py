"""Interface grafica para as operacoes principais do AutoRH247."""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from autorh247.api.services import RH247Service
from autorh247.config import DEFAULT_CSV_PATH
from autorh247.core.processor import AbonoProcessor
from autorh247.core.validator import carregar_e_validar_csv


class AutoRH247App:
    """Janela principal para buscar, validar e processar planilhas."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AutoRH247")
        self.root.geometry("760x560")
        self.root.minsize(640, 460)
        self._criar_widgets()

    def _criar_widgets(self):
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        ttk.Label(container, text="AutoRH247", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(container, text="Automacao de abonos do RH247").grid(
            row=1, column=0, sticky="w", pady=(0, 14)
        )

        busca = ttk.LabelFrame(container, text="Buscar funcionario", padding=10)
        busca.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        busca.columnconfigure(0, weight=1)
        self.identificador = tk.StringVar()
        ttk.Entry(busca, textvariable=self.identificador).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        self.botao_buscar = ttk.Button(busca, text="Buscar", command=self.buscar)
        self.botao_buscar.grid(row=0, column=1)

        arquivo = ttk.Frame(container)
        arquivo.grid(row=3, column=0, sticky="new", pady=(0, 10))
        arquivo.columnconfigure(1, weight=1)
        ttk.Label(arquivo, text="Planilha:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.caminho_arquivo = tk.StringVar(value=str(DEFAULT_CSV_PATH))
        ttk.Entry(arquivo, textvariable=self.caminho_arquivo).grid(
            row=0, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Button(arquivo, text="Selecionar", command=self.selecionar_arquivo).grid(
            row=0, column=2
        )
        self.botao_validar = ttk.Button(arquivo, text="Validar planilha", command=self.validar)
        self.botao_validar.grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.botao_processar = ttk.Button(arquivo, text="Processar planilha", command=self.processar)
        self.botao_processar.grid(row=1, column=2, sticky="w", pady=(8, 0))

        saida = ttk.LabelFrame(container, text="Resultado", padding=8)
        saida.grid(row=4, column=0, sticky="nsew")
        saida.columnconfigure(0, weight=1)
        saida.rowconfigure(0, weight=1)
        self.saida = tk.Text(saida, wrap="word", state="disabled", font=("Consolas", 10))
        self.saida.grid(row=0, column=0, sticky="nsew")
        barra = ttk.Scrollbar(saida, orient="vertical", command=self.saida.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self.saida.configure(yscrollcommand=barra.set)
        self.status = tk.StringVar(value="Pronto")
        ttk.Label(container, textvariable=self.status).grid(row=5, column=0, sticky="w", pady=(8, 0))

    def _escrever(self, texto: str):
        self.saida.configure(state="normal")
        self.saida.delete("1.0", tk.END)
        self.saida.insert("1.0", texto)
        self.saida.configure(state="disabled")

    def _executar_em_background(self, nome: str, funcao):
        self.status.set(f"Executando: {nome}...")
        for botao in (self.botao_buscar, self.botao_validar, self.botao_processar):
            botao.configure(state="disabled")

        def trabalhador():
            try:
                resultado = funcao()
                self.root.after(0, lambda: self._finalizar(nome, resultado))
            except Exception as erro:
                self.root.after(0, lambda: self._finalizar_erro(nome, erro))

        threading.Thread(target=trabalhador, daemon=True).start()

    def _finalizar(self, nome: str, resultado):
        self._escrever(str(resultado))
        self.status.set(f"Concluido: {nome}")
        self._habilitar_botoes()

    def _finalizar_erro(self, nome: str, erro: Exception):
        self._escrever(f"Erro em {nome}: {erro}")
        self.status.set(f"Falha: {nome}")
        self._habilitar_botoes()
        messagebox.showerror("AutoRH247", str(erro))

    def _habilitar_botoes(self):
        for botao in (self.botao_buscar, self.botao_validar, self.botao_processar):
            botao.configure(state="normal")

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar planilha",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            self.caminho_arquivo.set(caminho)

    def buscar(self):
        identificador = self.identificador.get().strip()
        if not identificador:
            messagebox.showwarning("AutoRH247", "Informe um nome ou CPF.")
            return

        def acao():
            resultados = RH247Service().buscar_funcionario(identificador)
            if not resultados:
                return "Nenhum funcionario encontrado."
            linhas = [f"Total encontrado: {len(resultados)}", ""]
            for indice, colaborador in enumerate(resultados, start=1):
                linhas.extend([
                    f"--- Colaborador #{indice} ---",
                    f"ID: {colaborador.get('id')}",
                    f"Nome: {colaborador.get('nome')}",
                    f"CPF: {colaborador.get('cpf_f') or colaborador.get('numero_cpf')}",
                    f"Matricula: {colaborador.get('matricula')}",
                    f"Cargo: {colaborador.get('cargo_descricao')}",
                    "",
                ])
            return "\n".join(linhas)

        self._executar_em_background("busca", acao)

    def validar(self):
        caminho = Path(self.caminho_arquivo.get())
        if not caminho.exists():
            messagebox.showerror("AutoRH247", f"Arquivo nao encontrado: {caminho}")
            return

        def acao():
            frame = carregar_e_validar_csv(caminho)
            erros = (frame["Status"] == "ERRO").sum()
            return f"Linhas com erros estruturais: {erros}\n\n{frame.to_string(index=False)}"

        self._executar_em_background("validacao", acao)

    def processar(self):
        caminho = Path(self.caminho_arquivo.get())
        if not caminho.exists():
            messagebox.showerror("AutoRH247", f"Arquivo nao encontrado: {caminho}")
            return
        if not messagebox.askyesno(
            "Confirmar processamento",
            "O processamento pode alterar a planilha e a API. Deseja continuar?",
        ):
            return

        def acao():
            frame = AbonoProcessor().processar_arquivo(caminho)
            return frame.to_string(index=False)

        self._executar_em_background("processamento", acao)


def main():
    root = tk.Tk()
    AutoRH247App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
