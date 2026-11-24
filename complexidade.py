"""Módulo 6 – Complexidade computacional dos algoritmos implementados.

n = tamanho da entrada; |Q| = nº de estados; |Σ| = tamanho do alfabeto.
Ω = limite inferior (melhor caso), Θ = limite justo (caso médio), O = limite superior (pior caso).
"""
from __future__ import annotations

from .automato_finito import Automato
from .automato_pilha import AutomatoPilha
from .glc import GLC
from .maquina_turing import tm_soma_unaria, tm_w_hash_w

# (algoritmo, melhor caso, caso médio, pior caso, justificativa)
TABELA = [
    ("Validar cadeia em Σ*", "Ω(1)", "Θ(n)", "O(n)",
     "Varre a cadeia; melhor caso: 1º símbolo inválido."),
    ("Tamanho |w|", "Θ(1)", "Θ(1)", "Θ(1)",
     "Python guarda o comprimento (formalmente Θ(n) se contar símbolo a símbolo)."),
    ("Concatenação u·v", "Ω(n+m)", "Θ(n+m)", "O(n+m)",
     "Copia as duas cadeias."),
    ("Enumerar Σ^k (e Σ* até k)", "Ω(|Σ|^k·k)", "Θ(|Σ|^k·k)", "O(|Σ|^k·k)",
     "Tamanho da saída domina: |Σ|^k cadeias de tamanho k."),
    ("Executar AFD", "Ω(1)", "Θ(n)", "O(n)",
     "1 transição por símbolo; melhor caso: falta transição no 1º símbolo."),
    ("Executar AFN (busca em configurações)", "Ω(1)", "Θ(n·|Q|)", "O(n·|Q|²)",
     "Há |Q|·(n+1) configurações (estado, posição), cada uma com até |Q| destinos."),
    ("AFN → AFD (subconjuntos)", "Ω(|Q|·|Σ|)", "depende do AFN", "O(2^|Q|·|Σ|·|Q|)",
     "Pode gerar até 2^|Q| subconjuntos."),
    ("Derivar GLC (BFS à esquerda + poda)", "Ω(n)", "Θ(n) p/ aⁿbⁿ", "O(b^L) – exponencial",
     "b = nº de alternativas, L = limite de tamanho da forma (2n+6). Referência: CYK = O(n³·|G|)."),
    ("Executar AP para aⁿbⁿ", "Ω(1)", "Θ(n)", "O(n)",
     "Cada símbolo faz 1 push/pop; melhor caso: cadeia começa com 'b'."),
    ("AP genérico (não determinístico)", "Ω(1)", "depende do AP", "O(|Q|·n·|Γ|^h)",
     "Configurações (estado, posição, pilha) com pilha de altura ≤ h."),
    ("MT para w#w", "Ω(n)", "Θ(n²)", "O(n²)",
     "Cada um dos ~n/2 pares exige ir e voltar na fita (~n passos)."),
    ("MT soma unária", "Ω(n+m)", "Θ(n+m)", "O(n+m)",
     "Uma varredura até o fim da fita e uma volta de 1 célula."),
]


def tabela_texto() -> str:
    cab = ("Algoritmo", "Melhor", "Médio", "Pior")
    larg = [max(len(r[i]) for r in TABELA + [cab]) for i in range(4)]
    linha = lambda r: " | ".join(r[i].ljust(larg[i]) for i in range(4))
    saida = [linha(cab), "-+-".join("-" * w for w in larg)]
    saida += [linha(r) for r in TABELA]
    return "\n".join(saida)


def benchmark(tamanhos=(2, 4, 8, 16, 32, 64)) -> list[tuple]:
    """Mede o nº de passos para entradas crescentes e a razão passos/n (ou /n²)."""
    afd = Automato(["p", "i"], ["a"], "p", ["p"],
                   [("p", "a", "i"), ("i", "a", "p")], "AFD")  # nº par de a's
    ap = AutomatoPilha.de_json(_ex("ap_anbn.json"))
    glc = GLC.de_json(_ex("glc_anbn.json"))
    mt1, mt2 = tm_w_hash_w(), tm_soma_unaria()
    linhas = []
    for n in tamanhos:
        r_afd = afd.executar("a" * n).explorados
        r_ap = len(ap.executar("a" * n + "b" * n).passos) - 1
        r_glc = glc.derivar("a" * n + "b" * n).explorados
        w = "ab" * (n // 2)
        r_mt1 = mt1.executar(w + "#" + w).passos
        r_mt2 = mt2.executar("0" * n + "1" + "0" * n).passos
        linhas.append((n, r_afd, r_ap, r_glc, r_mt1, r_mt1 / (2 * len(w) + 1) ** 2, r_mt2))
    return linhas


def _ex(nome: str) -> str:
    from pathlib import Path
    return str(Path(__file__).resolve().parent.parent / "exemplos" / nome)
