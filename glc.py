"""Módulo 3 – Gramática Livre de Contexto (GLC).

Formato JSON:
{
  "variaveis": ["S"],
  "terminais": ["a", "b"],
  "simbolo_inicial": "S",
  "producoes": ["S -> aSb | λ"]          # ou {"S": ["aSb", "λ"]}
}
Todos os símbolos têm 1 caractere. "λ" (ou vazio) é a cadeia vazia.

Algoritmo de reconhecimento: busca em largura sobre FORMAS SENTENCIAIS,
sempre expandindo a variável mais à esquerda (derivação mais à esquerda),
com podas que garantem término (veja o README / documento técnico).
"""
from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass, field

from .linguagens import LAMBDA, mostra

LIMITE_NOS = 200_000


@dataclass
class No:
    rotulo: str
    filhos: list["No"] = field(default_factory=list)


@dataclass
class ResultadoGLC:
    aceita: bool
    formas: list[str] = field(default_factory=list)    # formas sentenciais da derivação
    passos: list[tuple] = field(default_factory=list)  # (variável, lado direito)
    arvore: No | None = None
    explorados: int = 0
    limite_atingido: bool = False


class GLC:
    def __init__(self, variaveis, terminais, producoes: dict[str, list[str]], inicial: str):
        self.variaveis = set(variaveis)
        self.terminais = set(terminais)
        self.inicial = inicial
        self.producoes = {v: list(dict.fromkeys(rhs)) for v, rhs in producoes.items()}
        self._valida()
        self.anulaveis = self._calcula_anulaveis()

    # ------------------------------------------------------------------
    @classmethod
    def de_dict(cls, d: dict) -> "GLC":
        prods = d["producoes"]
        if isinstance(prods, list):  # ["S -> aSb | λ", ...]
            tabela: dict[str, list[str]] = {}
            for linha in prods:
                esq, dire = re.split(r"->|→", linha, maxsplit=1)
                esq = esq.strip()
                for alt in dire.split("|"):
                    alt = alt.replace(" ", "")
                    alt = "" if alt in (LAMBDA, "ε") else alt
                    tabela.setdefault(esq, []).append(alt)
            prods = tabela
        else:
            prods = {v: ["" if r in (LAMBDA, "ε") else r.replace(" ", "") for r in rhs]
                     for v, rhs in prods.items()}
        return cls(d["variaveis"], d["terminais"], prods, d["simbolo_inicial"])

    @classmethod
    def de_json(cls, caminho: str) -> "GLC":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_dict(json.load(f))

    def _valida(self):
        if self.variaveis & self.terminais:
            raise ValueError("Variáveis e terminais devem ser conjuntos disjuntos.")
        if self.inicial not in self.variaveis:
            raise ValueError("O símbolo inicial deve ser uma variável.")
        for v, rhs in self.producoes.items():
            if v not in self.variaveis:
                raise ValueError(f"Lado esquerdo '{v}' não é variável.")
            for r in rhs:
                for c in r:
                    if c not in self.variaveis | self.terminais:
                        raise ValueError(f"Símbolo '{c}' em {v} -> {r} não foi declarado.")

    def _calcula_anulaveis(self) -> set[str]:
        """Variáveis que derivam λ (ponto fixo)."""
        an, mudou = set(), True
        while mudou:
            mudou = False
            for v, rhs in self.producoes.items():
                if v not in an and any(all(c in an for c in r) for r in rhs):
                    an.add(v)
                    mudou = True
        return an

    def __str__(self):
        linhas = []
        for v in sorted(self.producoes, key=lambda x: (x != self.inicial, x)):
            linhas.append(f"{v} -> " + " | ".join(mostra(r) for r in self.producoes[v]))
        return "\n".join(linhas)

    # ------------------------------------------------------------------
    def _viavel(self, forma: str, w: str, limite_forma: int) -> bool:
        """Podas: prefixo/sufixo de terminais, comprimento mínimo e tamanho máximo."""
        idx = [i for i, c in enumerate(forma) if c in self.variaveis]
        if not idx:
            return forma == w
        pref, suf = forma[:idx[0]], forma[idx[-1] + 1:]
        if len(pref) + len(suf) > len(w) or not w.startswith(pref) or not w.endswith(suf):
            return False
        minimo = sum(1 for c in forma if c in self.terminais or c not in self.anulaveis)
        return minimo <= len(w) and len(forma) <= limite_forma

    def derivar(self, w: str) -> ResultadoGLC:
        for c in w:
            if c not in self.terminais:
                return ResultadoGLC(False)
        limite_forma = 2 * len(w) + 6
        pais = {self.inicial: None}
        fila = deque([self.inicial])
        explorados = 0
        while fila:
            forma = fila.popleft()
            explorados += 1
            if forma == w:
                return self._reconstroi(pais, forma, explorados)
            if explorados > LIMITE_NOS:
                return ResultadoGLC(False, explorados=explorados, limite_atingido=True)
            i = next((k for k, c in enumerate(forma) if c in self.variaveis), None)
            if i is None:
                continue
            for rhs in self.producoes.get(forma[i], []):
                nova = forma[:i] + rhs + forma[i + 1:]
                if nova not in pais and self._viavel(nova, w, limite_forma):
                    pais[nova] = (forma, i, forma[i], rhs)
                    fila.append(nova)
        return ResultadoGLC(False, explorados=explorados)

    def _reconstroi(self, pais, final, explorados) -> ResultadoGLC:
        formas, passos, forma = [final], [], final
        while pais[forma] is not None:
            ant, i, var, rhs = pais[forma]
            passos.append((i, var, rhs))
            formas.append(ant)
            forma = ant
        formas.reverse()
        passos.reverse()
        # árvore: a "fronteira" acompanha a forma sentencial símbolo a símbolo
        raiz = No(self.inicial)
        fronteira = [raiz]
        for i, var, rhs in passos:
            no = fronteira[i]
            no.filhos = [No(c) for c in rhs] or [No(LAMBDA)]
            fronteira[i:i + 1] = [] if rhs == "" else no.filhos
        return ResultadoGLC(True, formas, [(v, r) for _, v, r in passos], raiz, explorados)


def desenha_arvore(no: No, prefixo: str = "", ultimo: bool = True, raiz: bool = True) -> list[str]:
    """Árvore de derivação em ASCII."""
    if raiz:
        linhas = [no.rotulo]
        novo_prefixo = ""
    else:
        linhas = [prefixo + ("└── " if ultimo else "├── ") + no.rotulo]
        novo_prefixo = prefixo + ("    " if ultimo else "│   ")
    for k, f in enumerate(no.filhos):
        linhas += desenha_arvore(f, novo_prefixo, k == len(no.filhos) - 1, False)
    return linhas
