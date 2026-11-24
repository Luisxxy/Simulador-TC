"""
Implementa um motor genérico + duas máquinas prontas:
  * Opção A: reconhecer L = { w#w | w ∈ {a,b}* }
  * Opção B: somar dois números em representação unária (0^n 1 0^m  ->  0^(n+m))

Convenções: "_" é o branco; movimentos "R" (direita), "L" (esquerda), "S" (parado).
Se não existir transição para (estado, símbolo), a máquina REJEITA.
"""
from __future__ import annotations

from dataclasses import dataclass, field

BRANCO = "_"


@dataclass
class ResultadoMT:
    aceita: bool
    passos: int
    motivo: str = ""
    historico: list[tuple] = field(default_factory=list)  # (estado, fita, posição da cabeça)
    fita_final: str = ""


class MaquinaTuring:
    def __init__(self, nome, estados, alfabeto_entrada, inicial, aceita, transicoes):
        self.nome = nome
        self.estados = list(estados)
        self.alfabeto_entrada = set(alfabeto_entrada)
        self.inicial = inicial
        self.aceita = aceita
        self.delta = transicoes  # (estado, símbolo) -> (novo estado, escreve, movimento)

    @staticmethod
    def _render(fita: dict[int, str], cabeca: int) -> tuple[str, int]:
        chaves = list(fita) + [cabeca]
        lo, hi = min(chaves), max(chaves)
        return "".join(fita.get(i, BRANCO) for i in range(lo, hi + 1)), cabeca - lo

    def executar(self, entrada: str, max_passos: int = 1_000_000) -> ResultadoMT:
        for c in entrada:
            if c not in self.alfabeto_entrada:
                return ResultadoMT(False, 0, f"símbolo '{c}' não pertence ao alfabeto de entrada")
        fita = {i: c for i, c in enumerate(entrada)}
        q, cab, passos = self.inicial, 0, 0
        hist = [(q, *self._render(fita, cab))]
        while True:
            if q == self.aceita:
                motivo = "estado de aceitação alcançado"
                ok = True
                break
            acao = self.delta.get((q, fita.get(cab, BRANCO)))
            if acao is None:
                ok, motivo = False, f"sem transição para ({q}, {fita.get(cab, BRANCO)})"
                break
            if passos >= max_passos:
                ok, motivo = False, "limite de passos excedido (possível laço)"
                break
            q, escreve, mov = acao
            if escreve == BRANCO:
                fita.pop(cab, None)
            else:
                fita[cab] = escreve
            cab += {"R": 1, "L": -1, "S": 0}[mov]
            passos += 1
            hist.append((q, *self._render(fita, cab)))
        final = "".join(fita[i] for i in sorted(fita))
        return ResultadoMT(ok, passos, motivo, hist, final)
    
# Opção A – L = { w#w | w ∈ {a,b}* }
def tm_w_hash_w() -> MaquinaTuring:
    """Estratégia: marca com X o 1º símbolo livre à esquerda de '#', vai até o 1º livre
    à direita de '#', compara e marca; repete. Ao final, só pode sobrar X à direita."""
    t = {}
    for c in "ab":
        t[("q0", c)] = (f"p{c}", "X", "R")           # memoriza c e marca
        for o in "ab":
            t[(f"p{c}", o)] = (f"p{c}", o, "R")      # anda até '#'
        t[(f"p{c}", "#")] = (f"s{c}", "#", "R")
        t[(f"s{c}", "X")] = (f"s{c}", "X", "R")      # pula símbolos já comparados
        t[(f"s{c}", c)] = ("volta", "X", "L")        # achou o par: marca
    t[("q0", "#")] = ("verifica", "#", "R")          # esquerda esgotada
    t[("verifica", "X")] = ("verifica", "X", "R")
    t[("verifica", BRANCO)] = ("qa", BRANCO, "S")    # direita também esgotada: ACEITA
    for c in "abX":
        t[("volta", c)] = ("volta", c, "L")
    t[("volta", "#")] = ("volta2", "#", "L")
    for c in "ab":
        t[("volta2", c)] = ("volta2", c, "L")
    t[("volta2", "X")] = ("q0", "X", "R")
    estados = ["q0", "pa", "pb", "sa", "sb", "volta", "volta2", "verifica", "qa"]
    return MaquinaTuring("w#w", estados, "ab#", "q0", "qa", t)

# Opção B – soma unária:  0^n 1 0^m  ->  0^(n+m)
def tm_soma_unaria() -> MaquinaTuring:
    """Troca o '1' por '0' (juntando os blocos) e apaga o último '0' (n+1+m-1 = n+m)."""
    t = {
        ("s0", "0"): ("s0", "0", "R"),
        ("s0", "1"): ("s1", "0", "R"),
        ("s1", "0"): ("s1", "0", "R"),
        ("s1", BRANCO): ("s2", BRANCO, "L"),
        ("s2", "0"): ("qa", BRANCO, "S"),
    }
    return MaquinaTuring("soma unária", ["s0", "s1", "s2", "qa"], "01", "s0", "qa", t)
