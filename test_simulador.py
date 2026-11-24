"""Testes automatizados. Execute com:  python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulador.automato_finito import Automato
from simulador.automato_pilha import AutomatoPilha
from simulador.glc import GLC
from simulador.linguagens import Alfabeto, Linguagem, concatenacao, normaliza, tamanho
from simulador.maquina_turing import tm_soma_unaria, tm_w_hash_w

EX = Path(__file__).resolve().parent.parent / "exemplos"


class TestLinguagens(unittest.TestCase):
    def setUp(self):
        self.sigma = Alfabeto(["a", "b"])

    def test_validacao_e_tamanho(self):
        self.assertTrue(self.sigma.valida("abba"))
        self.assertFalse(self.sigma.valida("abca"))
        self.assertEqual(tamanho("abba"), 4)

    def test_estrela_e_mais(self):
        self.assertEqual(self.sigma.estrela(2), ["", "a", "b", "aa", "ab", "ba", "bb"])
        self.assertEqual(self.sigma.mais(1), ["a", "b"])
        self.assertEqual(len(self.sigma.estrela(4)), 2 ** 5 - 1)

    def test_concatenacao_e_lambda(self):
        self.assertEqual(concatenacao("ab", "ba"), "abba")
        self.assertEqual(concatenacao("ab", normaliza("λ")), "ab")

    def test_linguagem(self):
        L = Linguagem(self.sigma, regex="(ab)*")
        self.assertTrue(L.pertence("abab"))
        self.assertTrue(L.pertence(""))
        self.assertFalse(L.pertence("aba"))
        F = Linguagem(self.sigma, cadeias=["a", "ab"])
        self.assertEqual(F.enumera(5), ["a", "ab"])
        self.assertIn("aab", F.concatenar(F, 4))

    def test_alfabeto_invalido(self):
        with self.assertRaises(ValueError):
            Alfabeto([])
        with self.assertRaises(ValueError):
            Alfabeto(["ab"])


class TestAutomatoFinito(unittest.TestCase):
    def test_afd_exemplo_do_enunciado(self):
        afd = Automato.de_json(EX / "afd_exemplo.json")
        r = afd.executar("ab")
        self.assertTrue(r.aceita)
        self.assertEqual(r.caminho, ["q0", "q1", "q2"])
        self.assertFalse(afd.executar("a").aceita)
        self.assertFalse(afd.executar("abb").aceita)
        self.assertFalse(afd.executar("c").aceita)

    def test_afd_rejeita_nao_determinismo(self):
        with self.assertRaises(ValueError):
            Automato(["p", "q"], ["a"], "p", ["q"], [("p", "a", "p"), ("p", "a", "q")], "AFD")

    def test_afn_contem_ab(self):
        afn = Automato.de_json(EX / "afn_exemplo.json")
        for w in ["ab", "baab", "bbbabb"]:
            self.assertTrue(afn.executar(w).aceita, w)
        for w in ["", "a", "bba", "bbb"]:
            self.assertFalse(afn.executar(w).aceita, w)

    def test_afn_lambda(self):
        afn = Automato.de_json(EX / "afn_lambda.json")
        for n in range(0, 20):
            esperado = n % 2 == 0 or n % 3 == 0
            self.assertEqual(afn.executar("a" * n).aceita, esperado, n)

    def test_equivalencia_afn_afd(self):
        for arq in ("afn_exemplo.json", "afn_lambda.json"):
            afn = Automato.de_json(EX / arq)
            afd = afn.para_afd()
            self.assertEqual(afd.tipo, "AFD")
            alfa = Alfabeto(afn.alfabeto)
            for w in alfa.estrela(7):
                self.assertEqual(afn.executar(w).aceita, afd.executar(w).aceita, (arq, w))


class TestGLC(unittest.TestCase):
    def test_anbn(self):
        g = GLC.de_json(EX / "glc_anbn.json")
        for n in range(0, 8):
            self.assertTrue(g.derivar("a" * n + "b" * n).aceita)
        for w in ["aab", "abb", "ba", "aabbb", "abab"]:
            self.assertFalse(g.derivar(w).aceita, w)

    def test_derivacao_e_arvore(self):
        r = GLC.de_json(EX / "glc_anbn.json").derivar("aaabbb")
        self.assertEqual(r.formas, ["S", "aSb", "aaSbb", "aaaSbbb", "aaabbb"])
        self.assertEqual(r.arvore.rotulo, "S")

    def test_parenteses(self):
        g = GLC.de_json(EX / "glc_parenteses.json")
        for w in ["", "()", "(())()", "()()()"]:
            self.assertTrue(g.derivar(w).aceita, w)
        for w in ["(", ")(", "(()", "())"]:
            self.assertFalse(g.derivar(w).aceita, w)

    def test_recursao_a_esquerda_termina(self):
        g = GLC(["S"], ["a"], {"S": ["Sa", "a"]}, "S")
        self.assertTrue(g.derivar("aaaa").aceita)
        self.assertFalse(g.derivar("").aceita)


class TestAP(unittest.TestCase):
    def test_anbn(self):
        ap = AutomatoPilha.de_json(EX / "ap_anbn.json")
        for n in range(1, 8):
            self.assertTrue(ap.executar("a" * n + "b" * n).aceita)
        for w in ["", "a", "b", "aab", "abb", "ba", "abab", "aabbb"]:
            self.assertFalse(ap.executar(w).aceita, w)

    def test_passos_mostram_pilha(self):
        passos = AutomatoPilha.de_json(EX / "ap_anbn.json").executar("aabb").passos
        pilhas = [p[3] for p in passos]
        self.assertEqual(pilhas, ["Z", "AZ", "AAZ", "AZ", "Z", "Z"])


class TestTuring(unittest.TestCase):
    def test_w_hash_w(self):
        mt = tm_w_hash_w()
        for w in ["", "a", "b", "ab", "ba", "abba", "aabab"]:
            self.assertTrue(mt.executar(w + "#" + w).aceita, w)
        for s in ["a#b", "ab#ba", "ab#a", "a#ab", "ab", "##", "aa#aa#", "#a", "a#"]:
            self.assertFalse(mt.executar(s).aceita, s)

    def test_soma_unaria(self):
        mt = tm_soma_unaria()
        for n in range(0, 6):
            for m in range(0, 6):
                r = mt.executar("0" * n + "1" + "0" * m)
                self.assertTrue(r.aceita)
                self.assertEqual(r.fita_final, "0" * (n + m))
        self.assertEqual(mt.executar("000100").fita_final, "00000")
        self.assertFalse(mt.executar("0011").aceita)
        self.assertFalse(mt.executar("000").aceita)

    def test_complexidade_quadratica(self):
        mt = tm_w_hash_w()
        passos = [mt.executar("a" * n + "#" + "a" * n).passos for n in (10, 20, 40)]
        self.assertAlmostEqual(passos[1] / passos[0], 4, delta=0.5)
        self.assertAlmostEqual(passos[2] / passos[1], 4, delta=0.5)


if __name__ == "__main__":
    unittest.main()
