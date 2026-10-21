import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes import ProgramNode
from parser import parse
from semantic import SemanticResult, analyze, builtin_class_table


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

    def test_tabela_contem_classes_nativas(self):
        table = builtin_class_table()

        self.assertEqual(set(table), {"Object", "IO", "Int", "Bool", "String"})
        self.assertIsNone(table["Object"].parent)
        self.assertEqual(table["String"].parent, "Object")

    def test_tabela_contem_assinaturas_dos_metodos_nativos(self):
        result = analyze(parse("class Main { };"))

        self.assertEqual(
            result.class_table["IO"].methods["out_int"].parameter_types,
            ("Int",),
        )
        self.assertEqual(
            result.class_table["String"].methods["length"].return_type,
            "Int",
        )


if __name__ == "__main__":
    unittest.main()
