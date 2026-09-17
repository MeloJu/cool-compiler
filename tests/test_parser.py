import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser import parse, ProgramNode, ClassNode


class TestParserInicial(unittest.TestCase):
    def test_classe_vazia(self):
        ast = parse("class Main {\n};")
        self.assertEqual(ast, ProgramNode(classes=[ClassNode(name="Main")]))

    def test_rejeita_ponto_virgula_faltando(self):
        with self.assertRaises(SyntaxError):
            parse("class Main {\n}")

    def test_rejeita_erro_lexico(self):
        with self.assertRaises(SyntaxError):
            parse("class Main { $ };")


if __name__ == "__main__":
    unittest.main()
