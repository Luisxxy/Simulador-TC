"""Módulo 4 – Autômato com Pilha (AP), não determinístico.

Formato JSON:
{
  "estados": ["q0","q1","q2"],
  "alfabeto": ["a","b"],
  "alfabeto_pilha": ["A","Z"],
  "estado_inicial": "q0",
  "simbolo_inicial_pilha": "Z",
  "estados_finais": ["q2"],
  "aceitacao": "estado_final",            # ou "pilha_vazia"
  "transicoes": [
    {"de":"q0","le":"a","desempilha":"Z","para":"q0","empilha":"AZ"}
  ]
}
"le", "desempilha" e "empilha" aceitam "λ" (ou "") = não ler / não desempilhar / não empilhar.
A pilha é uma cadeia com o TOPO NA ESQUERDA: empilhar "AZ" coloca A no topo, sobre Z.
"""
from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field

from .linguagens import LAMBDA


def _v(s: str) -> str:
    return "" if s in ("", LAMBDA, "ε") else s


@dataclass
class ResultadoAP:
    aceita: bool
    # cada passo: (leitura, restante, estado, pilha, operação)
    passos: list[tuple] = field(default_factory=list)
    explorados: int = 0
    motivo: str = ""


class AutomatoPilha:
    LIMITE_CONFIGS = 200_000
    LIMITE_PILHA = 1_000

    def __init__(self, estados, alfabeto, alfabeto_pilha, inicial, simbolo_pilha, finais,
                 transicoes, aceitacao="estado_final"):
        self.estados = list(estados)
        self.alfabeto = list(alfabeto)
        self.alfabeto_pilha = list(alfabeto_pilha)
        self.inicial = inicial
        self.simbolo_pilha = simbolo_pilha
        self.finais = set(finais)
        self.aceitacao = aceitacao
        self.transicoes = [(de, _v(le), _v(des), para, _v(emp)) for de, le, des, para, emp in transicoes]
        self._valida()

    @classmethod
    def de_dict(cls, d: dict) -> "AutomatoPilha":
        trans = [(t["de"], t["le"], t["desempilha"], t["para"], t["empilha"]) for t in d["transicoes"]]
        return cls(d["estados"], d["alfabeto"], d["alfabeto_pilha"], d["estado_inicial"],
                   d["simbolo_inicial_pilha"], d["estados_finais"], trans,
                   d.get("aceitacao", "estado_final"))

    @classmethod
    def de_json(cls, caminho: str) -> "AutomatoPilha":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_dict(json.load(f))

    def _valida(self):
        est = set(self.estados)
        if self.inicial not in est or not self.finais <= est:
            raise ValueError("Estado inicial/final fora de Q.")
        if self.simbolo_pilha not in self.alfabeto_pilha:
            raise ValueError("Símbolo inicial da pilha fora do alfabeto da pilha.")
        if self.aceitacao not in ("estado_final", "pilha_vazia"):
            raise ValueError("aceitacao deve ser 'estado_final' ou 'pilha_vazia'.")
        for de, le, des, para, emp in self.transicoes:
            if de not in est or para not in est:
                raise ValueError(f"Transição com estado desconhecido: {de} -> {para}")
            if le and le not in self.alfabeto:
                raise ValueError(f"Símbolo de entrada '{le}' fora do alfabeto.")
            if any(c not in self.alfabeto_pilha for c in des + emp):
                raise ValueError(f"Símbolo de pilha desconhecido na transição {de} -> {para}.")

    @staticmethod
    def _op(des: str, emp: str) -> str:
        partes = []
        if des:
            partes.append(f"desempilha {des}")
        if emp:
            partes.append(f"empilha {emp}")
        return ", ".join(partes) if partes else "—"

    def executar(self, w: str) -> ResultadoAP:
        for c in w:
            if c not in self.alfabeto:
                return ResultadoAP(False, motivo=f"símbolo '{c}' não pertence ao alfabeto")
        ini = (self.inicial, 0, self.simbolo_pilha)
        pai = {ini: None}
        fila = deque([ini])
        while fila:
            cfg = fila.popleft()
            q, pos, pilha = cfg
            aceita = pos == len(w) and (q in self.finais if self.aceitacao == "estado_final"
                                         else pilha == "")
            if aceita:
                return ResultadoAP(True, self._passos(pai, cfg, w), len(pai))
            if len(pai) > self.LIMITE_CONFIGS:
                return ResultadoAP(False, explorados=len(pai), motivo="limite de configurações atingido")
            for de, le, des, para, emp in self.transicoes:
                if de != q:
                    continue
                if le and (pos >= len(w) or w[pos] != le):
                    continue
                if des and not pilha.startswith(des):
                    continue
                nova_pilha = emp + pilha[len(des):]
                if len(nova_pilha) > self.LIMITE_PILHA:
                    continue
                nova = (para, pos + len(le), nova_pilha)
                if nova not in pai:
                    pai[nova] = (cfg, le, self._op(des, emp))
                    fila.append(nova)
        return ResultadoAP(False, explorados=len(pai), motivo="nenhuma computação aceita a cadeia")

    def _passos(self, pai, final, w):
        seq, cfg = [], final
        while pai[cfg] is not None:
            ant, le, op = pai[cfg]
            seq.append((cfg, le, op))
            cfg = ant
        seq.reverse()
        passos = [("(início)", w, self.inicial, self.simbolo_pilha, "—")]
        for (q, pos, pilha), le, op in seq:
            passos.append((f"lê '{le}'" if le else "λ", w[pos:] or LAMBDA, q, pilha or "(vazia)", op))
        return passos
