import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes import ProgramNode
from parser import parse
from semantic import SemanticResult, analyze


class TestSemanticBase(unittest.TestCase):
    def test_analisa_programa_sintaticamente_valido(self):
        program = parse("class Main { main() : Object { self }; };")

        result = analyze(program)

        self.assertIsInstance(result, SemanticResult)
        self.assertTrue(result.success)
        self.assertEqual(result.errors, [])

    def test_rejeita_objeto_que_nao_e_ast_de_programa(self):
        with self.assertRaisesRegex(TypeError, "ProgramNode"):
            analyze(ProgramNode)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
