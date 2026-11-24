"""Módulo 1 – Linguagens Formais.

Alfabeto (Σ), cadeias, Σ*, Σ+, tamanho, concatenação e linguagens
(conjunto finito de cadeias ou expressão regular).
"""
from __future__ import annotations

import re
from itertools import product

LAMBDA = "λ"


def normaliza(cadeia: str) -> str:
    """Converte 'λ' (ou 'ε') na cadeia vazia e remove espaços nas pontas."""
    cadeia = cadeia.strip()
    return "" if cadeia in (LAMBDA, "ε") else cadeia


def mostra(cadeia: str) -> str:
    """Representação para exibição: cadeia vazia aparece como λ."""
    return cadeia if cadeia else LAMBDA


class Alfabeto:
    """Alfabeto Σ: conjunto finito, não vazio, de símbolos (1 caractere cada)."""

    def __init__(self, simbolos):
        simbolos = list(simbolos)
        if not simbolos:
            raise ValueError("O alfabeto não pode ser vazio.")
        if any(len(s) != 1 for s in simbolos):
            raise ValueError("Cada símbolo do alfabeto deve ter exatamente 1 caractere.")
        self.simbolos = tuple(dict.fromkeys(simbolos))  # remove repetidos, mantém ordem

    def __repr__(self):
        return "Σ = {" + ", ".join(self.simbolos) + "}"

    # ---- validação -------------------------------------------------
    def simbolo_invalido(self, cadeia: str):
        """Primeiro símbolo de `cadeia` que não pertence a Σ (ou None)."""
        for c in cadeia:
            if c not in self.simbolos:
                return c
        return None

    def valida(self, cadeia: str) -> bool:
        """Verifica se a cadeia pertence a Σ*  (todos os símbolos estão em Σ)."""
        return self.simbolo_invalido(cadeia) is None

    # ---- Σ^k, Σ*, Σ+ (enumeração limitada, pois Σ* é infinito) -------
    def potencia(self, k: int) -> list[str]:
        """Σ^k: todas as cadeias de comprimento exatamente k."""
        return ["".join(t) for t in product(self.simbolos, repeat=k)]

    def estrela(self, ate: int) -> list[str]:
        """Σ* restrito a cadeias de comprimento 0..ate."""
        return [w for k in range(0, ate + 1) for w in self.potencia(k)]

    def mais(self, ate: int) -> list[str]:
        """Σ+ = Σ* − {λ}, restrito a cadeias de comprimento 1..ate."""
        return [w for k in range(1, ate + 1) for w in self.potencia(k)]


def tamanho(cadeia: str) -> int:
    """|w|"""
    return len(cadeia)


def concatenacao(u: str, v: str) -> str:
    """u · v"""
    return u + v


class Linguagem:
    """Linguagem L ⊆ Σ*, definida por conjunto finito ou por expressão regular."""

    def __init__(self, alfabeto: Alfabeto, cadeias=None, regex: str | None = None, nome="L"):
        if (cadeias is None) == (regex is None):
            raise ValueError("Informe OU um conjunto de cadeias OU uma expressão regular.")
        self.alfabeto = alfabeto
        self.nome = nome
        self.regex = re.compile(regex) if regex is not None else None
        self.descricao_regex = regex
        self.cadeias = None
        if cadeias is not None:
            self.cadeias = {normaliza(c) for c in cadeias}
            for c in self.cadeias:
                if not alfabeto.valida(c):
                    raise ValueError(f"A cadeia '{c}' usa símbolo fora de Σ.")

    def pertence(self, w: str) -> bool:
        if not self.alfabeto.valida(w):
            return False
        if self.cadeias is not None:
            return w in self.cadeias
        return self.regex.fullmatch(w) is not None

    def enumera(self, ate: int) -> list[str]:
        """Cadeias de L com comprimento ≤ ate (ordem por tamanho, depois lexicográfica)."""
        if self.cadeias is not None:
            return sorted((w for w in self.cadeias if len(w) <= ate), key=lambda w: (len(w), w))
        return [w for w in self.alfabeto.estrela(ate) if self.regex.fullmatch(w)]

    def concatenar(self, outra: "Linguagem", ate: int) -> list[str]:
        """L1·L2 = {uv | u∈L1, v∈L2}, limitado a |uv| ≤ ate."""
        res = {u + v for u in self.enumera(ate) for v in outra.enumera(ate) if len(u + v) <= ate}
        return sorted(res, key=lambda w: (len(w), w))
