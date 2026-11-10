import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes import ProgramNode
from codegen import BrilGenerator, generate_bril
from parser import parse


class TestCodegenBase(unittest.TestCase):
    def test_gera_programa_bril_com_funcao_main(self):
        program = parse("class Main { main() : Object { self }; };")

        bril = generate_bril(program)

        self.assertEqual(bril, {"functions": [{"name": "main", "instrs": []}]})

    def test_gera_nomes_temporarios_unicos(self):
        generator = BrilGenerator()

        self.assertEqual(generator.new_temporary(), "tmp0")
        self.assertEqual(generator.new_temporary(), "tmp1")

    def test_gera_labels_unicos(self):
        generator = BrilGenerator()

        self.assertEqual(generator.new_label("if_then"), "if_then_0")
        self.assertEqual(generator.new_label("if_else"), "if_else_1")

    def test_rejeita_objeto_que_nao_e_ast_de_programa(self):
        with self.assertRaisesRegex(TypeError, "ProgramNode"):
            generate_bril(ProgramNode)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
