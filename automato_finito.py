"""Módulo 2 – Autômatos Finitos (AFD e AFN, com transições λ).

Formato JSON aceito (as transições podem ser lista ou dicionário):

{
  "tipo": "AFD",                      # ou "AFN"
  "estados": ["q0", "q1", "q2"],
  "alfabeto": ["a", "b"],
  "estado_inicial": "q0",
  "estados_finais": ["q2"],
  "transicoes": [ {"de": "q0", "simbolo": "a", "para": "q1"}, ... ]
}
Use "λ" (ou "") como símbolo para transições espontâneas (somente AFN).
"""
from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field

from .linguagens import LAMBDA


def _sim(s: str) -> str:
    return "" if s in ("", LAMBDA, "ε", "lambda") else s


@dataclass
class ResultadoAF:
    aceita: bool
    inicio: str = ""
    transicoes: list = field(default_factory=list)  # (de, simbolo, para)
    motivo: str = ""
    explorados: int = 0

    @property
    def caminho(self) -> list[str]:
        return [self.inicio] + [t[2] for t in self.transicoes]


class Automato:
    def __init__(self, estados, alfabeto, inicial, finais, transicoes, tipo="AFN"):
        self.estados = list(estados)
        self.alfabeto = list(alfabeto)
        self.inicial = inicial
        self.finais = set(finais)
        self.tipo = tipo.upper()
        self.delta: dict[tuple[str, str], set[str]] = {}
        for de, s, para in transicoes:
            self.delta.setdefault((de, _sim(s)), set()).add(para)
        self._valida()
    # Construção / validação

    @classmethod
    def de_dict(cls, d: dict) -> "Automato":
        trans = []
        t = d["transicoes"]
        if isinstance(t, dict):  # {"q0": {"a": "q1", "λ": ["q2", "q3"]}}
            for de, mapa in t.items():
                for sim, dest in mapa.items():
                    for p in ([dest] if isinstance(dest, str) else dest):
                        trans.append((de, sim, p))
        else:  # [{"de": "q0", "simbolo": "a", "para": "q1"}]
            for item in t:
                trans.append((item["de"], item["simbolo"], item["para"]))
        return cls(d["estados"], d["alfabeto"], d["estado_inicial"],
                   d["estados_finais"], trans, d.get("tipo", "AFN"))

    @classmethod
    def de_json(cls, caminho: str) -> "Automato":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_dict(json.load(f))

    def _valida(self):
        est = set(self.estados)
        if self.inicial not in est:
            raise ValueError(f"Estado inicial '{self.inicial}' não está em Q.")
        if not self.finais <= est:
            raise ValueError("Há estados finais que não pertencem a Q.")
        for (q, s), destinos in self.delta.items():
            if q not in est or not destinos <= est:
                raise ValueError(f"Transição com estado desconhecido: {q} --{s}--> {destinos}")
            if s != "" and s not in self.alfabeto:
                raise ValueError(f"Símbolo '{s}' da transição não pertence ao alfabeto.")
            if self.tipo == "AFD":
                if s == "":
                    raise ValueError("AFD não pode ter transições λ.")
                if len(destinos) > 1:
                    raise ValueError(f"AFD com não determinismo em δ({q},{s}).")

    def move(self, q: str, s: str) -> set[str]:
        return self.delta.get((q, s), set())
    
    # Execução
    def executar(self, cadeia: str) -> ResultadoAF:
        for c in cadeia:
            if c not in self.alfabeto:
                return ResultadoAF(False, self.inicial,
                                   motivo=f"símbolo '{c}' não pertence ao alfabeto")
        return self._executar_afd(cadeia) if self.tipo == "AFD" else self._executar_afn(cadeia)

    def _executar_afd(self, cadeia: str) -> ResultadoAF:
        q, trans = self.inicial, []
        for c in cadeia:
            destino = next(iter(self.move(q, c)), None)
            if destino is None:
                return ResultadoAF(False, self.inicial, trans, f"sem transição de {q} com '{c}'",
                                   len(trans))
            trans.append((q, c, destino))
            q = destino
        ok = q in self.finais
        return ResultadoAF(ok, self.inicial, trans,
                           "" if ok else f"terminou em {q}, que não é final", len(trans))

    def _executar_afn(self, cadeia: str) -> ResultadoAF:
        """Busca em largura sobre configurações (estado, posição) – acha um caminho de aceitação."""
        ini = (self.inicial, 0)
        pai = {ini: None}
        fila = deque([ini])
        while fila:
            q, pos = fila.popleft()
            if pos == len(cadeia) and q in self.finais:
                trans, cfg = [], (q, pos)
                while pai[cfg] is not None:
                    ant, s = pai[cfg]
                    trans.append((ant[0], s, cfg[0]))
                    cfg = ant
                trans.reverse()
                return ResultadoAF(True, self.inicial, trans, "", len(pai))
            candidatos = [("", p, pos) for p in self.move(q, "")]
            if pos < len(cadeia):
                candidatos += [(cadeia[pos], p, pos + 1) for p in self.move(q, cadeia[pos])]
            for s, p, npos in candidatos:
                if (p, npos) not in pai:
                    pai[(p, npos)] = ((q, pos), s)
                    fila.append((p, npos))
        return ResultadoAF(False, self.inicial, [], "nenhum caminho leva a estado final", len(pai))
    
    # Simulação por conjuntos de estados (visão "paralela" do AFN)
    def fecho(self, conjunto) -> set[str]:
        """Fecho-λ: estados alcançáveis apenas por transições λ."""
        res, pilha = set(conjunto), list(conjunto)
        while pilha:
            for p in self.move(pilha.pop(), ""):
                if p not in res:
                    res.add(p)
                    pilha.append(p)
        return res

    def traco_conjuntos(self, cadeia: str):
        """Lista de (símbolo lido, conjunto de estados ativos) após cada passo."""
        atual = self.fecho({self.inicial})
        tracos = [(None, atual)]
        for c in cadeia:
            atual = self.fecho({d for q in atual for d in self.move(q, c)})
            tracos.append((c, atual))
        return tracos
    
    # AFN -> AFD (construção de subconjuntos)
    def para_afd(self) -> "Automato":
        def nome(s):
            return "{" + ",".join(sorted(s)) + "}" if s else "∅"

        ini = frozenset(self.fecho({self.inicial}))
        vistos, fila, trans = {ini}, deque([ini]), []
        while fila:
            S = fila.popleft()
            for a in self.alfabeto:
                T = frozenset(self.fecho({d for q in S for d in self.move(q, a)}))
                trans.append((nome(S), a, nome(T)))
                if T not in vistos:
                    vistos.add(T)
                    fila.append(T)
        finais = [nome(S) for S in vistos if S & self.finais]
        return Automato([nome(S) for S in vistos], self.alfabeto, nome(ini), finais, trans, "AFD")
