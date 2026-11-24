#!/usr/bin/env python3
"""Simulador de Linguagens Formais e Modelos Computacionais – interface de console.

Uso:
    python main.py          # menu interativo
    python main.py --demo   # roda uma demonstração automática de todos os módulos
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from simulador import complexidade
from simulador.automato_finito import Automato
from simulador.automato_pilha import AutomatoPilha
from simulador.glc import GLC, desenha_arvore
from simulador.linguagens import LAMBDA, Alfabeto, Linguagem, concatenacao, mostra, normaliza, tamanho
from simulador.maquina_turing import tm_soma_unaria, tm_w_hash_w

EXEMPLOS = Path(__file__).resolve().parent / "exemplos"


# ======================================================================
# Utilidades de E/S
# ======================================================================
def titulo(txt: str):
    print("\n" + "=" * 64 + f"\n  {txt}\n" + "=" * 64)


def ler(prompt: str, padrao: str | None = None) -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    try:
        r = input(f"{prompt}{sufixo}: ")
    except EOFError:  # Ctrl+D / fim da entrada: encerra com elegância
        print("\nAté logo!")
        sys.exit(0)
    return r if r.strip() or padrao is None else padrao


def ler_cadeia(prompt="Cadeia de entrada (λ = vazia)") -> str:
    return normaliza(ler(prompt, ""))


def escolher(opcoes: list[str]) -> str:
    for linha in opcoes:
        print("  " + linha)
    return ler("Opção").strip()


def carregar(classe, padrao: str):
    """Pede um caminho de JSON (Enter = exemplo padrão). Retorna None se der erro."""
    caminho = ler("Arquivo JSON", str(EXEMPLOS / padrao))
    try:
        return classe.de_json(caminho)
    except FileNotFoundError:
        print(f"  ✗ Arquivo não encontrado: {caminho}")
    except (ValueError, KeyError) as e:
        print(f"  ✗ JSON inválido: {e}")
    return None


# ======================================================================
# Módulo 1 – Linguagens Formais
# ======================================================================
def mostra_lista(itens: list[str], limite=60):
    exibe = [mostra(x) for x in itens[:limite]]
    print("  {" + ", ".join(exibe) + (", ..." if len(itens) > limite else "") + "}")
    print(f"  ({len(itens)} cadeias)")


def modulo_linguagens(alfabeto_txt: str | None = None):
    titulo("MÓDULO 1 – LINGUAGENS FORMAIS")
    try:
        simbolos = [s.strip() for s in (alfabeto_txt or ler("Alfabeto Σ (símbolos separados por vírgula)", "a,b")).split(",")]
        sigma = Alfabeto(simbolos)
    except ValueError as e:
        print(f"  ✗ {e}")
        return
    print("  " + repr(sigma))
    L = None
    while True:
        op = escolher(["1) Validar cadeia   2) Σ* (até k)   3) Σ+ (até k)   4) Tamanho",
                       "5) Concatenação    6) Definir linguagem L e testar   0) Voltar"])
        if op == "0":
            return
        if op == "1":
            w = ler_cadeia()
            bad = sigma.simbolo_invalido(w)
            print("  Cadeia válida para Σ" if bad is None else f"  Cadeia INVÁLIDA: '{bad}' não pertence a Σ")
            if bad is None:
                print(f"  Tamanho = {tamanho(w)}")
        elif op in ("2", "3"):
            try:
                k = max(0, min(int(ler("Comprimento máximo k", "3")), 8))
            except ValueError:
                print("  ✗ k deve ser um inteiro.")
                continue
            lista = sigma.estrela(k) if op == "2" else sigma.mais(k)
            print(f"  {'Σ*' if op == '2' else 'Σ+'} (|w| ≤ {k}):")
            mostra_lista(lista)
        elif op == "4":
            w = ler_cadeia()
            print(f"  |{mostra(w)}| = {tamanho(w)}")
        elif op == "5":
            u, v = ler_cadeia("u"), ler_cadeia("v")
            print(f"  u·v = {mostra(concatenacao(u, v))}   (|u·v| = {tamanho(u) + tamanho(v)})")
        elif op == "6":
            modo = ler("Definir por (1) conjunto finito ou (2) expressão regular", "1")
            try:
                if modo == "2":
                    L = Linguagem(sigma, regex=ler("Regex (sintaxe Python, ex.: (ab)*)", "(ab)*"))
                else:
                    L = Linguagem(sigma, cadeias=ler("Cadeias separadas por vírgula", "a,ab,abb").split(","))
            except (ValueError, re.error) as e:
                print(f"  ✗ {e}")
                continue
            print("  Primeiras cadeias de L (|w| ≤ 4):")
            mostra_lista(L.enumera(4))
            w = ler_cadeia("Testar pertinência de w")
            print(f"  {mostra(w)} {'∈' if L.pertence(w) else '∉'} L")


# ======================================================================
# Módulo 2 – Autômato Finito
# ======================================================================
def mostra_af(aut: Automato, w: str):
    r = aut.executar(w)
    print(f"\n  Entrada: {mostra(w)}   ({aut.tipo})")
    if aut.tipo == "AFN":
        print("  Conjuntos de estados ativos (com fecho-λ):")
        for i, (c, conj) in enumerate(aut.traco_conjuntos(w) if r.motivo[:7] != "símbolo" else []):
            lido = "início" if c is None else f"lê '{c}'"
            print(f"    passo {i}: {lido:<8} → {{{', '.join(sorted(conj)) or '∅'}}}")
        print("  Caminho de aceitação:" if r.aceita else "  Nenhum caminho de aceitação.")
    else:
        print("  Passo a passo:")
    for i, (de, s, para) in enumerate(r.transicoes, 1):
        print(f"    {i}. {de} --{s or LAMBDA}--> {para}")
    if r.transicoes or r.aceita:
        print("  " + " -> ".join(r.caminho))
    print(f"  {'ACEITA' if r.aceita else 'REJEITA'}" + ("" if r.aceita else f"  ({r.motivo})"))


def modulo_af():
    titulo("MÓDULO 2 – AUTÔMATO FINITO (AFD / AFN)")
    aut = carregar(Automato, "afd_exemplo.json")
    if aut is None:
        return
    print(f"  {aut.tipo}: Q={aut.estados}  Σ={aut.alfabeto}  q0={aut.inicial}  F={sorted(aut.finais)}")
    for (q, s), ds in sorted(aut.delta.items()):
        print(f"    δ({q}, {s or LAMBDA}) = {sorted(ds)}")
    while True:
        op = escolher(["1) Executar cadeia   2) Converter AFN → AFD   0) Voltar"])
        if op == "0":
            return
        if op == "1":
            mostra_af(aut, ler_cadeia())
        elif op == "2":
            d = aut.para_afd()
            print(f"  AFD equivalente: {len(d.estados)} estados, inicial {d.inicial}, finais {sorted(d.finais)}")
            for (q, s), ds in sorted(d.delta.items()):
                print(f"    δ({q}, {s}) = {sorted(ds)[0]}")


# ======================================================================
# Módulo 3 – GLC
# ======================================================================
def mostra_glc(g: GLC, w: str):
    r = g.derivar(w)
    print(f"\n  Entrada: {mostra(w)}")
    if r.aceita:
        print("  Derivação (mais à esquerda), passo a passo:")
        for i, forma in enumerate(r.formas):
            if i == 0:
                print(f"    {mostra(forma)}")
            else:
                var, rhs = r.passos[i - 1]
                print(f"    ⇒ {mostra(forma):<14} (usa {var} -> {mostra(rhs)})")
        print("\n  Árvore de derivação:")
        for linha in desenha_arvore(r.arvore):
            print("    " + linha)
    print("  ACEITA" if r.aceita else "  REJEITA" + (" (limite de busca atingido)" if r.limite_atingido else ""))
    print(f"  (formas sentenciais exploradas: {r.explorados})")


def modulo_glc():
    titulo("MÓDULO 3 – GRAMÁTICA LIVRE DE CONTEXTO")
    g = carregar(GLC, "glc_anbn.json")
    if g is None:
        return
    print(f"  Variáveis={sorted(g.variaveis)}  Terminais={sorted(g.terminais)}  Inicial={g.inicial}")
    print("  Produções:\n" + "\n".join("    " + l for l in str(g).splitlines()))
    while True:
        w = ler("Cadeia (λ = vazia; 'sair' para voltar)").strip()
        if w == "sair":
            return
        mostra_glc(g, normaliza(w))


# ======================================================================
# Módulo 4 – Autômato com Pilha
# ======================================================================
def mostra_ap(ap: AutomatoPilha, w: str):
    r = ap.executar(w)
    print(f"\n  Entrada: {mostra(w)}   (pilha: topo à esquerda, fundo = {ap.simbolo_pilha})")
    if r.passos:
        print(f"  {'Passo':<6}{'Leitura':<10}{'Restante':<10}{'Estado':<8}{'Pilha':<12}Operação")
        for i, (leit, rest, est, pil, op) in enumerate(r.passos):
            print(f"  {i:<6}{leit:<10}{rest:<10}{est:<8}{pil:<12}{op}")
    print("  ACEITA" if r.aceita else f"  REJEITA ({r.motivo})")


def modulo_ap():
    titulo("MÓDULO 4 – AUTÔMATO COM PILHA  (L = { aⁿbⁿ | n ≥ 1 })")
    ap = carregar(AutomatoPilha, "ap_anbn.json")
    if ap is None:
        return
    while True:
        w = ler("Cadeia (λ = vazia; 'sair' para voltar)").strip()
        if w == "sair":
            return
        mostra_ap(ap, normaliza(w))


# ======================================================================
# Módulo 5 – Máquina de Turing
# ======================================================================
def mostra_mt(mt, entrada: str, completo: bool | None = None):
    r = mt.executar(entrada)
    print(f"\n  Máquina: {mt.nome}   Entrada: {mostra(entrada)}")
    if completo is None:
        completo = r.passos <= 40 or ler(f"  {r.passos} passos. Mostrar todos? (s/n)", "n").lower() == "s"
    passos_exibidos = list(enumerate(r.historico)) if completo else [(0, r.historico[0]), (len(r.historico) - 1, r.historico[-1])]
    for i, (q, fita, cab) in passos_exibidos:
        prefixo = f"  passo {i:>3} | estado {q:<8} | "
        print(prefixo + fita)
        print(" " * (len(prefixo) + cab) + "^")
    print(f"  {'ACEITA' if r.aceita else 'REJEITA'} em {r.passos} passos ({r.motivo})")
    if r.aceita and mt.nome == "soma unária":
        print(f"  Resultado na fita: {r.fita_final or LAMBDA}  (= {len(r.fita_final)})")


def modulo_mt():
    titulo("MÓDULO 5 – MÁQUINA DE TURING")
    op = escolher(["A) Reconhecer L = { w#w | w ∈ {a,b}* }", "B) Soma unária (ex.: 000100 = 3 + 2)", "0) Voltar"]).upper()
    if op not in ("A", "B"):
        return
    mt, dica = (tm_w_hash_w(), "ab#ab") if op == "A" else (tm_soma_unaria(), "000100")
    while True:
        w = ler("Entrada ('sair' para voltar)", dica)
        if w == "sair":
            return
        mostra_mt(mt, normaliza(w))


# ======================================================================
# Módulo 6 – Complexidade
# ======================================================================
def modulo_complexidade():
    titulo("MÓDULO 6 – COMPLEXIDADE COMPUTACIONAL")
    print(complexidade.tabela_texto())
    print("\n  Medição empírica (nº de passos × tamanho da entrada):")
    print(f"  {'n':>4} | {'AFD':>5} | {'AP':>5} | {'GLC*':>5} | {'MT w#w':>7} | {'passos/N²':>9} | {'MT soma':>7}")
    for n, afd, ap, glc, mt1, razao, mt2 in complexidade.benchmark():
        print(f"  {n:>4} | {afd:>5} | {ap:>5} | {glc:>5} | {mt1:>7} | {razao:>9.3f} | {mt2:>7}")
    print("  * GLC = formas sentenciais exploradas. Entradas: aⁿbⁿ (AP/GLC), (ab)^(n/2)#(ab)^(n/2) (MT w#w),")
    print("    0ⁿ10ⁿ (soma); N = tamanho total da entrada. A razão passos/N² estabiliza (≈ 0,5) ⇒ Θ(N²).")


# ======================================================================
# Demonstração automática (--demo)
# ======================================================================
def demo():
    modulo_linguagens_demo()
    titulo("MÓDULO 2 – AUTÔMATO FINITO")
    mostra_af(Automato.de_json(EXEMPLOS / "afd_exemplo.json"), "ab")
    mostra_af(Automato.de_json(EXEMPLOS / "afd_exemplo.json"), "aa")
    mostra_af(Automato.de_json(EXEMPLOS / "afn_exemplo.json"), "baab")
    mostra_af(Automato.de_json(EXEMPLOS / "afn_lambda.json"), "aaa")
    titulo("MÓDULO 3 – GRAMÁTICA LIVRE DE CONTEXTO")
    g = GLC.de_json(EXEMPLOS / "glc_anbn.json")
    mostra_glc(g, "aaabbb")
    mostra_glc(g, "aab")
    titulo("MÓDULO 4 – AUTÔMATO COM PILHA")
    ap = AutomatoPilha.de_json(EXEMPLOS / "ap_anbn.json")
    mostra_ap(ap, "aabb")
    mostra_ap(ap, "aab")
    titulo("MÓDULO 5 – MÁQUINA DE TURING")
    mostra_mt(tm_w_hash_w(), "ab#ab", True)
    mostra_mt(tm_w_hash_w(), "ab#ba", True)
    mostra_mt(tm_soma_unaria(), "000100", True)
    modulo_complexidade()


def modulo_linguagens_demo():
    titulo("MÓDULO 1 – LINGUAGENS FORMAIS")
    sigma = Alfabeto(["a", "b"])
    print("  " + repr(sigma))
    w = "abba"
    print(f"  Entrada: {w}\n  " + ("Cadeia válida para Σ" if sigma.valida(w) else "Cadeia inválida") + f"\n  Tamanho = {tamanho(w)}")
    print("  Σ* (|w| ≤ 2):", sigma.estrela(2) and [mostra(x) for x in sigma.estrela(2)])
    print("  Σ+ (|w| ≤ 2):", sigma.mais(2))
    print(f"  'ab' · 'ba' = {concatenacao('ab', 'ba')}")
    L = Linguagem(sigma, regex="(ab)*")
    print(f"  L = (ab)*  →  abab ∈ L? {L.pertence('abab')};  aba ∈ L? {L.pertence('aba')}")


# ======================================================================
def main():
    if "--demo" in sys.argv:
        demo()
        return
    acoes = {"1": modulo_linguagens, "2": modulo_af, "3": modulo_glc, "4": modulo_ap,
             "5": modulo_mt, "6": modulo_complexidade}
    while True:
        titulo("SIMULADOR DE LINGUAGENS FORMAIS E MODELOS COMPUTACIONAIS")
        op = escolher(["1) Linguagens Formais", "2) Autômato Finito (AFD/AFN)",
                       "3) Gramática Livre de Contexto", "4) Autômato com Pilha",
                       "5) Máquina de Turing", "6) Complexidade Computacional", "0) Sair"])
        if op == "0":
            print("Até logo!")
            return
        acoes.get(op, lambda: print("  Opção inválida."))()


if __name__ == "__main__":
    main()
